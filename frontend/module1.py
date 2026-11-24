import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from backend.shipment_service import shipment_service, STATUS_MAP, PRIORITY_MAP
from backend.graph_service import graph_service
from backend.database import get_db_connection
from backend.c_bridge import c_bridge, CShipment
import ctypes

def render_module1():
    st.markdown('<h1 class="main-title">Module 1: Adaptive Shipment Processing & Deadline Management</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">C-Powered Dynamic Linked List, Stack History, FIFO Queue, Priority Queue Scheduler, and Min-Heap Deadline Engine</p>', unsafe_allow_html=True)

    # 1. Summary Metrics Strip
    metrics = shipment_service.get_summary_metrics()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Shipments", metrics["total"])
    c2.metric("Pending Queue", metrics["pending"])
    c3.metric("Processed / Delivered", metrics["delivered"])
    c4.metric("Urgent (Priority ≥ 4)", metrics["urgent"])
    c5.metric("Imminent Deadlines (<24h)", metrics["imminent_deadlines"])

    st.markdown("---")

    # 2. Add New Shipment Form
    with st.expander("Register New Shipment Record (Inserts to C Linked List & C Hash Table)", expanded=False):
        with st.form("add_shipment_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                shipment_code = st.text_input("Shipment Code / ID", value=f"SHP-{int(time.time()) % 10000 + 2000}")
                weight = st.number_input("Weight (kg)", min_value=0.5, max_value=25000.0, value=125.0, step=5.0)
            with f_col2:
                locations = [loc["name"] for loc in graph_service.get_locations()]
                destination = st.selectbox("Destination Hub", locations if locations else ["Central Distribution Center"])
                volume = st.number_input("Volume (m³)", min_value=0.01, max_value=120.0, value=1.5, step=0.1)
            with f_col3:
                deadline_hours = st.slider("Deadline (Hours from Now)", min_value=1, max_value=168, value=24)
                priority = st.selectbox("Priority Level", options=[1, 2, 3, 4, 5],
                                       format_func=lambda x: f"{x} - {PRIORITY_MAP[x]}")

            submit_add = st.form_submit_button("Add Shipment (Execute C Insertion)")
            if submit_add:
                deadline_ts = int(time.time()) + (deadline_hours * 3600)
                try:
                    new_id = shipment_service.create_shipment(
                        shipment_code.strip(), weight, volume, destination, deadline_ts, priority
                    )
                    st.success(f"Shipment {shipment_code} successfully registered with Database ID {new_id}! Added to C Linked List, Queue, and Min-Heap.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Insertion Error: {str(e)}")

    # 3. Tabbed Interactive C Data Structures Operations
    tab_ll, tab_stack, tab_queue, tab_pq, tab_heap = st.tabs([
        "A. Linked List",
        "B. Stack (Audit & Undo)",
        "C. FIFO Queue",
        "D. Priority Queue",
        "E. Deadline Min-Heap"
    ])

    # TAB A: Linked List
    with tab_ll:
        st.markdown("### C Dynamic Linked List Operations")
        st.info("The C Linked List dynamically manages all active shipment records in memory, supporting O(1) head/tail insertions, O(N) linear deletions, and field updates.")

        ll_col1, ll_col2 = st.columns([1, 2])

        with ll_col1:
            st.markdown("#### Operations")
            op_choice = st.radio("Select Linked List Action:", ["View All Records", "Update Shipment", "Delete Shipment"])

            if op_choice == "Delete Shipment":
                all_s = shipment_service.get_all_shipments()
                del_id = st.selectbox("Select Shipment to Delete:", [s["id"] for s in all_s],
                                      format_func=lambda x: f"ID {x}: {next(s['shipment_code'] for s in all_s if s['id'] == x)}")
                if st.button("Execute C Deletion"):
                    if shipment_service.delete_shipment(del_id):
                        st.success(f"Shipment ID {del_id} successfully deleted from C Linked List and Database.")
                        st.rerun()
                    else:
                        st.error("Deletion failed.")

            elif op_choice == "Update Shipment":
                all_s = shipment_service.get_all_shipments()
                up_id = st.selectbox("Select Shipment to Update:", [s["id"] for s in all_s],
                                     format_func=lambda x: f"ID {x}: {next(s['shipment_code'] for s in all_s if s['id'] == x)}")
                curr = shipment_service.get_shipment_by_id(up_id)
                new_wt = st.number_input("New Weight (kg)", value=float(curr["weight"]))
                new_vol = st.number_input("New Volume (m³)", value=float(curr["volume"]))
                new_pri = st.selectbox("New Priority", [1, 2, 3, 4, 5], index=curr["priority"] - 1,
                                       format_func=lambda x: f"{x} - {PRIORITY_MAP[x]}")
                new_stat = st.selectbox("New Status", [0, 1, 2, 3, 4, 5], index=curr["status"],
                                        format_func=lambda x: f"{x} - {STATUS_MAP[x]}")

                if st.button("Execute C Update"):
                    res = shipment_service.validate_and_update_status(up_id, new_stat, f"Updated weight to {new_wt}kg, vol to {new_vol}m³")
                    if res["valid"]:
                        st.success(f"C Linked List and Database updated: {res['message']}")
                        st.rerun()
                    else:
                        st.error(f"FSM Rejection: {res['message']}")

        with ll_col2:
            st.markdown("#### In-Memory C Linked List View")
            # Query directly from C Linked list
            max_c = 100
            out_arr = (CShipment * max_c)()
            out_cnt = ctypes.c_int(0)
            c_bridge.lib.ll_get_all(out_arr, max_c, ctypes.byref(out_cnt))

            ll_data = []
            for i in range(out_cnt.value):
                cs = out_arr[i]
                ll_data.append({
                    "Node": f"Node #{i+1}",
                    "ID": cs.id,
                    "Code": cs.shipment_code.decode("utf-8", errors="ignore"),
                    "Weight (kg)": round(cs.weight, 2),
                    "Volume (m³)": round(cs.volume, 2),
                    "Destination": cs.destination.decode("utf-8", errors="ignore"),
                    "Priority": PRIORITY_MAP.get(cs.priority, cs.priority),
                    "Status": STATUS_MAP.get(cs.status, cs.status)
                })

            if ll_data:
                st.dataframe(pd.DataFrame(ll_data).head(20), use_container_width=True, hide_index=True)
                st.caption(f"Displaying {min(len(ll_data), 20)} of {out_cnt.value} nodes currently resident in C Linked List memory.")
            else:
                st.info("C Linked list is currently empty.")

    # TAB B: Stack
    with tab_stack:
        st.markdown("### C Stack (LIFO) for Processing Audit & Undo History")
        st.info("Every shipment modification (create, status transition, delete) pushes a state snapshot onto the C Stack. Popping retrieves the most recent activity in LIFO order.")

        st_c1, st_c2 = st.columns([1, 2])
        with st_c1:
            st.markdown("#### Stack Controls")
            stack_size = c_bridge.lib.stack_size()
            st.metric("Current Stack Depth", stack_size)

            if st.button("PEEK Top Activity (C Stack Peek)"):
                act_id = ctypes.c_int(0)
                act_name = ctypes.create_string_buffer(64)
                shp_id = ctypes.c_int(0)
                ts = ctypes.c_longlong(0)
                det = ctypes.create_string_buffer(128)
                res = c_bridge.lib.stack_peek(ctypes.byref(act_id), act_name, ctypes.byref(shp_id), ctypes.byref(ts), det)
                if res == 1:
                    st.success(f"Top Activity: [{act_name.value.decode()}] Shipment #{shp_id.value} - {det.value.decode()}")
                else:
                    st.warning("Stack is currently empty.")

            if st.button("POP Top Activity (C Stack Pop)"):
                pop_res = shipment_service.pop_stack_history()
                if pop_res["success"]:
                    st.success(f"Popped: [{pop_res['action']}] Shipment #{pop_res['shipment_id']} - {pop_res['details']}")
                    st.rerun()
                else:
                    st.warning(pop_res["message"])

        with st_c2:
            st.markdown("#### Processing Audit Trail (Recent Database Log)")
            conn = get_db_connection()
            hist_df = pd.read_sql_query("""
                SELECT 
                    datetime(timestamp, 'unixepoch') as Timestamp,
                    action_type as Action,
                    shipment_id as Shipment_ID,
                    details as Details
                FROM processing_history
                ORDER BY id DESC
                LIMIT 10;
            """, conn)
            conn.close()
            st.dataframe(hist_df, use_container_width=True, hide_index=True)

    # TAB C: Queue
    with tab_queue:
        st.markdown("### C FIFO Queue for Incoming Shipment Arrival Order")
        st.info("Incoming shipments enter the FIFO arrival queue and are processed in the strict sequential order of their arrival.")

        q_c1, q_c2 = st.columns([1, 2])
        with q_c1:
            q_size = c_bridge.lib.queue_size()
            st.metric("C Queue Size (Awaiting Dispatch)", q_size)

            if st.button("DEQUEUE Next Shipment (C Queue Dequeue)"):
                out_s = CShipment()
                res = c_bridge.lib.queue_dequeue(ctypes.byref(out_s))
                if res == 1:
                    code = out_s.shipment_code.decode("utf-8", errors="ignore")
                    dest = out_s.destination.decode("utf-8", errors="ignore")
                    st.success(f"Dequeued Next Shipment: {code} destined for {dest} (Weight: {round(out_s.weight, 1)} kg)")
                    st.rerun()
                else:
                    st.warning("FIFO Queue is empty.")

            if st.button("PEEK Front Shipment (C Queue Peek)"):
                out_s = CShipment()
                res = c_bridge.lib.queue_peek(ctypes.byref(out_s))
                if res == 1:
                    code = out_s.shipment_code.decode("utf-8", errors="ignore")
                    st.info(f"Front of Queue: {code} (Priority {out_s.priority})")
                else:
                    st.warning("Queue is empty.")

        with q_c2:
            st.markdown("#### Current C Arrival Queue Buffer")
            q_records = shipment_service.get_queue_records(max_records=15)
            if q_records:
                st.dataframe(pd.DataFrame(q_records), use_container_width=True, hide_index=True)
            else:
                st.info("No incoming shipments currently in FIFO queue.")

    # TAB D: Priority Queue
    with tab_pq:
        st.markdown("### C Priority Queue for Intelligent Urgent Scheduling")
        st.info("Maintained as a Max-Heap in C. Shipments with higher priority (5: Critical, 4: Urgent) are scheduled and extracted ahead of lower-priority cargo regardless of arrival time.")

        pq_c1, pq_c2 = st.columns([1, 2])
        with pq_c1:
            pq_size = c_bridge.lib.pq_size()
            st.metric("Priority Queue Depth", pq_size)

            if st.button("EXTRACT Highest Priority Shipment (C PQ Extract)"):
                out_s = CShipment()
                res = c_bridge.lib.pq_extract_max(ctypes.byref(out_s))
                if res == 1:
                    code = out_s.shipment_code.decode("utf-8", errors="ignore")
                    pri_name = PRIORITY_MAP.get(out_s.priority, out_s.priority)
                    st.success(f"Extracted Highest Priority: {code} [Priority: {pri_name}] destined for {out_s.destination.decode('utf-8', errors='ignore')}")
                    st.rerun()
                else:
                    st.warning("Priority queue is empty.")

        with pq_c2:
            st.markdown("#### Scheduled Priority Queue Buffer (Top Records)")
            pq_records = shipment_service.get_priority_queue_records(max_records=15)
            if pq_records:
                st.dataframe(pd.DataFrame(pq_records), use_container_width=True, hide_index=True)
            else:
                st.info("No pending shipments in Priority Queue.")

    # TAB E: Min-Heap
    with tab_heap:
        st.markdown("### C Min-Heap for Real-Time Deadline Surveillance & Alerts")
        st.info("The root of the C Min-Heap always represents the closest upcoming delivery deadline (minimum timestamp), enabling O(1) deadline inspection and O(log N) alert scheduling.")

        mh_c1, mh_c2 = st.columns([1, 2])
        with mh_c1:
            mh_size = c_bridge.lib.minheap_size()
            st.metric("Active Monitored Deadlines", mh_size)

            if st.button("PEEK Nearest Deadline (C Min-Heap Peek)"):
                out_s = CShipment()
                res = c_bridge.lib.minheap_peek_min(ctypes.byref(out_s))
                if res == 1:
                    code = out_s.shipment_code.decode("utf-8", errors="ignore")
                    now_ts = int(time.time())
                    hrs_rem = round((out_s.deadline_timestamp - now_ts) / 3600.0, 1)
                    st.warning(f"Root of Heap: {code} | {hrs_rem} hours remaining to deadline!")
                else:
                    st.info("Min-heap is empty.")

            if st.button("EXTRACT Imminent Deadline (C Min-Heap Extract)"):
                out_s = CShipment()
                res = c_bridge.lib.minheap_extract_min(ctypes.byref(out_s))
                if res == 1:
                    code = out_s.shipment_code.decode("utf-8", errors="ignore")
                    st.success(f"Extracted nearest deadline shipment {code}.")
                    st.rerun()

        with mh_c2:
            st.markdown("#### Upcoming Deadline Alerts (< 48 Hours)")
            deadlines = shipment_service.get_upcoming_deadlines_c_minheap(hours_threshold=48)
            if deadlines:
                df_deadlines = pd.DataFrame(deadlines)
                st.dataframe(df_deadlines[["shipment_code", "destination", "priority", "hours_left", "is_urgent"]],
                             use_container_width=True, hide_index=True)
            else:
                st.info("No shipments with deadlines in the next 48 hours.")
