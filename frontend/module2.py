import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random
import ctypes
import math
import time
from datetime import datetime
from backend.shipment_service import shipment_service, STATUS_MAP, STATUS_REVERSE_MAP
from backend.performance_service import performance_service
from backend.c_bridge import c_bridge, CShipment
from backend.database import get_db_connection

def render_module2():
    st.markdown('<h1 class="main-title">Module 2: Self-Optimizing Data Management & Integrity</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">C Implementation of Self-Balancing Trees, Hash Table Collision Resolution, Finite State Machine, and High-Performance Sorting</p>', unsafe_allow_html=True)

    sec_trees, sec_hash, sec_fsm, sec_sort = st.tabs([
        "1. Tree Structure Comparison",
        "2. Hash Table & Duplicate Detection",
        "3. Finite State Machine (FSM)",
        "4. Sorting Algorithm Comparison"
    ])

    # SECTION 1: Tree Structures
    with sec_trees:
        st.markdown("### Self-Balancing Tree Structures Performance Comparison")
        st.info("Demonstrates C implementations of BST, AVL Tree, Red-Black Tree, B-Tree (Order 4), and Splay Tree against the shipment dataset. Searching any Shipment ID benchmarks all 5 C trees simultaneously and retrieves the complete shipment cargo record containing that ID.")

        all_shipments_db = shipment_service.get_all_shipments()
        all_csv_ids = sorted([s["id"] for s in all_shipments_db]) if all_shipments_db else list(range(1, 111))
        min_csv_id = min(all_csv_ids) if all_csv_ids else 1
        max_csv_id = max(all_csv_ids) if all_csv_ids else 110

        col_t1, col_t2 = st.columns([1, 2])

        with col_t1:
            st.markdown("#### Input Dataset & Search")
            dataset_mode = st.radio(
                "Key Generation Mode:",
                [
                    "Complete CSV Dataset (All 110 Records)",
                    "Sample Subset (First 25 Records)",
                    "Custom Comma-Separated Keys"
                ],
                index=0
            )

            if dataset_mode == "Complete CSV Dataset (All 110 Records)":
                parsed_keys = all_csv_ids
                keys_str = ", ".join(map(str, parsed_keys))
                st.caption(f"Loaded all **{len(parsed_keys)}** shipment keys directly from `sample_shipments.csv` (IDs {min_csv_id} to {max_csv_id}).")
                with st.expander("View All Keys in Tree"):
                    st.write(keys_str)
            elif dataset_mode == "Sample Subset (First 25 Records)":
                parsed_keys = [s["id"] for s in all_shipments_db[:25]]
                keys_str = ", ".join(map(str, parsed_keys))
                raw_keys_input = st.text_area("Keys in Tree:", value=keys_str, height=90)
                parsed_keys = [int(k.strip()) for k in raw_keys_input.split(",") if k.strip().isdigit()]
            else:
                default_keys = "102, 108, 105, 114, 120, 101, 109, 115, 118, 125, 103, 111"
                raw_keys_input = st.text_area("Keys in Tree:", value=default_keys, height=90)
                parsed_keys = [int(k.strip()) for k in raw_keys_input.split(",") if k.strip().isdigit()]

            # Quick Preset Buttons
            st.markdown("**Quick Preset ID:**")
            p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns(5)
            preset_val = None
            if p_c1.button("ID 98"):
                preset_val = 98
            if p_c2.button("ID 42"):
                preset_val = 42
            if p_c3.button(f"Min ({min_csv_id})"):
                preset_val = min_csv_id
            if p_c4.button(f"Max ({max_csv_id})"):
                preset_val = max_csv_id
            if p_c5.button("🎲 Rand"):
                preset_val = random.choice(parsed_keys) if parsed_keys else 42

            if preset_val is not None:
                st.session_state["tree_search_target"] = preset_val

            curr_default_val = st.session_state.get("tree_search_target", 98)
            target_key = st.number_input(
                "Target Key (Shipment ID) to Search:",
                min_value=1,
                max_value=99999,
                value=int(curr_default_val),
                step=1,
                key="target_key_input"
            )

            btn_benchmark_trees = st.button("Execute Tree Search Across All 5 Structures", use_container_width=True)

        with col_t2:
            st.markdown("#### Real C Execution Benchmarks & Shipment Details")
            if (btn_benchmark_trees or True) and parsed_keys:
                tree_results = performance_service.benchmark_search_trees(parsed_keys, target_key)

                # =========================================================================
                # 1. ID CONTAINING DETAILS (TARGET SHIPMENT RECORD FROM DATASET)
                # =========================================================================
                shipment = shipment_service.get_shipment_by_id(target_key)

                st.markdown(f"#### 📦 Ingested Shipment Details for ID #{target_key}")
                if shipment:
                    priority_labels = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent", 5: "Critical"}
                    priority_colors = {1: "#64748b", 2: "#0284c7", 3: "#d97706", 4: "#ea580c", 5: "#dc2626"}
                    status_colors = {
                        0: ("Created", "#64748b", "#f1f5f9"),
                        1: ("Pending", "#d97706", "#fef3c7"),
                        2: ("Assigned", "#4f46e5", "#e0e7ff"),
                        3: ("In Transit", "#2563eb", "#dbeafe"),
                        4: ("Delivered", "#16a34a", "#dcfce7"),
                        5: ("Cancelled", "#dc2626", "#fee2e2"),
                    }
                    stat_name, stat_fg, stat_bg = status_colors.get(shipment["status"], ("Unknown", "#333", "#eee"))
                    prio_name = priority_labels.get(shipment["priority"], f"Priority {shipment['priority']}")
                    prio_color = priority_colors.get(shipment["priority"], "#333")

                    # Vehicle assignment lookup
                    conn = get_db_connection()
                    va_row = conn.execute("""
                        SELECT va.status as assign_status, v.vehicle_code, v.vehicle_type 
                        FROM vehicle_assignments va 
                        JOIN vehicles v ON va.vehicle_id = v.id 
                        WHERE va.shipment_id = ?
                    """, (target_key,)).fetchone()
                    conn.close()

                    vehicle_info = f"{va_row['vehicle_code']} ({va_row['vehicle_type']})" if va_row else "Awaiting Vehicle Dispatch"

                    # Deadline calculations
                    dl_dt = datetime.fromtimestamp(shipment["deadline_timestamp"])
                    now_ts = time.time()
                    hrs_remaining = round((shipment["deadline_timestamp"] - now_ts) / 3600, 1)
                    dl_str = dl_dt.strftime("%Y-%m-%d %H:%M")
                    if hrs_remaining > 0:
                        dl_display = f"{dl_str} ({hrs_remaining}h remaining)"
                    else:
                        dl_display = f"{dl_str} (Overdue by {abs(hrs_remaining)}h)"

                    # 4 Metric Cards for the Target ID
                    sm1, sm2, sm3, sm4 = st.columns(4)
                    with sm1:
                        st.markdown(f"""
                        <div class="metric-container" style="padding: 0.8rem;">
                            <div class="metric-label">Shipment Code</div>
                            <div class="metric-value" style="font-size: 1.35rem; color: #1e40af;">{shipment['shipment_code']}</div>
                            <div class="metric-footer">Database ID: {shipment['id']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with sm2:
                        st.markdown(f"""
                        <div class="metric-container" style="padding: 0.8rem;">
                            <div class="metric-label">Destination Hub</div>
                            <div class="metric-value" style="font-size: 1.05rem; font-weight: 600; line-height: 1.3;">{shipment['destination']}</div>
                            <div class="metric-footer">Fleet: {vehicle_info}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with sm3:
                        st.markdown(f"""
                        <div class="metric-container" style="padding: 0.8rem;">
                            <div class="metric-label">Cargo Specs</div>
                            <div class="metric-value" style="font-size: 1.25rem;">{shipment['weight']} <span style="font-size: 0.85rem; color: #64748b;">kg</span></div>
                            <div class="metric-footer">Volume: {shipment['volume']} m³</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with sm4:
                        st.markdown(f"""
                        <div class="metric-container" style="padding: 0.8rem;">
                            <div class="metric-label">Priority & Status</div>
                            <div style="margin-top: 0.2rem;">
                                <span style="background-color: {stat_bg}; color: {stat_fg}; font-weight: 700; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem;">{stat_name}</span>
                                <span style="color: {prio_color}; font-weight: 700; font-size: 0.8rem; margin-left: 4px;">● {prio_name}</span>
                            </div>
                            <div class="metric-footer" style="margin-top: 0.5rem; font-size: 0.75rem;">Deadline: {dl_display}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Full CSV Data Record Expander
                    with st.expander(f"View Complete CSV Data Attributes for ID #{target_key}"):
                        rec_df = pd.DataFrame([{
                            "ID": shipment["id"],
                            "Shipment Code": shipment["shipment_code"],
                            "Weight (kg)": shipment["weight"],
                            "Volume (m³)": shipment["volume"],
                            "Destination": shipment["destination"],
                            "Deadline": dl_str,
                            "Priority": f"{shipment['priority']} ({prio_name})",
                            "Status": stat_name,
                            "Vehicle Assigned": vehicle_info,
                            "Created At": shipment["created_at"],
                            "Updated At": shipment["updated_at"]
                        }])
                        st.dataframe(rec_df, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"⚠️ **Key #{target_key} NOT found in database.** (Valid CSV shipment IDs are {min_csv_id} to {max_csv_id}). The C search trees traversed their structures to verify key absence (`Found: No`).")

                st.markdown("---")

                # =========================================================================
                # 2. ALL 5 DETAILS: DETAILED C PERFORMANCE BENCHMARKS ACROSS ALL 5 TREES
                # =========================================================================
                st.markdown(f"#### 🌲 Performance & Structural Details Across All 5 Tree Structures")

                # 5 Metric Cards Side-by-Side
                tc1, tc2, tc3, tc4, tc5 = st.columns(5)
                tree_icons = {
                    "BST": ("🌳 BST", "#64748b"),
                    "AVL Tree": ("⚖️ AVL Tree", "#2563eb"),
                    "Red-Black Tree": ("🔴⚫ Red-Black", "#dc2626"),
                    "B-Tree": ("🌲 B-Tree (Ord 4)", "#16a34a"),
                    "Splay Tree": ("⚡ Splay Tree", "#7c3aed")
                }

                tree_cols = [tc1, tc2, tc3, tc4, tc5]
                for idx, (t_name, t_data) in enumerate(tree_results.items()):
                    icon_lbl, accent_c = tree_icons.get(t_name, (t_name, "#333"))
                    with tree_cols[idx]:
                        found_badge = '<span style="color: #16a34a; font-weight: 700;">✓ FOUND</span>' if t_data['found'] else '<span style="color: #dc2626; font-weight: 700;">✗ NOT FOUND</span>'
                        st.markdown(f"""
                        <div class="metric-container" style="border-top: 3px solid {accent_c}; padding: 0.75rem;">
                            <div class="metric-label" style="color: {accent_c}; font-size: 0.75rem;">{icon_lbl}</div>
                            <div class="metric-value" style="font-size: 1.4rem;">{t_data['comparisons']} <span style="font-size: 0.75rem; color: #64748b;">comps</span></div>
                            <div class="metric-footer" style="font-size: 0.75rem; line-height: 1.4;">
                                Height: <b>{t_data['height']} lvls</b><br>
                                Time: <b>{t_data['execution_time_us']} μs</b><br>
                                {found_badge}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Comprehensive Comparative Table
                table_rows = []
                mechanisms = {
                    "BST": "Standard binary search; no balancing; vulnerable to linear O(N) skew on sorted inputs",
                    "AVL Tree": "Strict height balancing: |h_L - h_R| ≤ 1 enforced via 4 rotation types (LL, RR, LR, RL)",
                    "Red-Black Tree": "Color invariant balancing (5 rules) with recoloring and rotations; height ≤ 2 log₂(N+1)",
                    "B-Tree": "Multi-way search tree (Order 4 / 2-3-4 tree) with high fan-out; minimum height",
                    "Splay Tree": "Self-adjusting tree: splays searched node to root via Zig, Zig-Zig, and Zig-Zag rotations"
                }

                optimal_height = math.floor(math.log2(len(parsed_keys))) + 1 if parsed_keys else 1

                for name, res in tree_results.items():
                    h_ratio = round(res["height"] / optimal_height, 2)
                    table_rows.append({
                        "Tree Structure": name,
                        "Found": "Yes (Found)" if res["found"] else "No (Absent)",
                        "Comparisons (C)": res["comparisons"],
                        "Execution Time (μs)": res["execution_time_us"],
                        "Height (Levels)": res["height"],
                        "Optimality (Height / log₂ N)": f"{h_ratio}x (Optimal: {optimal_height})",
                        "Balancing Mechanism": mechanisms.get(name, "Native C tree implementation"),
                        "Theoretical Complexity": res["time_complexity"],
                        "Space Complexity": res["space_complexity"]
                    })

                st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                # Charts
                fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 3.4))
                tree_names = list(tree_results.keys())
                comps = [tree_results[t]["comparisons"] for t in tree_names]
                heights = [tree_results[t]["height"] for t in tree_names]
                times = [tree_results[t]["execution_time_us"] for t in tree_names]
                colors = ["#64748b", "#2563eb", "#dc2626", "#16a34a", "#7c3aed"]

                # 1. Comparisons
                bars1 = ax1.bar(tree_names, comps, color=colors, width=0.6)
                ax1.set_ylabel("Comparison Count", fontweight="bold", fontsize=8)
                ax1.set_title("Search Comparisons", fontweight="bold", fontsize=9)
                ax1.tick_params(axis="x", rotation=30, labelsize=7)
                for b in bars1:
                    ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.1, f"{int(b.get_height())}", ha="center", fontsize=8, fontweight="bold")

                # 2. Height
                bars2 = ax2.bar(tree_names, heights, color=colors, width=0.6)
                ax2.axhline(optimal_height, color="#059669", linestyle="--", linewidth=1.5, label=f"Optimal ({optimal_height})")
                ax2.set_ylabel("Tree Height (Levels)", fontweight="bold", fontsize=8)
                ax2.set_title("Tree Height Levels", fontweight="bold", fontsize=9)
                ax2.tick_params(axis="x", rotation=30, labelsize=7)
                ax2.legend(fontsize=7, loc="upper right")
                for b in bars2:
                    ax2.text(b.get_x() + b.get_width()/2, b.get_height() + 0.1, f"{int(b.get_height())}", ha="center", fontsize=8, fontweight="bold")

                # 3. Execution Time
                bars3 = ax3.bar(tree_names, times, color=colors, width=0.6)
                ax3.set_ylabel("Time (μs)", fontweight="bold", fontsize=8)
                ax3.set_title("Execution Time (μs)", fontweight="bold", fontsize=9)
                ax3.tick_params(axis="x", rotation=30, labelsize=7)
                for b in bars3:
                    ax3.text(b.get_x() + b.get_width()/2, b.get_height() + 0.01, f"{b.get_height():.2f}", ha="center", fontsize=8, fontweight="bold")

                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

                # In-depth architectural explanation tabs
                with st.expander("🔬 In-Depth Structural Architecture: Why Self-Balancing Trees Outperform BST"):
                    st.markdown(fr"""
                    - **1. Binary Search Tree (BST)**: Insertion of pre-sorted data causes worst-case $O(N)$ degeneration into a linear linked list (Height = {tree_results['BST']['height']}, Comparisons = {tree_results['BST']['comparisons']}).
                    - **2. AVL Tree**: Enforces strict balance factor $|h_L - h_R| \le 1$. Uses 4 rotation cases (LL, RR, LR, RL) to guarantee optimal height ($h = {tree_results['AVL Tree']['height']}$) and minimal search comparisons ($C = {tree_results['AVL Tree']['comparisons']}$).
                    - **3. Red-Black Tree**: Uses 5 coloring invariants to maintain black-depth balance. Rebalancing requires fewer rotations during updates than AVL, guaranteeing height $\le 2\log_2(N+1)$ ($h = {tree_results['Red-Black Tree']['height']}$).
                    - **4. B-Tree (Order 4)**: A multi-way 2-3-4 tree where each node holds multiple keys and children. Has the lowest height ($h = {tree_results['B-Tree']['height']}$) and is the foundation for database disk indexing.
                    - **5. Splay Tree**: Self-adjusting tree that performs tree rotations (Zig, Zig-Zig, Zig-Zag) on access, splaying the searched key to the root. Subsequent accesses to key #{target_key} execute in $O(1)$ time.
                    """)
            else:
                st.info("Click 'Execute Tree Search Across All 5 Structures' to observe C comparison and height metrics.")

    # SECTION 2: Hash Table
    with sec_hash:
        st.markdown("### C Hash Table with Chaining & Duplicate Detection")
        st.info("Uses a polynomial hash function `hash = ((hash << 5) + hash) + c % TABLE_SIZE` with separate chaining in C to deliver O(1) average lookup and prevent duplicate shipment IDs.")

        h_c1, h_c2 = st.columns([1, 2])

        with h_c1:
            st.markdown("#### Hash Table Operations")
            test_id = st.text_input("Shipment Code to Test:", value="SHP-1005")
            col_b1, col_b2 = st.columns(2)

            with col_b1:
                if st.button("Search Hash Table"):
                    search_res = shipment_service.search_by_code_c_hash(test_id.strip())
                    if search_res["found"]:
                        st.success(f"Found '{test_id}' in C Hash Table!\n- Comparisons: {search_res['comparisons']}\n- Time: {search_res['time_us']} μs")
                    else:
                        st.error(f"'{test_id}' NOT found in C Hash Table (Comparisons: {search_res['comparisons']}).")

            with col_b2:
                if st.button("Detect Duplicate ID"):
                    dup = ctypes.c_int(0)
                    temp_s = CShipment()
                    temp_s.id = 9999
                    temp_s.shipment_code = test_id.strip().encode("utf-8")
                    c_bridge.lib.hash_insert(temp_s.shipment_code, ctypes.byref(temp_s), ctypes.byref(dup))
                    if dup.value == 1:
                        st.warning(f"DUPLICATE DETECTED! '{test_id}' is already registered in C Hash Table.")
                    else:
                        st.success(f"UNIQUE ID! '{test_id}' was inserted as a new entry.")

        with h_c2:
            st.markdown("#### Bucket Distribution & Collision Analysis")
            tot_elem = ctypes.c_int(0)
            col_cnt = ctypes.c_int(0)
            bucket_lens = (ctypes.c_int * 37)()
            c_bridge.lib.hash_get_stats(ctypes.byref(tot_elem), ctypes.byref(col_cnt), bucket_lens, 37)

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Total Elements", tot_elem.value)
            col_m2.metric("Hash Collisions", col_cnt.value)
            load_factor = round(tot_elem.value / 37.0, 2)
            col_m3.metric("Load Factor (λ)", load_factor)

            # Bar plot of bucket lengths
            fig, ax = plt.subplots(figsize=(8, 3.2))
            bucket_indices = list(range(37))
            lens = [bucket_lens[i] for i in bucket_indices]
            ax.bar(bucket_indices, lens, color="#3b82f6", width=0.7)
            ax.set_xlabel("Hash Table Bucket Index (0 to 36)", fontsize=9, fontweight="bold")
            ax.set_ylabel("Chain Length (Nodes)", fontsize=9, fontweight="bold")
            ax.set_title("Separate Chaining Collision Distribution", fontsize=10, fontweight="bold")
            ax.grid(axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # SECTION 3: Finite State Machine
    with sec_fsm:
        st.markdown("### C Finite State Machine (FSM) Lifecycle Validation")
        st.info("The C FSM enforces strict deterministic shipment lifecycle rules, preventing illegal state skips (e.g. Created -> Delivered) and protecting data integrity.")

        fsm_c1, fsm_c2 = st.columns([1, 1])

        with fsm_c1:
            st.markdown("#### Validate State Transition")
            all_s = shipment_service.get_all_shipments()
            selected_s_id = st.selectbox("Select Shipment:", [s["id"] for s in all_s],
                                         format_func=lambda x: f"ID {x}: {next(s['shipment_code'] for s in all_s if s['id'] == x)} [Current: {STATUS_MAP[next(s['status'] for s in all_s if s['id'] == x)]}]")
            curr_s = shipment_service.get_shipment_by_id(selected_s_id)

            curr_status_idx = curr_s["status"]
            st.write(f"**Current State:** `{STATUS_MAP[curr_status_idx]}` (Index: {curr_status_idx})")

            target_status_name = st.selectbox("Select Target State:", list(STATUS_MAP.values()), index=min(curr_status_idx + 1, 5))
            target_status_idx = STATUS_REVERSE_MAP[target_status_name]

            if st.button("Validate Transition with C FSM"):
                res = shipment_service.validate_and_update_status(selected_s_id, target_status_idx, "FSM UI Transition Test")
                if res["valid"]:
                    st.success(f"VALID TRANSITION:\n{res['message']}")
                    st.rerun()
                else:
                    st.error(f"INVALID TRANSITION BLOCKED BY C FSM:\n{res['message']}")

        with fsm_c2:
            st.markdown("#### Lifecycle State Transition Rules Matrix")
            fsm_table = [
                {"Current State": "Created", "Allowed Next States": "Pending, Cancelled", "Terminal": "No"},
                {"Current State": "Pending", "Allowed Next States": "Assigned, Cancelled", "Terminal": "No"},
                {"Current State": "Assigned", "Allowed Next States": "In Transit, Pending (Unassign), Cancelled", "Terminal": "No"},
                {"Current State": "In Transit", "Allowed Next States": "Delivered, Cancelled", "Terminal": "No"},
                {"Current State": "Delivered", "Allowed Next States": "None (Terminal State)", "Terminal": "Yes"},
                {"Current State": "Cancelled", "Allowed Next States": "None (Terminal State)", "Terminal": "Yes"}
            ]
            st.dataframe(pd.DataFrame(fsm_table), use_container_width=True, hide_index=True)

    # SECTION 4: Sorting Algorithms
    with sec_sort:
        st.markdown("### C Sorting Algorithm Performance Comparison")
        st.info("Implements Quick Sort (median pivot), Merge Sort (divide-and-conquer), and Heap Sort (in-place binary max-heap) in C.")

        sort_c1, sort_c2 = st.columns([1, 2])

        with sort_c1:
            st.markdown("#### Sorting Parameters")
            criterion = st.selectbox("Sort Shipment Records By:", ["Weight", "Priority", "Deadline", "ID"])
            crit_key = criterion.lower()
            all_s = shipment_service.get_all_shipments()

            st.write(f"Total Records in Dataset: **{len(all_s)}**")
            sort_algo_choice = st.radio("Execute Individual Algorithm:", ["Quick Sort", "Merge Sort", "Heap Sort", "Compare All Three"])
            btn_run_sort = st.button("Run C Sorting Execution")

        with sort_c2:
            st.markdown("#### Sorting Execution & Performance Results")
            if btn_run_sort:
                if sort_algo_choice == "Compare All Three":
                    res_qs = shipment_service.sort_shipments_c(all_s, criterion=crit_key, algorithm="Quick Sort")
                    res_ms = shipment_service.sort_shipments_c(all_s, criterion=crit_key, algorithm="Merge Sort")
                    res_hs = shipment_service.sort_shipments_c(all_s, criterion=crit_key, algorithm="Heap Sort")

                    comp_df = pd.DataFrame([
                        {"Algorithm": "Quick Sort", "Execution Time (μs)": res_qs["time_us"], "Comparisons": res_qs["comparisons"], "Operations": res_qs["operations"], "Time Complexity": "O(N log N) avg"},
                        {"Algorithm": "Merge Sort", "Execution Time (μs)": res_ms["time_us"], "Comparisons": res_ms["comparisons"], "Operations": res_ms["operations"], "Time Complexity": "O(N log N) worst"},
                        {"Algorithm": "Heap Sort", "Execution Time (μs)": res_hs["time_us"], "Comparisons": res_hs["comparisons"], "Operations": res_hs["operations"], "Time Complexity": "O(N log N) in-place"}
                    ])
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)

                    # Bar chart
                    fig, ax = plt.subplots(figsize=(6, 3))
                    bars = ax.bar(["Quick Sort", "Merge Sort", "Heap Sort"], [res_qs["time_us"], res_ms["time_us"], res_hs["time_us"]],
                                  color=["#3b82f6", "#10b981", "#f59e0b"], width=0.55)
                    ax.set_ylabel("Execution Time (μs)", fontweight="bold", fontsize=9)
                    ax.set_title(f"Sorting Performance on {len(all_s)} Shipments ({criterion})", fontweight="bold", fontsize=10)
                    for b in bars:
                        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.1, f"{b.get_height():.2f} μs", ha="center", fontsize=8, fontweight="bold")
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)

                    st.markdown("##### Sorted Dataset Preview")
                    st.dataframe(pd.DataFrame(res_qs["sorted"]).head(10), use_container_width=True, hide_index=True)

                else:
                    res = shipment_service.sort_shipments_c(all_s, criterion=crit_key, algorithm=sort_algo_choice)
                    st.success(f"{sort_algo_choice} Complete:\n- Execution Time: {res['time_us']} μs\n- Comparisons: {res['comparisons']}\n- Operations: {res['operations']}")
                    st.markdown("##### Sorted Shipment Dataset")
                    st.dataframe(pd.DataFrame(res["sorted"]), use_container_width=True, hide_index=True)
            else:
                st.info("Select sorting parameters and click 'Run C Sorting Execution'.")
