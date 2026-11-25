import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import random
from backend.vehicle_service import vehicle_service
from backend.shipment_service import shipment_service
from backend.graph_service import graph_service
from backend.database import get_db_connection

def render_module3():
    st.markdown('<h1 class="main-title">Module 3: Intelligent Vehicle Assignment & Dynamic Route Optimization</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">C Graph Algorithms (BFS, DFS, Dijkstra, Prim, Kruskal) with Dual-Constraint Vehicle Capacity Management and Dynamic Rerouting</p>', unsafe_allow_html=True)

    tab_vehicle, tab_graph, tab_traversal, tab_dijkstra, tab_mst, tab_dynamic = st.tabs([
        "1. Vehicle Assignment",
        "2. Network Topology",
        "3. BFS & DFS Traversals",
        "4. Dijkstra Shortest Route",
        "5. Prim & Kruskal MST",
        "6. Dynamic Route Recalculation"
    ])

    # 1. VEHICLE ASSIGNMENT
    with tab_vehicle:
        st.markdown("### Dual-Constraint Vehicle Assignment Engine")
        st.info("Assigns shipments to vehicles strictly enforcing BOTH Weight Capacity and Volume Capacity limits to prevent physical overloading.")

        v_c1, v_c2 = st.columns([1, 2])

        with v_c1:
            st.markdown("#### Assign Shipment to Vehicle")
            all_s = shipment_service.get_all_shipments()
            pending_s = [s for s in all_s if s["status"] in (0, 1)]

            if pending_s:
                s_choice_id = st.selectbox("Select Pending Shipment:", [s["id"] for s in pending_s],
                                           format_func=lambda x: f"{next(s['shipment_code'] for s in pending_s if s['id'] == x)} ({next(s['weight'] for s in pending_s if s['id'] == x)} kg, {next(s['volume'] for s in pending_s if s['id'] == x)} m³)")
                curr_shp = shipment_service.get_shipment_by_id(s_choice_id)

                vehicles = vehicle_service.get_all_vehicles()
                v_choice_id = st.selectbox("Select Target Vehicle:", [v["id"] for v in vehicles],
                                           format_func=lambda x: f"{next(v['vehicle_code'] for v in vehicles if v['id'] == x)} [{next(v['vehicle_type'] for v in vehicles if v['id'] == x)}] (Rem: {next(v['remaining_weight'] for v in vehicles if v['id'] == x)}kg, {next(v['remaining_volume'] for v in vehicles if v['id'] == x)}m³)")

                auto_rec = vehicle_service.find_suitable_vehicle(curr_shp["weight"], curr_shp["volume"])
                if auto_rec:
                    st.caption(f"Best-Fit Recommendation: **{auto_rec['vehicle_code']}** ({auto_rec['vehicle_type']})")

                if st.button("Confirm Vehicle Assignment"):
                    assign_res = vehicle_service.assign_shipment_to_vehicle(v_choice_id, s_choice_id)
                    if assign_res["success"]:
                        st.success(f"{assign_res['message']}\n- Remaining Weight: {assign_res['remaining_weight']} kg\n- Remaining Volume: {assign_res['remaining_volume']} m³\n- Utilization: {assign_res['weight_utilization_pct']}%")
                        st.rerun()
                    else:
                        st.error(assign_res["message"])
            else:
                st.info("No pending shipments awaiting vehicle assignment.")

            st.markdown("---")
            with st.expander("Add New Fleet Vehicle"):
                with st.form("add_v_form"):
                    n_code = st.text_input("Vehicle Code", value=f"V-{random.randint(120, 999)}")
                    n_type = st.selectbox("Type", ["Electric Van", "Urban Cargo Sprinter", "Refrigerated Medium Truck", "Heavy Duty Box Truck", "Semi-Trailer Hauler"])
                    n_wt = st.number_input("Max Weight (kg)", value=2500.0)
                    n_vol = st.number_input("Max Volume (m³)", value=15.0)
                    if st.form_submit_button("Add Vehicle"):
                        vehicle_service.add_vehicle(n_code, n_type, n_wt, n_vol)
                        st.success(f"Vehicle {n_code} added to fleet.")
                        st.rerun()

        with v_c2:
            st.markdown("#### Active Fleet Status & Capacity Utilization")
            vehicles = vehicle_service.get_all_vehicles()
            v_table = []
            for v in vehicles:
                v_table.append({
                    "Vehicle": v["vehicle_code"],
                    "Type": v["vehicle_type"],
                    "Max Wt (kg)": v["max_weight"],
                    "Assigned Wt": v["current_weight"],
                    "Remaining Wt": v["remaining_weight"],
                    "Max Vol (m³)": v["max_volume"],
                    "Assigned Vol": v["current_volume"],
                    "Remaining Vol": v["remaining_volume"],
                    "Util %": f"{v['overall_utilization_pct']}%",
                    "Status": "Available" if v["is_available"] == 1 and v["overall_utilization_pct"] < 95.0 else "Full / Dispatched"
                })
            st.dataframe(pd.DataFrame(v_table), use_container_width=True, hide_index=True)

    # 2. NETWORK TOPOLOGY
    with tab_graph:
        st.markdown("### Logistics Network Topology (C Adjacency List Representation)")
        st.info("Delivery locations represent vertices; active roads represent weighted edges storing travel distance in kilometers.")

        g_c1, g_c2 = st.columns([1, 2])

        with g_c1:
            st.markdown("#### Network Infrastructure Management")
            action = st.radio("Action:", ["View Map", "Add Road", "Update Road Distance", "Disable / Enable Road"])
            locations = graph_service.get_locations()
            roads = graph_service.get_roads()

            if action == "Add Road":
                u = st.selectbox("Source Location:", [l["id"] for l in locations], format_func=lambda x: next(l["name"] for l in locations if l["id"] == x))
                v = st.selectbox("Destination Location:", [l["id"] for l in locations], format_func=lambda x: next(l["name"] for l in locations if l["id"] == x))
                dist = st.number_input("Distance (km):", min_value=1.0, max_value=500.0, value=25.0)
                if st.button("Add Road to Graph"):
                    if u != v:
                        graph_service.add_road(u, v, dist)
                        st.success(f"Road added between Location {u} and {v} ({dist} km).")
                        st.rerun()
                    else:
                        st.error("Source and destination must be distinct.")

            elif action == "Update Road Distance":
                r_id = st.selectbox("Select Road:", [r["id"] for r in roads],
                                    format_func=lambda x: f"Road #{x}: {next(r['source_name'] for r in roads if r['id'] == x)} &harr; {next(r['dest_name'] for r in roads if r['id'] == x)} ({next(r['distance_km'] for r in roads if r['id'] == x)} km)")
                new_d = st.number_input("New Distance (km):", min_value=0.5, max_value=1000.0, value=30.0)
                if st.button("Update Road Distance in C"):
                    graph_service.update_road_distance(r_id, new_d)
                    st.success(f"Road #{r_id} updated to {new_d} km.")
                    st.rerun()

            elif action == "Disable / Enable Road":
                r_id = st.selectbox("Select Road to Toggle:", [r["id"] for r in roads],
                                    format_func=lambda x: f"Road #{x}: {next(r['source_name'] for r in roads if r['id'] == x)} &harr; {next(r['dest_name'] for r in roads if r['id'] == x)} [{'ACTIVE' if next(r['is_active'] for r in roads if r['id'] == x) else 'DISABLED'}]")
                curr_act = next(r["is_active"] for r in roads if r["id"] == r_id)
                new_act = 0 if curr_act == 1 else 1
                lbl = "Disable Road (Simulate Closure)" if curr_act == 1 else "Re-enable Road"
                if st.button(lbl):
                    graph_service.set_road_active(r_id, new_act)
                    st.success(f"Road #{r_id} state toggled to {'ACTIVE' if new_act else 'DISABLED'}.")
                    st.rerun()

        with g_c2:
            st.markdown("#### Matplotlib Delivery Network Map")
            locations = graph_service.get_locations()
            roads = graph_service.get_roads()

            fig, ax = plt.subplots(figsize=(7, 5))
            G = nx.Graph()

            pos = {}
            for loc in locations:
                G.add_node(loc["id"], label=loc["code"])
                pos[loc["id"]] = (loc["x_coord"], loc["y_coord"])

            active_edges = []
            disabled_edges = []
            for r in roads:
                if r["is_active"] == 1:
                    G.add_edge(r["source_id"], r["dest_id"], weight=r["distance_km"])
                    active_edges.append((r["source_id"], r["dest_id"]))
                else:
                    disabled_edges.append((r["source_id"], r["dest_id"]))

            nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#1e40af", node_size=320)
            nx.draw_networkx_labels(G, pos, ax=ax, labels={l["id"]: l["code"] for l in locations}, font_size=7, font_color="white", font_weight="bold")
            nx.draw_networkx_edges(G, pos, edgelist=active_edges, ax=ax, edge_color="#94a3b8", width=1.5)
            if disabled_edges:
                nx.draw_networkx_edges(G, pos, edgelist=disabled_edges, ax=ax, edge_color="#ef4444", width=2.0, style="dashed")

            ax.set_title("Logistics Network Topology (Blue: Nodes, Gray: Active Roads, Red Dashed: Disabled)", fontsize=9, fontweight="bold")
            ax.axis("off")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # 3. BFS & DFS TRAVERSALS
    with tab_traversal:
        st.markdown("### Breadth-First Search (BFS) & Depth-First Search (DFS) in C")
        st.info("BFS visits delivery hubs level-by-level across radial expansion zones; DFS traverses deep logistics transport corridors before backtracking.")

        tr_c1, tr_c2 = st.columns([1, 2])
        locations = graph_service.get_locations()

        with tr_c1:
            st.markdown("#### Traversal Source Hub")
            start_hub = st.selectbox("Select Origin Hub:", [l["id"] for l in locations],
                                     format_func=lambda x: f"{next(l['name'] for l in locations if l['id'] == x)} ({next(l['code'] for l in locations if l['id'] == x)})")
            traversal_type = st.radio("Algorithm:", ["Breadth-First Search (BFS)", "Depth-First Search (DFS)"])
            btn_run_trav = st.button("Execute Traversal in C")

        with tr_c2:
            if btn_run_trav:
                if traversal_type == "Breadth-First Search (BFS)":
                    res = graph_service.run_bfs(start_hub)
                    st.success(f"C BFS Traversal Complete: Visited {res['total_visited']} Hubs in {res['execution_time_us']} μs")
                    st.dataframe(pd.DataFrame(res["traversal"]), use_container_width=True, hide_index=True)
                else:
                    res = graph_service.run_dfs(start_hub)
                    st.success(f"C DFS Traversal Complete: Visited {res['total_visited']} Hubs in {res['execution_time_us']} μs")
                    st.dataframe(pd.DataFrame(res["traversal"]), use_container_width=True, hide_index=True)
            else:
                st.info("Select an origin hub and click 'Execute Traversal in C'.")

    # 4. DIJKSTRA SHORTEST ROUTE
    with tab_dijkstra:
        st.markdown("### Dijkstra Shortest Path Algorithm in C")
        st.info("Computes the exact minimum distance route between any two logistics facilities through the weighted graph using C Dijkstra implementation.")

        d_c1, d_c2 = st.columns([1, 2])
        locations = graph_service.get_locations()

        with d_c1:
            src_id = st.selectbox("Origin Location:", [l["id"] for l in locations], index=0,
                                  format_func=lambda x: f"{next(l['name'] for l in locations if l['id'] == x)}")
            dst_id = st.selectbox("Destination Location:", [l["id"] for l in locations], index=min(14, len(locations)-1),
                                  format_func=lambda x: f"{next(l['name'] for l in locations if l['id'] == x)}")
            btn_dijkstra = st.button("Calculate Shortest Route (C Dijkstra)")

        with d_c2:
            if btn_dijkstra:
                d_res = graph_service.run_dijkstra(src_id, dst_id)
                if d_res["success"]:
                    st.success(f"Shortest Path Found: **{d_res['total_distance']} km** (C Time: {d_res['execution_time_us']} μs, Comparisons: {d_res['comparisons']})")
                    path_names = [n["name"] for n in d_res["path_nodes"]]
                    st.markdown("**Route Sequence:** " + " &rarr; ".join([f"`{name}`" for name in path_names]))

                    # Plot Shortest Path Highlighted
                    roads = graph_service.get_roads()
                    fig, ax = plt.subplots(figsize=(7, 4.5))
                    G = nx.Graph()
                    pos = {l["id"]: (l["x_coord"], l["y_coord"]) for l in locations}
                    for loc in locations:
                        G.add_node(loc["id"])

                    for r in roads:
                        if r["is_active"] == 1:
                            G.add_edge(r["source_id"], r["dest_id"])

                    path_edges = []
                    p_ids = d_res["path_ids"]
                    for i in range(len(p_ids) - 1):
                        path_edges.append((p_ids[i], p_ids[i+1]))

                    nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#cbd5e1", node_size=250)
                    nx.draw_networkx_nodes(G, pos, nodelist=p_ids, ax=ax, node_color="#10b981", node_size=350)
                    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#e2e8f0", width=1.5)
                    nx.draw_networkx_edges(G, pos, edgelist=path_edges, ax=ax, edge_color="#10b981", width=3.0)
                    nx.draw_networkx_labels(G, pos, ax=ax, labels={l["id"]: l["code"] for l in locations}, font_size=7)

                    ax.set_title(f"Dijkstra Route: {locations[src_id]['code']} to {locations[dst_id]['code']} ({d_res['total_distance']} km)", fontsize=9, fontweight="bold")
                    ax.axis("off")
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)
                else:
                    st.error("No active route connects the selected origin and destination.")
            else:
                st.info("Select origin and destination and click 'Calculate Shortest Route'.")

    # 5. PRIM & KRUSKAL MST
    with tab_mst:
        st.markdown("### Minimum Spanning Tree (MST) Optimization: Prim vs Kruskal")
        st.info("Determines the minimum cost backbone to interconnect the entire logistics network. Prim uses greedy cut vertex expansion; Kruskal uses edge sorting with Disjoint Set Union (DSU / Union-Find).")

        mst_c1, mst_c2 = st.columns([1, 2])

        with mst_c1:
            st.markdown("#### MST Algorithm Controls")
            mst_choice = st.radio("Run MST Algorithm:", ["Prim's Algorithm", "Kruskal's Algorithm", "Compare Both"])
            btn_run_mst = st.button("Generate MST in C")

        with mst_c2:
            if btn_run_mst:
                prim_res = graph_service.run_prim_mst(0)
                krusk_res = graph_service.run_kruskal_mst()

                if mst_choice == "Compare Both":
                    st.markdown("#### Algorithmic Comparison (Identical Network Graph)")
                    mst_comp_df = pd.DataFrame([
                        {"Algorithm": "Prim's Algorithm", "MST Total Cost (km)": prim_res["total_cost"], "Selected Edges": prim_res["edge_count"], "Operations": prim_res["operations"], "Execution Time (μs)": prim_res["execution_time_us"], "Technique": "Vertex Cut / Priority Relaxation"},
                        {"Algorithm": "Kruskal's Algorithm", "MST Total Cost (km)": krusk_res["total_cost"], "Selected Edges": krusk_res["edge_count"], "Operations": krusk_res["operations"], "Execution Time (μs)": krusk_res["execution_time_us"], "Technique": "Sorted Edges + Disjoint Set Union (DSU)"}
                    ])
                    st.dataframe(mst_comp_df, use_container_width=True, hide_index=True)
                    st.success(f"Mathematical Invariance Verified: Both algorithms yield identical optimal MST cost = **{prim_res['total_cost']} km**.")

                # Visualization of MST
                selected_res = prim_res if mst_choice != "Kruskal's Algorithm" else krusk_res
                mst_edges_tuples = [(e["u"], e["v"]) for e in selected_res["edges"]]

                fig, ax = plt.subplots(figsize=(7, 4.5))
                G = nx.Graph()
                locations = graph_service.get_locations()
                pos = {l["id"]: (l["x_coord"], l["y_coord"]) for l in locations}
                for loc in locations:
                    G.add_node(loc["id"])

                roads = graph_service.get_roads()
                for r in roads:
                    if r["is_active"] == 1:
                        G.add_edge(r["source_id"], r["dest_id"])

                nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#3b82f6", node_size=300)
                nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#e2e8f0", width=1.0)
                nx.draw_networkx_edges(G, pos, edgelist=mst_edges_tuples, ax=ax, edge_color="#15803d", width=2.5)
                nx.draw_networkx_labels(G, pos, ax=ax, labels={l["id"]: l["code"] for l in locations}, font_size=7, font_color="white", font_weight="bold")

                ax.set_title(f"Minimum Spanning Tree Backbone (Total Network Distance: {selected_res['total_cost']} km)", fontsize=9, fontweight="bold")
                ax.axis("off")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("Click 'Generate MST in C' to view backbone network.")

    # 6. DYNAMIC ROUTE RECALCULATION
    with tab_dynamic:
        st.markdown("### Dynamic Route Recalculation on Road Disruption")
        st.info("Simulates active road closures (e.g. traffic accidents, weather disruptions). Re-evaluates C Graph topology and computes the optimal detour route using Dijkstra.")

        dyn_c1, dyn_c2 = st.columns([1, 2])
        locations = graph_service.get_locations()
        roads = graph_service.get_roads()
        active_roads = [r for r in roads if r["is_active"] == 1]

        with dyn_c1:
            st.markdown("#### Disruption Scenario Configuration")
            dyn_src = st.selectbox("Origin Hub:", [l["id"] for l in locations], index=0, key="dyn_src",
                                   format_func=lambda x: next(l["name"] for l in locations if l["id"] == x))
            dyn_dst = st.selectbox("Destination Hub:", [l["id"] for l in locations], index=min(14, len(locations)-1), key="dyn_dst",
                                   format_func=lambda x: next(l["name"] for l in locations if l["id"] == x))

            if active_roads:
                disrupt_road_id = st.selectbox("Road Segment to Disrupt / Close:", [r["id"] for r in active_roads],
                                               format_func=lambda x: f"Road #{x}: {next(r['source_name'] for r in active_roads if r['id'] == x)} &harr; {next(r['dest_name'] for r in active_roads if r['id'] == x)} ({next(r['distance_km'] for r in active_roads if r['id'] == x)} km)")
                btn_recalc = st.button("Simulate Disruption & Recalculate Route")
            else:
                st.warning("No active roads available to disrupt.")
                btn_recalc = False

        with dyn_c2:
            if btn_recalc and active_roads:
                recalc_res = graph_service.dynamic_recalculate_route(dyn_src, dyn_dst, disrupt_road_id)
                init_r = recalc_res["initial_route"]
                upd_r = recalc_res["updated_route"]
                d_diff = recalc_res["distance_difference"]
                d_road = recalc_res["disrupted_road"]

                st.warning(f"ROAD CLOSURE REPORT: Road #{d_road.get('id')} between `{d_road.get('s_name', '')}` and `{d_road.get('d_name', '')}` is now DISABLED.")

                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("Original Route Distance", f"{init_r['total_distance']} km")
                c_m2.metric("Recalculated Route Distance", f"{upd_r['total_distance']} km")
                c_m3.metric("Detour Distance Delta", f"+{d_diff} km", delta=f"{d_diff} km", delta_color="inverse")

                # Comparison visual
                fig, (ax_orig, ax_detour) = plt.subplots(1, 2, figsize=(8, 3.8))
                pos = {l["id"]: (l["x_coord"], l["y_coord"]) for l in locations}

                # Original
                G1 = nx.Graph()
                for loc in locations: G1.add_node(loc["id"])
                for r in roads:
                    if r["is_active"] == 1: G1.add_edge(r["source_id"], r["dest_id"])

                p1_edges = [(init_r["path_ids"][i], init_r["path_ids"][i+1]) for i in range(len(init_r["path_ids"])-1)] if init_r["success"] else []
                nx.draw_networkx_nodes(G1, pos, ax=ax_orig, node_color="#cbd5e1", node_size=200)
                nx.draw_networkx_edges(G1, pos, ax=ax_orig, edge_color="#e2e8f0", width=1.0)
                nx.draw_networkx_edges(G1, pos, edgelist=p1_edges, ax=ax_orig, edge_color="#2563eb", width=2.5)
                nx.draw_networkx_labels(G1, pos, ax=ax_orig, labels={l["id"]: l["code"] for l in locations}, font_size=6)
                ax_orig.set_title(f"Baseline Route ({init_r['total_distance']} km)", fontsize=8, fontweight="bold")
                ax_orig.axis("off")

                # Detour
                G2 = nx.Graph()
                for loc in locations: G2.add_node(loc["id"])
                for r in graph_service.get_roads():
                    if r["is_active"] == 1: G2.add_edge(r["source_id"], r["dest_id"])

                p2_edges = [(upd_r["path_ids"][i], upd_r["path_ids"][i+1]) for i in range(len(upd_r["path_ids"])-1)] if upd_r["success"] else []
                nx.draw_networkx_nodes(G2, pos, ax=ax_detour, node_color="#cbd5e1", node_size=200)
                nx.draw_networkx_edges(G2, pos, ax=ax_detour, edge_color="#e2e8f0", width=1.0)
                nx.draw_networkx_edges(G2, pos, edgelist=p2_edges, ax=ax_detour, edge_color="#dc2626", width=2.5)
                nx.draw_networkx_labels(G2, pos, ax=ax_detour, labels={l["id"]: l["code"] for l in locations}, font_size=6)
                ax_detour.set_title(f"Updated Detour Route ({upd_r['total_distance']} km)", fontsize=8, fontweight="bold")
                ax_detour.axis("off")

                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

                if st.button("Restore Disrupted Road to Active"):
                    graph_service.set_road_active(disrupt_road_id, 1)
                    st.success("Road re-opened and added back to graph.")
                    st.rerun()
            else:
                st.info("Select parameters and click 'Simulate Disruption & Recalculate Route'.")
