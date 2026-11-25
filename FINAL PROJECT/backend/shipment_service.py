import ctypes
import time
from datetime import datetime
from backend.database import get_db_connection
from backend.c_bridge import c_bridge, CShipment

STATUS_MAP = {
    0: "Created",
    1: "Pending",
    2: "Assigned",
    3: "In Transit",
    4: "Delivered",
    5: "Cancelled"
}

STATUS_REVERSE_MAP = {v: k for k, v in STATUS_MAP.items()}

PRIORITY_MAP = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Urgent",
    5: "Critical"
}

class ShipmentService:
    def __init__(self):
        self.c = c_bridge
        self.sync_c_structures()

    def sync_c_structures(self):
        """Loads all active shipments from SQLite into C structures."""
        self.c.lib.ll_init()
        self.c.lib.queue_init()
        self.c.lib.pq_init()
        self.c.lib.minheap_init()
        self.c.lib.hash_init()

        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM shipments ORDER BY id ASC;").fetchall()
        conn.close()

        for r in rows:
            cs = CShipment()
            cs.id = r["id"]
            cs.shipment_code = r["shipment_code"].encode("utf-8")
            cs.weight = float(r["weight"])
            cs.volume = float(r["volume"])
            dest = r["destination"] if r["destination"] else ""
            cs.destination = dest.encode("utf-8")
            cs.deadline_timestamp = int(r["deadline_timestamp"])
            cs.priority = int(r["priority"])
            cs.status = int(r["status"])

            # Insert into C Linked List
            self.c.lib.ll_insert_tail(ctypes.byref(cs))

            # Insert into C Hash Table for duplicate detection
            dup = ctypes.c_int(0)
            self.c.lib.hash_insert(cs.shipment_code, ctypes.byref(cs), ctypes.byref(dup))

            # If Pending, insert into C Queue and Priority Queue
            if cs.status in (0, 1):
                self.c.lib.queue_enqueue(ctypes.byref(cs))
                self.c.lib.pq_insert(ctypes.byref(cs))

            # Insert into C Min-Heap if not yet delivered or cancelled
            if cs.status not in (4, 5):
                self.c.lib.minheap_insert(ctypes.byref(cs))

    def get_all_shipments(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM shipments ORDER BY id DESC;").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_shipment_by_id(self, shipment_id):
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM shipments WHERE id = ?;", (shipment_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def search_by_code_c_hash(self, code):
        """Uses C Hash Table to search for shipment by code."""
        cs = CShipment()
        comp = ctypes.c_longlong(0)
        t_us = ctypes.c_double(0.0)
        found = self.c.lib.hash_search(code.encode("utf-8"), ctypes.byref(cs), ctypes.byref(comp), ctypes.byref(t_us))
        if found:
            return {
                "found": True,
                "shipment": cs.to_dict(),
                "comparisons": comp.value,
                "time_us": t_us.value
            }
        return {"found": False, "comparisons": comp.value, "time_us": t_us.value}

    def create_shipment(self, shipment_code, weight, volume, destination, deadline_ts, priority):
        """Creates a shipment with duplicate check via C Hash Table and insertion into DB."""
        # Check duplicate using C Hash Table
        dup = ctypes.c_int(0)
        temp_s = CShipment()
        temp_s.id = 0
        temp_s.shipment_code = shipment_code.encode("utf-8")
        temp_s.weight = float(weight)
        temp_s.volume = float(volume)
        temp_s.destination = destination.encode("utf-8")
        temp_s.deadline_timestamp = int(deadline_ts)
        temp_s.priority = int(priority)
        temp_s.status = 0 # Created

        self.c.lib.hash_insert(shipment_code.encode("utf-8"), ctypes.byref(temp_s), ctypes.byref(dup))
        if dup.value == 1:
            raise ValueError(f"Duplicate Shipment ID detected: '{shipment_code}' already exists in C Hash Table and database.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO shipments (shipment_code, weight, volume, destination, deadline_timestamp, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?);
            """, (shipment_code, weight, volume, destination, deadline_ts, priority, now_str, now_str))
            new_id = cursor.lastrowid

            temp_s.id = new_id

            # Update C Linked List
            self.c.lib.ll_insert_tail(ctypes.byref(temp_s))

            # Push to C Stack
            self.c.lib.stack_push(
                1, b"CREATE", new_id, int(time.time()),
                f"Created {shipment_code} ({weight}kg, {destination})".encode("utf-8")
            )

            # Record in SQLite Processing History
            cursor.execute("""
            INSERT INTO processing_history (action_type, shipment_id, details, timestamp)
            VALUES (?, ?, ?, ?);
            """, ("CREATE", new_id, f"Shipment {shipment_code} created", int(time.time())))

            # Record in Status History
            cursor.execute("""
            INSERT INTO shipment_status_history (shipment_id, from_status, to_status, changed_at, notes)
            VALUES (?, 0, 0, ?, 'Shipment created in system');
            """, (new_id, now_str))

            conn.commit()
        finally:
            conn.close()

        # Re-sync active queue and min-heap
        self.c.lib.queue_enqueue(ctypes.byref(temp_s))
        self.c.lib.pq_insert(ctypes.byref(temp_s))
        self.c.lib.minheap_insert(ctypes.byref(temp_s))

        return new_id

    def validate_and_update_status(self, shipment_id, target_status, notes=""):
        """Validates state transition using C FSM before committing to database."""
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment with ID {shipment_id} not found.")

        current_status = shipment["status"]

        # Validate with C Finite State Machine
        msg_buf = ctypes.create_string_buffer(512)
        is_valid = self.c.lib.fsm_validate_transition(current_status, target_status, msg_buf, 512)
        message = msg_buf.value.decode("utf-8", errors="ignore")

        if not is_valid:
            return {"success": False, "valid": False, "message": message}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE shipments
            SET status = ?, updated_at = ?
            WHERE id = ?;
            """, (target_status, now_str, shipment_id))

            cursor.execute("""
            INSERT INTO shipment_status_history (shipment_id, from_status, to_status, changed_at, notes)
            VALUES (?, ?, ?, ?, ?);
            """, (shipment_id, current_status, target_status, now_str, notes if notes else message))

            cursor.execute("""
            INSERT INTO processing_history (action_type, shipment_id, details, timestamp)
            VALUES (?, ?, ?, ?);
            """, (f"STATUS_{STATUS_MAP[target_status].upper()}", shipment_id, message, int(time.time())))

            conn.commit()
        finally:
            conn.close()

        # Update C Linked List
        self.c.lib.ll_update(shipment_id, shipment["weight"], shipment["volume"], shipment["priority"], target_status)

        # Push action to C Stack
        self.c.lib.stack_push(
            2, b"STATUS_UPDATE", shipment_id, int(time.time()),
            f"{shipment['shipment_code']} -> {STATUS_MAP[target_status]}".encode("utf-8")
        )

        return {"success": True, "valid": True, "message": message}

    def delete_shipment(self, shipment_id):
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return False

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shipments WHERE id = ?;", (shipment_id,))
            cursor.execute("""
            INSERT INTO processing_history (action_type, shipment_id, details, timestamp)
            VALUES (?, ?, ?, ?);
            """, ("DELETE", shipment_id, f"Shipment {shipment['shipment_code']} deleted", int(time.time())))
            conn.commit()
        finally:
            conn.close()

        # Delete from C Linked List
        self.c.lib.ll_delete_by_id(shipment_id)
        self.c.lib.stack_push(3, b"DELETE", shipment_id, int(time.time()), f"Deleted {shipment['shipment_code']}".encode("utf-8"))
        self.sync_c_structures()
        return True

    def get_upcoming_deadlines_c_minheap(self, hours_threshold=48):
        """Identifies upcoming deadlines using C Min-Heap."""
        now_ts = int(time.time())
        threshold_ts = now_ts + (hours_threshold * 3600)

        out_arr = (CShipment * 128)()
        out_cnt = ctypes.c_int(0)
        self.c.lib.minheap_get_imminent(threshold_ts, out_arr, 128, ctypes.byref(out_cnt))

        results = []
        for i in range(out_cnt.value):
            s = out_arr[i]
            secs_left = s.deadline_timestamp - now_ts
            hours_left = round(secs_left / 3600.0, 1)
            results.append({
                "id": s.id,
                "shipment_code": s.shipment_code.decode("utf-8", errors="ignore"),
                "destination": s.destination.decode("utf-8", errors="ignore"),
                "priority": PRIORITY_MAP.get(s.priority, "Unknown"),
                "deadline_ts": s.deadline_timestamp,
                "hours_left": hours_left,
                "is_urgent": hours_left <= 12
            })
        results.sort(key=lambda x: x["hours_left"])
        return results

    def get_priority_queue_records(self, max_records=20):
        """Retrieves top scheduled shipments from C Priority Queue."""
        out_arr = (CShipment * max_records)()
        out_cnt = ctypes.c_int(0)
        self.c.lib.pq_get_all(out_arr, max_records, ctypes.byref(out_cnt))

        results = []
        for i in range(out_cnt.value):
            s = out_arr[i]
            results.append({
                "id": s.id,
                "shipment_code": s.shipment_code.decode("utf-8", errors="ignore"),
                "priority_val": s.priority,
                "priority": PRIORITY_MAP.get(s.priority, "Unknown"),
                "destination": s.destination.decode("utf-8", errors="ignore"),
                "weight": round(s.weight, 2),
                "volume": round(s.volume, 2)
            })
        return results

    def get_queue_records(self, max_records=20):
        """Retrieves incoming arrival order from C Queue (FIFO)."""
        out_arr = (CShipment * max_records)()
        out_cnt = ctypes.c_int(0)
        self.c.lib.queue_get_all(out_arr, max_records, ctypes.byref(out_cnt))

        results = []
        for i in range(out_cnt.value):
            s = out_arr[i]
            results.append({
                "id": s.id,
                "shipment_code": s.shipment_code.decode("utf-8", errors="ignore"),
                "destination": s.destination.decode("utf-8", errors="ignore"),
                "weight": round(s.weight, 2),
                "priority": PRIORITY_MAP.get(s.priority, "Unknown")
            })
        return results

    def pop_stack_history(self):
        """Pops most recent action from C Stack."""
        action_id = ctypes.c_int(0)
        action_name = ctypes.create_string_buffer(64)
        shipment_id = ctypes.c_int(0)
        ts = ctypes.c_longlong(0)
        details = ctypes.create_string_buffer(128)

        res = self.c.lib.stack_pop(
            ctypes.byref(action_id), action_name, ctypes.byref(shipment_id),
            ctypes.byref(ts), details
        )
        if res == 1:
            return {
                "success": True,
                "action": action_name.value.decode("utf-8", errors="ignore"),
                "shipment_id": shipment_id.value,
                "timestamp": ts.value,
                "details": details.value.decode("utf-8", errors="ignore")
            }
        return {"success": False, "message": "Stack is empty."}

    def sort_shipments_c(self, shipments_list, criterion="id", algorithm="Quick Sort"):
        """Sorts shipment records using actual C sorting algorithm."""
        n = len(shipments_list)
        if n == 0:
            return {"sorted": [], "time_us": 0.0, "comparisons": 0, "operations": 0}

        crit_map = {"id": 0, "weight": 1, "priority": 2, "deadline": 3}
        c_crit = crit_map.get(criterion.lower(), 0)

        c_arr = (CShipment * n)()
        for i, s in enumerate(shipments_list):
            c_arr[i].id = s["id"]
            code_bytes = s["shipment_code"].encode("utf-8") if isinstance(s["shipment_code"], str) else s["shipment_code"]
            c_arr[i].shipment_code = code_bytes
            c_arr[i].weight = float(s["weight"])
            c_arr[i].volume = float(s["volume"])
            dest_bytes = s["destination"].encode("utf-8") if isinstance(s["destination"], str) else s["destination"]
            c_arr[i].destination = dest_bytes
            c_arr[i].deadline_timestamp = int(s["deadline_timestamp"])
            c_arr[i].priority = int(s["priority"])
            c_arr[i].status = int(s["status"])

        perf = self.c.lib.CPerformanceResult() if hasattr(self.c.lib, "CPerformanceResult") else None
        from backend.c_bridge import CPerformanceResult
        perf_res = CPerformanceResult()

        if algorithm == "Quick Sort":
            self.c.lib.run_quick_sort(c_arr, n, c_crit, ctypes.byref(perf_res))
        elif algorithm == "Merge Sort":
            self.c.lib.run_merge_sort(c_arr, n, c_crit, ctypes.byref(perf_res))
        elif algorithm == "Heap Sort":
            self.c.lib.run_heap_sort(c_arr, n, c_crit, ctypes.byref(perf_res))
        else:
            self.c.lib.run_quick_sort(c_arr, n, c_crit, ctypes.byref(perf_res))

        sorted_list = []
        for i in range(n):
            sorted_list.append(c_arr[i].to_dict())

        return {
            "sorted": sorted_list,
            "time_us": round(perf_res.execution_time_us, 2),
            "comparisons": perf_res.comparisons,
            "operations": perf_res.operations
        }

    def get_summary_metrics(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM shipments;").fetchone()[0]
        pending = cursor.execute("SELECT COUNT(*) FROM shipments WHERE status = 1;").fetchone()[0]
        in_transit = cursor.execute("SELECT COUNT(*) FROM shipments WHERE status = 3;").fetchone()[0]
        delivered = cursor.execute("SELECT COUNT(*) FROM shipments WHERE status = 4;").fetchone()[0]
        urgent = cursor.execute("SELECT COUNT(*) FROM shipments WHERE priority >= 4 AND status NOT IN (4, 5);").fetchone()[0]
        conn.close()

        imminent = len(self.get_upcoming_deadlines_c_minheap(hours_threshold=24))

        return {
            "total": total,
            "pending": pending,
            "in_transit": in_transit,
            "delivered": delivered,
            "urgent": urgent,
            "imminent_deadlines": imminent
        }

shipment_service = ShipmentService()
