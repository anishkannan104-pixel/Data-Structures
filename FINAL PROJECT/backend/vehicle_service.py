import time
from datetime import datetime
from backend.database import get_db_connection
from backend.shipment_service import shipment_service

class VehicleService:
    def get_all_vehicles(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM vehicles ORDER BY id ASC;").fetchall()
        conn.close()

        vehicles = []
        for r in rows:
            v = dict(r)
            rem_wt = max(0.0, v["max_weight"] - v["current_weight"])
            rem_vol = max(0.0, v["max_volume"] - v["current_volume"])
            wt_util = round((v["current_weight"] / v["max_weight"]) * 100.0, 1) if v["max_weight"] > 0 else 0.0
            vol_util = round((v["current_volume"] / v["max_volume"]) * 100.0, 1) if v["max_volume"] > 0 else 0.0
            overall_util = max(wt_util, vol_util)

            v["remaining_weight"] = round(rem_wt, 2)
            v["remaining_volume"] = round(rem_vol, 2)
            v["weight_utilization_pct"] = wt_util
            v["volume_utilization_pct"] = vol_util
            v["overall_utilization_pct"] = overall_util
            vehicles.append(v)
        return vehicles

    def get_vehicle_by_id(self, vehicle_id):
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM vehicles WHERE id = ?;", (vehicle_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def add_vehicle(self, vehicle_code, vehicle_type, max_weight, max_volume):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO vehicles (vehicle_code, vehicle_type, max_weight, max_volume, current_weight, current_volume, is_available)
            VALUES (?, ?, ?, ?, 0.0, 0.0, 1);
            """, (vehicle_code, vehicle_type, max_weight, max_volume))
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        finally:
            conn.close()

    def find_suitable_vehicle(self, shipment_weight, shipment_volume):
        """Finds best available vehicle satisfying both weight and volume constraints."""
        vehicles = self.get_all_vehicles()
        suitable = []
        for v in vehicles:
            if v["is_available"] == 1:
                if v["remaining_weight"] >= shipment_weight and v["remaining_volume"] >= shipment_volume:
                    # Score by remaining slack (Best-fit minimizes unused capacity)
                    slack = (v["remaining_weight"] - shipment_weight) + (v["remaining_volume"] - shipment_volume) * 50
                    suitable.append((slack, v))

        if not suitable:
            return None
        suitable.sort(key=lambda x: x[0])
        return suitable[0][1]

    def assign_shipment_to_vehicle(self, vehicle_id, shipment_id):
        """Strict capacity validation: prevents overloading of either weight or volume."""
        v = self.get_vehicle_by_id(vehicle_id)
        if not v:
            return {"success": False, "message": f"Vehicle ID {vehicle_id} not found."}

        s = shipment_service.get_shipment_by_id(shipment_id)
        if not s:
            return {"success": False, "message": f"Shipment ID {shipment_id} not found."}

        if s["status"] not in (0, 1): # Created or Pending
            return {
                "success": False,
                "message": f"Shipment '{s['shipment_code']}' is in state '{s['status']}' and cannot be assigned."
            }

        new_weight = v["current_weight"] + s["weight"]
        new_volume = v["current_volume"] + s["volume"]

        # Capacity constraints validation
        if new_weight > v["max_weight"]:
            excess_wt = round(new_weight - v["max_weight"], 2)
            return {
                "success": False,
                "message": f"Overload Rejected! Exceeds maximum weight by {excess_wt} kg (Limit: {v['max_weight']} kg, Needed: {round(new_weight, 2)} kg)."
            }

        if new_volume > v["max_volume"]:
            excess_vol = round(new_volume - v["max_volume"], 2)
            return {
                "success": False,
                "message": f"Overload Rejected! Exceeds maximum volume by {excess_vol} m³ (Limit: {v['max_volume']} m³, Needed: {round(new_volume, 2)} m³)."
            }

        # Transition shipment to 'Assigned' (2) via C FSM
        fsm_res = shipment_service.validate_and_update_status(shipment_id, 2, f"Assigned to {v['vehicle_code']}")
        if not fsm_res["valid"]:
            return {"success": False, "message": f"FSM Transition Error: {fsm_res['message']}"}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO vehicle_assignments (vehicle_id, shipment_id, assigned_at, status)
            VALUES (?, ?, ?, 'ACTIVE');
            """, (vehicle_id, shipment_id, now_str))

            cursor.execute("""
            UPDATE vehicles
            SET current_weight = ?,
                current_volume = ?
            WHERE id = ?;
            """, (new_weight, new_volume, vehicle_id))

            conn.commit()
        finally:
            conn.close()

        rem_wt = round(v["max_weight"] - new_weight, 2)
        rem_vol = round(v["max_volume"] - new_volume, 2)
        wt_util = round((new_weight / v["max_weight"]) * 100.0, 1)

        return {
            "success": True,
            "message": f"Shipment {s['shipment_code']} successfully assigned to {v['vehicle_code']}.",
            "vehicle_code": v["vehicle_code"],
            "remaining_weight": rem_wt,
            "remaining_volume": rem_vol,
            "weight_utilization_pct": wt_util
        }

    def get_vehicle_summary_metrics(self):
        vehicles = self.get_all_vehicles()
        total = len(vehicles)
        available = sum(1 for v in vehicles if v["is_available"] == 1 and v["overall_utilization_pct"] < 95.0)
        assigned = sum(1 for v in vehicles if v["current_weight"] > 0)
        avg_util = round(sum(v["overall_utilization_pct"] for v in vehicles) / total, 1) if total > 0 else 0.0

        return {
            "total_vehicles": total,
            "available_vehicles": available,
            "assigned_vehicles": assigned,
            "avg_utilization": avg_util
        }

vehicle_service = VehicleService()
