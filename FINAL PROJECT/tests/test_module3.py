import pytest
from backend.vehicle_service import vehicle_service
from backend.graph_service import graph_service
from backend.shipment_service import shipment_service

def test_vehicle_capacity_and_overload_prevention():
    vehicles = vehicle_service.get_all_vehicles()
    assert len(vehicles) >= 15

    # Test overload rejection: try to assign huge weight exceeding capacity
    v = vehicles[0]
    # Create temporary shipment with massive weight
    all_s = shipment_service.get_all_shipments()
    s = [x for x in all_s if x["status"] in (0, 1)][0]

    # Temporarily set shipment weight to exceed vehicle max weight
    conn = vehicle_service.get_db_connection() if hasattr(vehicle_service, "get_db_connection") else None
    from backend.database import get_db_connection
    conn = get_db_connection()
    conn.execute("UPDATE shipments SET weight = 999999.0 WHERE id = ?;", (s["id"],))
    conn.commit()
    conn.close()

    res = vehicle_service.assign_shipment_to_vehicle(v["id"], s["id"])
    assert res["success"] is False
    assert "Overload Rejected" in res["message"]

    # Restore weight
    conn = get_db_connection()
    conn.execute("UPDATE shipments SET weight = 50.0 WHERE id = ?;", (s["id"],))
    conn.commit()
    conn.close()

def test_graph_bfs_and_dfs():
    graph_service.sync_graph_from_db()
    bfs_res = graph_service.run_bfs(0)
    assert bfs_res["total_visited"] >= 10
    assert bfs_res["traversal"][0]["node_id"] == 0

    dfs_res = graph_service.run_dfs(0)
    assert dfs_res["total_visited"] >= 10
    assert dfs_res["traversal"][0]["node_id"] == 0

def test_dijkstra_shortest_path():
    graph_service.sync_graph_from_db()
    dijk = graph_service.run_dijkstra(0, 14)
    assert dijk["success"] is True
    assert dijk["total_distance"] > 0
    assert dijk["path_ids"][0] == 0
    assert dijk["path_ids"][-1] == 14

def test_prim_and_kruskal_mst_invariance():
    graph_service.sync_graph_from_db()
    prim = graph_service.run_prim_mst(0)
    krusk = graph_service.run_kruskal_mst()

    assert prim["edge_count"] > 0
    assert krusk["edge_count"] > 0
    # Both MST algorithms must yield identical total cost
    assert abs(prim["total_cost"] - krusk["total_cost"]) < 1e-4

def test_dynamic_route_recalculation():
    graph_service.sync_graph_from_db()
    roads = graph_service.get_roads()
    active_roads = [r for r in roads if r["is_active"] == 1]
    assert len(active_roads) > 0

    road_to_close = active_roads[0]
    recalc = graph_service.dynamic_recalculate_route(0, 14, road_to_close["id"])
    assert "initial_route" in recalc
    assert "updated_route" in recalc
    assert "distance_difference" in recalc

    # Restore road
    graph_service.set_road_active(road_to_close["id"], 1)
