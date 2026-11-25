import ctypes
from backend.database import get_db_connection
from backend.c_bridge import c_bridge, CRouteResult, CMSTResult, CRoad

class GraphService:
    def __init__(self):
        self.c = c_bridge
        self.sync_graph_from_db()

    def sync_graph_from_db(self):
        """Loads vertices and roads from SQLite into C Graph structure."""
        self.c.lib.graph_init()
        conn = get_db_connection()
        loc_rows = conn.execute("SELECT * FROM locations ORDER BY id ASC;").fetchall()
        road_rows = conn.execute("SELECT * FROM roads;").fetchall()
        conn.close()

        for loc in loc_rows:
            self.c.lib.graph_add_location(
                loc["id"],
                loc["name"].encode("utf-8"),
                loc["code"].encode("utf-8"),
                float(loc["x_coord"]),
                float(loc["y_coord"])
            )

        for road in road_rows:
            self.c.lib.graph_add_road(
                road["source_id"],
                road["dest_id"],
                float(road["distance_km"]),
                road["id"],
                int(road["is_active"])
            )

    def get_locations(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM locations ORDER BY id ASC;").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_roads(self):
        conn = get_db_connection()
        rows = conn.execute("""
        SELECT r.*, l1.name as source_name, l2.name as dest_name
        FROM roads r
        JOIN locations l1 ON r.source_id = l1.id
        JOIN locations l2 ON r.dest_id = l2.id
        ORDER BY r.id ASC;
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_location(self, name, code, x, y, desc=""):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            max_id = cursor.execute("SELECT COALESCE(MAX(id), -1) FROM locations;").fetchone()[0]
            new_id = max_id + 1
            cursor.execute("""
            INSERT INTO locations (id, name, code, x_coord, y_coord, description)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (new_id, name, code, x, y, desc))
            conn.commit()
        finally:
            conn.close()
        self.sync_graph_from_db()
        return new_id

    def add_road(self, source_id, dest_id, distance_km):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO roads (source_id, dest_id, distance_km, is_active)
            VALUES (?, ?, ?, 1);
            """, (source_id, dest_id, distance_km))
            new_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        self.sync_graph_from_db()
        return new_id

    def update_road_distance(self, road_id, new_distance):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE roads SET distance_km = ? WHERE id = ?;", (new_distance, road_id))
            conn.commit()
        finally:
            conn.close()
        # Direct C update
        self.c.lib.graph_update_road_weight(road_id, float(new_distance))
        return True

    def set_road_active(self, road_id, is_active):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE roads SET is_active = ? WHERE id = ?;", (is_active, road_id))
            conn.commit()
        finally:
            conn.close()
        # Direct C update
        self.c.lib.graph_set_road_active(road_id, is_active)
        return True

    def run_bfs(self, start_id=0):
        out_order = (ctypes.c_int * 64)()
        out_levels = (ctypes.c_int * 64)()
        out_count = ctypes.c_int(0)
        time_us = ctypes.c_double(0.0)

        self.c.lib.run_bfs(start_id, out_order, out_levels, 64, ctypes.byref(out_count), ctypes.byref(time_us))

        loc_map = {loc["id"]: loc for loc in self.get_locations()}
        traversal = []
        for i in range(out_count.value):
            node_id = out_order[i]
            level = out_levels[i]
            loc = loc_map.get(node_id, {"name": f"Node {node_id}", "code": f"N{node_id}"})
            traversal.append({
                "step": i + 1,
                "node_id": node_id,
                "level": level,
                "name": loc["name"],
                "code": loc["code"]
            })

        return {
            "traversal": traversal,
            "total_visited": out_count.value,
            "execution_time_us": round(time_us.value, 2)
        }

    def run_dfs(self, start_id=0):
        out_order = (ctypes.c_int * 64)()
        out_count = ctypes.c_int(0)
        time_us = ctypes.c_double(0.0)

        self.c.lib.run_dfs(start_id, out_order, 64, ctypes.byref(out_count), ctypes.byref(time_us))

        loc_map = {loc["id"]: loc for loc in self.get_locations()}
        traversal = []
        for i in range(out_count.value):
            node_id = out_order[i]
            loc = loc_map.get(node_id, {"name": f"Node {node_id}", "code": f"N{node_id}"})
            traversal.append({
                "step": i + 1,
                "node_id": node_id,
                "name": loc["name"],
                "code": loc["code"]
            })

        return {
            "traversal": traversal,
            "total_visited": out_count.value,
            "execution_time_us": round(time_us.value, 2)
        }

    def run_dijkstra(self, source_id, dest_id):
        res = CRouteResult()
        success = self.c.lib.run_dijkstra(source_id, dest_id, ctypes.byref(res))

        loc_map = {loc["id"]: loc for loc in self.get_locations()}
        if not success or res.total_path_len <= 0 or res.total_distance < 0:
            return {
                "success": False,
                "path": [],
                "total_distance": 0.0,
                "execution_time_us": round(res.execution_time_us, 2),
                "comparisons": res.comparisons
            }

        path_nodes = []
        for i in range(res.total_path_len):
            nid = res.path[i]
            loc = loc_map.get(nid, {"name": f"Loc {nid}", "code": f"L{nid}", "x_coord": 0, "y_coord": 0})
            path_nodes.append({
                "id": nid,
                "name": loc["name"],
                "code": loc["code"],
                "x": loc["x_coord"],
                "y": loc["y_coord"]
            })

        return {
            "success": True,
            "path_nodes": path_nodes,
            "path_ids": [res.path[i] for i in range(res.total_path_len)],
            "total_distance": round(res.total_distance, 2),
            "execution_time_us": round(res.execution_time_us, 2),
            "comparisons": res.comparisons
        }

    def run_prim_mst(self, start_id=0):
        res = CMSTResult()
        self.c.lib.run_prim_mst(start_id, ctypes.byref(res))

        loc_map = {loc["id"]: loc for loc in self.get_locations()}
        edges = []
        for i in range(res.edge_count):
            u_id = res.u[i]
            v_id = res.v[i]
            w = round(res.weights[i], 2)
            edges.append({
                "u": u_id,
                "v": v_id,
                "u_name": loc_map.get(u_id, {}).get("name", str(u_id)),
                "v_name": loc_map.get(v_id, {}).get("name", str(v_id)),
                "weight": w
            })

        return {
            "algorithm": "Prim's MST",
            "edge_count": res.edge_count,
            "edges": edges,
            "total_cost": round(res.total_cost, 2),
            "execution_time_us": round(res.execution_time_us, 2),
            "operations": res.operations
        }

    def run_kruskal_mst(self):
        res = CMSTResult()
        self.c.lib.run_kruskal_mst(ctypes.byref(res))

        loc_map = {loc["id"]: loc for loc in self.get_locations()}
        edges = []
        for i in range(res.edge_count):
            u_id = res.u[i]
            v_id = res.v[i]
            w = round(res.weights[i], 2)
            edges.append({
                "u": u_id,
                "v": v_id,
                "u_name": loc_map.get(u_id, {}).get("name", str(u_id)),
                "v_name": loc_map.get(v_id, {}).get("name", str(v_id)),
                "weight": w
            })

        return {
            "algorithm": "Kruskal's MST",
            "edge_count": res.edge_count,
            "edges": edges,
            "total_cost": round(res.total_cost, 2),
            "execution_time_us": round(res.execution_time_us, 2),
            "operations": res.operations
        }

    def dynamic_recalculate_route(self, source_id, dest_id, disrupted_road_id):
        """Calculates initial route, disables road, recalculates route, and quantifies impact."""
        # 1. Baseline Route
        initial = self.run_dijkstra(source_id, dest_id)

        # 2. Disable road
        self.set_road_active(disrupted_road_id, 0)

        # 3. Recalculate Shortest Route
        updated = self.run_dijkstra(source_id, dest_id)

        # Retrieve disrupted road details
        conn = get_db_connection()
        road_info = conn.execute("""
        SELECT r.*, l1.name as s_name, l2.name as d_name
        FROM roads r
        JOIN locations l1 ON r.source_id = l1.id
        JOIN locations l2 ON r.dest_id = l2.id
        WHERE r.id = ?;
        """, (disrupted_road_id,)).fetchone()
        conn.close()

        dist_diff = round(updated["total_distance"] - initial["total_distance"], 2) if updated["success"] and initial["success"] else 0.0

        return {
            "initial_route": initial,
            "updated_route": updated,
            "distance_difference": dist_diff,
            "disrupted_road": dict(road_info) if road_info else {"id": disrupted_road_id}
        }

graph_service = GraphService()
