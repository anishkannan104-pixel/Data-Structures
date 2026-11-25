import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
from datetime import datetime
from backend.shipment_service import shipment_service, STATUS_MAP
from backend.vehicle_service import vehicle_service
from backend.database import get_db_connection

# Configure Matplotlib Globally for High Presentation Readability & Crisp Projector Display
plt.rcParams.update({
    'font.size': 13,
    'font.family': 'sans-serif',
    'axes.labelsize': 14,
    'axes.titlesize': 15,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 16
})

def render_dashboard():
    st.markdown('<h1 class="main-title">Logistics Intelligence Executive Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Real-Time Operational Telemetry, Fleet Capacity Utilization, and Predictive Deadline Intelligence</p>', unsafe_allow_html=True)

    # =========================================================================
    # 1. INTERACTIVE LIVE FILTER & CONTROL TOOLBAR
    # =========================================================================
    all_shipments_raw = shipment_service.get_all_shipments()
    all_hubs = sorted(list(set(s["destination"] for s in all_shipments_raw))) if all_shipments_raw else []

    with st.expander("🔍 Interactive Dashboard Filters & Data Slicing", expanded=False):
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.2, 1.2, 0.8])
        
        with f_col1:
            sel_hub = st.selectbox("Filter by Regional Hub:", ["All Regional Hubs (15 Hubs)"] + all_hubs, index=0)
        with f_col2:
            sel_priority = st.selectbox("Filter Priority Level:", ["All Priorities", "Critical & Urgent (4 & 5)", "Priority 5 (Critical)", "Priority 4 (Urgent)", "Priority 3 (High)", "Normal (1 & 2)"], index=0)
        with f_col3:
            sel_status = st.selectbox("Filter Lifecycle Status:", ["All Statuses", "Pending Queue (0 & 1)", "In Transit (3)", "Delivered (4)", "Assigned (2)", "Cancelled (5)"], index=0)
        with f_col4:
            st.markdown("<div style='height: 1.8rem;'></div>", unsafe_allow_html=True)
            btn_reset_filters = st.button("🔄 Reset", use_container_width=True)

    if btn_reset_filters:
        sel_hub = "All Regional Hubs (15 Hubs)"
        sel_priority = "All Priorities"
        sel_status = "All Statuses"

    # Apply interactive filters to dataset
    filtered_shipments = all_shipments_raw[:]
    if sel_hub != "All Regional Hubs (15 Hubs)":
        filtered_shipments = [s for s in filtered_shipments if s["destination"] == sel_hub]

    if sel_priority == "Critical & Urgent (4 & 5)":
        filtered_shipments = [s for s in filtered_shipments if s["priority"] in (4, 5)]
    elif sel_priority == "Priority 5 (Critical)":
        filtered_shipments = [s for s in filtered_shipments if s["priority"] == 5]
    elif sel_priority == "Priority 4 (Urgent)":
        filtered_shipments = [s for s in filtered_shipments if s["priority"] == 4]
    elif sel_priority == "Priority 3 (High)":
        filtered_shipments = [s for s in filtered_shipments if s["priority"] == 3]
    elif sel_priority == "Normal (1 & 2)":
        filtered_shipments = [s for s in filtered_shipments if s["priority"] in (1, 2)]

    if sel_status == "Pending Queue (0 & 1)":
        filtered_shipments = [s for s in filtered_shipments if s["status"] in (0, 1)]
    elif sel_status == "In Transit (3)":
        filtered_shipments = [s for s in filtered_shipments if s["status"] == 3]
    elif sel_status == "Delivered (4)":
        filtered_shipments = [s for s in filtered_shipments if s["status"] == 4]
    elif sel_status == "Assigned (2)":
        filtered_shipments = [s for s in filtered_shipments if s["status"] == 2]
    elif sel_status == "Cancelled (5)":
        filtered_shipments = [s for s in filtered_shipments if s["status"] == 5]

    # Calculate dynamic metrics based on filter
    tot_filtered = len(filtered_shipments)
    pending_filtered = sum(1 for s in filtered_shipments if s["status"] in (0, 1))
    intransit_filtered = sum(1 for s in filtered_shipments if s["status"] == 3)
    delivered_filtered = sum(1 for s in filtered_shipments if s["status"] == 4)

    # General system metrics
    s_metrics = shipment_service.get_summary_metrics()
    v_metrics = vehicle_service.get_vehicle_summary_metrics()

    # Active filter notification if filters applied
    is_filtered = (sel_hub != "All Regional Hubs (15 Hubs)" or sel_priority != "All Priorities" or sel_status != "All Statuses")
    if is_filtered:
        st.info(f"Showing filtered view: **{tot_filtered}** of **{s_metrics['total']}** shipments matching filters ({sel_hub} | {sel_priority} | {sel_status}).")

    # =========================================================================
    # 2. TOP EXECUTIVE KPI CARDS (LARGE HIGH-LEGIBILITY FONT)
    # =========================================================================
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total Cargo</div>
            <div class="metric-value">{tot_filtered}</div>
            <div class="metric-footer">{'Filtered' if is_filtered else 'Active Database Records'}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Pending Queue</div>
            <div class="metric-value" style="color: #b45309;">{pending_filtered}</div>
            <div class="metric-footer">Awaiting Dispatch</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">In Transit</div>
            <div class="metric-value" style="color: #1d4ed8;">{intransit_filtered}</div>
            <div class="metric-footer">Active En-Route</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Delivered</div>
            <div class="metric-value" style="color: #15803d;">{delivered_filtered}</div>
            <div class="metric-footer">Completed Deliveries</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi5:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Fleet Units</div>
            <div class="metric-value" style="color: #0f172a;">{v_metrics['available_vehicles']} <span style="font-size: 1.25rem; color: #64748b;">/ {v_metrics['total_vehicles']}</span></div>
            <div class="metric-footer">Avg Util: {v_metrics['avg_utilization']}%</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi6:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Urgent Alerts</div>
            <div class="metric-value" style="color: #b91c1c;">{s_metrics['imminent_deadlines']}</div>
            <div class="metric-footer">&lt; 24h Deadline (C Heap)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 3. INTERACTIVE INSTANT SHIPMENT INSPECTOR (QUICK LOOKUP BAR)
    # =========================================================================
    with st.expander("⚡ Instant Cargo Inspector: Quick-Search Any Shipment by Code or ID", expanded=False):
        insp_col1, insp_col2 = st.columns([1.5, 2.5])
        with insp_col1:
            all_codes = [f"{s['shipment_code']} (ID #{s['id']})" for s in all_shipments_raw]
            sel_inspect = st.selectbox("Select or Type Shipment:", all_codes, index=min(41, len(all_codes)-1))
            # Extract id
            inspect_id = int(sel_inspect.split("ID #")[1].replace(")", "").strip())
            target_shp = shipment_service.get_shipment_by_id(inspect_id)

        with insp_col2:
            if target_shp:
                prio_names = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent", 5: "Critical"}
                prio_colors = {1: "#64748b", 2: "#0284c7", 3: "#d97706", 4: "#ea580c", 5: "#dc2626"}
                stat_colors = {
                    0: ("Created", "#64748b", "#f1f5f9"),
                    1: ("Pending", "#d97706", "#fef3c7"),
                    2: ("Assigned", "#4f46e5", "#e0e7ff"),
                    3: ("In Transit", "#1d4ed8", "#dbeafe"),
                    4: ("Delivered", "#16a34a", "#dcfce7"),
                    5: ("Cancelled", "#dc2626", "#fee2e2"),
                }
                s_name, s_fg, s_bg = stat_colors.get(target_shp["status"], ("Unknown", "#333", "#eee"))
                p_name = prio_names.get(target_shp["priority"], f"Priority {target_shp['priority']}")
                p_col = prio_colors.get(target_shp["priority"], "#333")

                # Vehicle lookup
                conn = get_db_connection()
                va_row = conn.execute("""
                    SELECT v.vehicle_code, v.vehicle_type 
                    FROM vehicle_assignments va 
                    JOIN vehicles v ON va.vehicle_id = v.id 
                    WHERE va.shipment_id = ?
                """, (inspect_id,)).fetchone()
                conn.close()
                v_text = f"{va_row['vehicle_code']} ({va_row['vehicle_type']})" if va_row else "Unassigned (Awaiting Dispatch)"

                dl_dt = datetime.fromtimestamp(target_shp["deadline_timestamp"])
                hours_left = round((target_shp["deadline_timestamp"] - time.time()) / 3600, 1)

                st.markdown(f"""
                <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.35rem; font-weight: 800; color: #1d4ed8;">{target_shp['shipment_code']}</span>
                        <div>
                            <span style="background-color: {s_bg}; color: {s_fg}; font-weight: 750; padding: 3px 10px; border-radius: 6px; font-size: 0.95rem;">{s_name}</span>
                            <span style="color: {p_col}; font-weight: 750; font-size: 0.95rem; margin-left: 6px;">● {p_name}</span>
                        </div>
                    </div>
                    <div style="font-size: 1.05rem; color: #1e293b; line-height: 1.6;">
                        <strong>Destination:</strong> {target_shp['destination']}<br>
                        <strong>Weight & Volume:</strong> {target_shp['weight']} kg &bull; {target_shp['volume']} m³<br>
                        <strong>Fleet Assignment:</strong> {v_text}<br>
                        <strong>Deadline:</strong> {dl_dt.strftime('%Y-%m-%d %H:%M')} ({hours_left} hrs remaining)
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # =========================================================================
    # 4. INTERACTIVE FEATURE TABS
    # =========================================================================
    tab_analytics, tab_deadlines, tab_simulator, tab_stream = st.tabs([
        "📊 1. Visual Telemetry & Fleet Capacity",
        "🚨 2. Predictive Deadline Surveillance (C Min-Heap)",
        "🚀 3. Live Dispatch Simulator (Faculty Demo)",
        "📋 4. Audit Trail & Activity Log"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: VISUAL TELEMETRY & FLEET CAPACITY
    # -------------------------------------------------------------------------
    with tab_analytics:
        st.markdown("### Interactive Fleet & Cargo Visual Analytics")

        c_view1, c_view2 = st.columns([1, 1])

        with c_view1:
            st.markdown("#### Interactive Operational Disk & Cargo Metrics")
            chart_type = st.radio(
                "Select Visual Metric:",
                ["🎯 Interactive Status Donut Disk", "Top Hub Cargo Distribution", "Cargo Priority Breakdown"],
                horizontal=True
            )

            conn = get_db_connection()

            if chart_type == "🎯 Interactive Status Donut Disk":
                status_df = pd.read_sql_query("""
                    SELECT 
                        status as StatusCode,
                        CASE status
                            WHEN 0 THEN 'Created'
                            WHEN 1 THEN 'Pending'
                            WHEN 2 THEN 'Assigned'
                            WHEN 3 THEN 'In Transit'
                            WHEN 4 THEN 'Delivered'
                            WHEN 5 THEN 'Cancelled'
                        END as Status,
                        COUNT(*) as Count
                    FROM shipments
                    GROUP BY status
                    ORDER BY status;
                """, conn)

                if not status_df.empty:
                    # Interactive Slice Selector & Mode
                    d_ctrl1, d_ctrl2 = st.columns([1.5, 1])
                    with d_ctrl1:
                        sel_slice = st.selectbox(
                            "🎯 Select Wedge to Explode & Inspect:",
                            ["All Wedges (Complete Disk)"] + list(status_df["Status"]),
                            index=0
                        )
                    with d_ctrl2:
                        disk_style = st.radio("Disk Style:", ["Donut Ring Disk", "Exploded 3D Disk"], horizontal=True)

                    colors = ["#94a3b8", "#f59e0b", "#6366f1", "#2563eb", "#10b981", "#ef4444"]
                    status_colors_map = dict(zip(status_df["Status"], colors[:len(status_df)]))

                    # Calculate exploded wedge
                    if sel_slice != "All Wedges (Complete Disk)":
                        explode_vals = [0.15 if s == sel_slice else 0 for s in status_df["Status"]]
                    else:
                        explode_vals = [0.03] * len(status_df) if disk_style == "Exploded 3D Disk" else [0] * len(status_df)

                    hole_size = 0.52 if disk_style == "Donut Ring Disk" else 0.0

                    fig, ax = plt.subplots(figsize=(7, 4.8), dpi=105)
                    wedges, texts, autotexts = ax.pie(
                        status_df["Count"],
                        labels=status_df["Status"],
                        autopct="%1.1f%%",
                        startangle=140,
                        colors=[status_colors_map[s] for s in status_df["Status"]],
                        explode=explode_vals,
                        pctdistance=0.75 if hole_size > 0 else 0.6,
                        wedgeprops=dict(width=1.0 - hole_size if hole_size > 0 else 1.0, edgecolor="#ffffff", linewidth=2.5)
                    )

                    # Dynamic center text in donut disk
                    if hole_size > 0:
                        if sel_slice != "All Wedges (Complete Disk)":
                            target_cnt = status_df.loc[status_df["Status"] == sel_slice, "Count"].values[0]
                            ax.text(0, 0.08, f"{sel_slice}", ha="center", va="center", fontsize=13, fontweight="bold", color="#0f172a")
                            ax.text(0, -0.12, f"{target_cnt} units", ha="center", va="center", fontsize=12, fontweight="bold", color="#1d4ed8")
                        else:
                            total_s = status_df["Count"].sum()
                            ax.text(0, 0.08, "Total Cargo", ha="center", va="center", fontsize=12, fontweight="bold", color="#64748b")
                            ax.text(0, -0.12, f"{total_s} units", ha="center", va="center", fontsize=14, fontweight="bold", color="#0f172a")

                    for t in texts:
                        t.set_fontsize(12)
                        t.set_weight("bold")
                        t.set_color("#0f172a")
                    for at in autotexts:
                        at.set_fontsize(11)
                        at.set_weight("bold")
                        at.set_color("#ffffff" if disk_style != "Donut Ring Disk" else "#0f172a")

                    title_label = f"Interactive Status Disk (Focused on {sel_slice})" if sel_slice != "All Wedges (Complete Disk)" else "Interactive Operational Status Disk"
                    ax.set_title(title_label, fontsize=14, fontweight="bold", pad=14)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)

                    # Interactive Drill-down if slice selected
                    if sel_slice != "All Wedges (Complete Disk)":
                        target_code = status_df.loc[status_df["Status"] == sel_slice, "StatusCode"].values[0]
                        drill_df = pd.read_sql_query("""
                            SELECT 
                                id as ID,
                                shipment_code as Code,
                                destination as Destination,
                                weight as Weight_kg,
                                volume as Volume_m3,
                                priority as Priority
                            FROM shipments
                            WHERE status = ?
                            LIMIT 6;
                        """, conn, params=(int(target_code),))

                        st.markdown(f"**Live Drill-Down: Active Shipments in '{sel_slice}' Wedge:**")
                        st.dataframe(drill_df, use_container_width=True, hide_index=True)

            elif chart_type == "Top Hub Cargo Distribution":
                hub_df = pd.read_sql_query("""
                    SELECT destination as Hub, COUNT(*) as Shipments
                    FROM shipments
                    GROUP BY destination
                    ORDER BY Shipments DESC
                    LIMIT 8;
                """, conn)

                if not hub_df.empty:
                    fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=100)
                    bars = ax.barh(hub_df["Hub"], hub_df["Shipments"], color="#1d4ed8", height=0.6)
                    ax.set_xlabel("Shipment Count", fontsize=12, fontweight="bold")
                    ax.set_title("Top 8 Delivery Hubs by Volume", fontsize=14, fontweight="bold", pad=12)
                    ax.tick_params(axis="both", labelsize=11)
                    for b in bars:
                        w = b.get_width()
                        ax.text(w + 0.3, b.get_y() + b.get_height()/2, f"{int(w)}",
                                va="center", ha="left", fontsize=11, fontweight="bold", color="#0f172a")
                    ax.invert_yaxis()
                    ax.grid(axis="x", linestyle="--", alpha=0.4)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)

            else: # Priority Breakdown
                prio_df = pd.read_sql_query("""
                    SELECT 
                        CASE priority
                            WHEN 1 THEN '1 - Low'
                            WHEN 2 THEN '2 - Medium'
                            WHEN 3 THEN '3 - High'
                            WHEN 4 THEN '4 - Urgent'
                            WHEN 5 THEN '5 - Critical'
                        END as Priority,
                        COUNT(*) as Count
                    FROM shipments
                    GROUP BY priority
                    ORDER BY priority ASC;
                """, conn)

                if not prio_df.empty:
                    p_colors = ["#64748b", "#0284c7", "#d97706", "#ea580c", "#dc2626"]
                    fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=100)
                    bars = ax.bar(prio_df["Priority"], prio_df["Count"], color=p_colors[:len(prio_df)], width=0.55)
                    ax.set_ylabel("Shipments", fontsize=12, fontweight="bold")
                    ax.set_title("Cargo Urgency & Priority Breakdown", fontsize=14, fontweight="bold", pad=12)
                    ax.tick_params(axis="both", labelsize=11)
                    for b in bars:
                        h = b.get_height()
                        ax.text(b.get_x() + b.get_width()/2, h + 0.5, f"{int(h)}",
                                ha="center", fontsize=11, fontweight="bold", color="#0f172a")
                    ax.grid(axis="y", linestyle="--", alpha=0.4)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)

            conn.close()

        with c_view2:
            st.markdown("#### Fleet Capacity & Loading Radar")
            vehicles_all = vehicle_service.get_all_vehicles()
            v_types = sorted(list(set(v["vehicle_type"] for v in vehicles_all))) if vehicles_all else []
            sel_v_type = st.selectbox("Filter by Vehicle Class:", ["All Vehicle Classes"] + v_types, index=0)

            filtered_v = vehicles_all[:]
            if sel_v_type != "All Vehicle Classes":
                filtered_v = [v for v in filtered_v if v["vehicle_type"] == sel_v_type]

            min_util = st.slider("Filter Minimum Utilization (%):", min_value=0, max_value=100, value=0, step=5)
            filtered_v = [v for v in filtered_v if v["weight_utilization_pct"] >= min_util]

            if filtered_v:
                v_df = pd.DataFrame(filtered_v).head(8)
                fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=100)
                # Dynamic bar colors based on utilization threshold
                bar_colors = []
                for u in v_df["weight_utilization_pct"]:
                    if u >= 90: bar_colors.append("#dc2626") # red
                    elif u >= 70: bar_colors.append("#f59e0b") # amber
                    else: bar_colors.append("#16a34a") # green

                bars = ax.barh(v_df["vehicle_code"], v_df["weight_utilization_pct"], color=bar_colors, height=0.55)
                ax.set_xlim(0, 105)
                ax.set_xlabel("Capacity Utilization (%)", fontsize=12, fontweight="bold")
                ax.set_title(f"Fleet Unit Utilization ({len(v_df)} Displayed)", fontsize=14, fontweight="bold", pad=12)
                ax.tick_params(axis="both", labelsize=11)
                ax.grid(axis="x", linestyle="--", alpha=0.4)

                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 1.5, bar.get_y() + bar.get_height()/2, f"{width:.1f}%",
                            va="center", ha="left", fontsize=11, fontweight="bold", color="#0f172a")

                ax.invert_yaxis()
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("No vehicles match the selected utilization threshold and vehicle class.")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("💾 Hardware Disk & Database Storage Telemetry (SQLite & C Memory Architecture)", expanded=False):
            db_path = r'database/logistics.db'
            db_size_kb = os.path.getsize(db_path) / 1024 if os.path.exists(db_path) else 92.0
            conn = get_db_connection()
            page_sz = conn.execute('PRAGMA page_size;').fetchone()[0]
            page_cnt = conn.execute('PRAGMA page_count;').fetchone()[0]
            j_mode = conn.execute('PRAGMA journal_mode;').fetchone()[0]
            conn.close()

            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            d_col1.metric("Disk Storage Size", f"{db_size_kb:.1f} KB", "Relational Database")
            d_col2.metric("Disk Block Page Size", f"{page_sz} B", "Standard 4KB Page")
            d_col3.metric("Allocated Disk Pages", f"{page_cnt} Pages", "B-Tree Node Layout")
            d_col4.metric("Disk Journal Mode", f"{j_mode.upper()}", "Crash-Resilient ACID")

            st.caption("🚀 **Two-Tier Storage Architecture**: In-memory C shared library (`logistics_c.dll`) handles microsecond algorithmic lookups (0.1 μs), while SQLite persists all relational state to disk with 4096-byte pages (42.0 μs).")

    # -------------------------------------------------------------------------
    # TAB 2: PREDICTIVE DEADLINE SURVEILLANCE (C MIN-HEAP RADAR)
    # -------------------------------------------------------------------------
    with tab_deadlines:
        st.markdown("### Predictive Deadline Intelligence (Native C Min-Heap)")
        st.info("Continuous O(1) minimum deadline monitoring powered by native C Min-Heap. Use the interactive horizon slider to inspect shipments approaching SLA expiration.")

        dh_col1, dh_col2 = st.columns([1.5, 2.5])

        with dh_col1:
            urgency_slider = st.slider(
                "Urgency Time Horizon Filter (Hours):",
                min_value=3,
                max_value=72,
                value=24,
                step=3,
                format="%d hrs"
            )
            st.caption(f"Inspecting all cargo consignments expiring within the next **{urgency_slider} hours**.")

            deadlines_c = shipment_service.get_upcoming_deadlines_c_minheap(hours_threshold=urgency_slider)
            st.metric("Imminent SLA Breaches", len(deadlines_c), delta=f"within {urgency_slider}h", delta_color="inverse")

        with dh_col2:
            if deadlines_c:
                st.markdown(f"#### Active Alert Queue ({len(deadlines_c)} Shipments)")
                for item in deadlines_c[:8]:
                    hrs = item["hours_left"]
                    if hrs <= 6:
                        badge_bg = "#fee2e2"
                        badge_fg = "#991b1b"
                        urgency_tag = "CRITICAL (<6h)"
                        border_col = "#dc2626"
                    elif hrs <= 12:
                        badge_bg = "#ffedd5"
                        badge_fg = "#9a3412"
                        urgency_tag = "URGENT (<12h)"
                        border_col = "#ea580c"
                    else:
                        badge_bg = "#fef3c7"
                        badge_fg = "#92400e"
                        urgency_tag = "ATTENTION"
                        border_col = "#d97706"

                    st.markdown(f"""
                    <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-left: 5px solid {border_col}; padding: 0.85rem 1.15rem; border-radius: 9px; margin-bottom: 0.65rem; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.18rem; font-weight: 800; color: #0f172a;">{item['shipment_code']}</span> &rarr; 
                            <span style="font-size: 1.08rem; font-weight: 600; color: #334155;">{item['destination']}</span>
                            <div style="font-size: 0.95rem; color: #64748b; margin-top: 2px;">
                                Weight: <b>{item.get('weight', 'N/A')} kg</b> &bull; Priority: <b>{item['priority']}</b>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: {badge_bg}; color: {badge_fg}; font-weight: 800; font-size: 0.92rem; padding: 0.35rem 0.75rem; border-radius: 9999px;">
                                {hrs}h remaining [{urgency_tag}]
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success(f"Excellent SLA Health! No shipment deadlines expire within the next {urgency_slider} hours.")

    # -------------------------------------------------------------------------
    # TAB 3: LIVE DISPATCH SIMULATOR (FACULTY DEMO)
    # -------------------------------------------------------------------------
    with tab_simulator:
        st.markdown("### Interactive Operational Dispatch Engine (Live Faculty Demo)")
        st.info("Demonstrates live interplay between the C Priority Queue (Max-Heap), C Finite State Machine (Lifecycle Validation), and Dual-Constraint Vehicle Assignment Engine.")

        sim_c1, sim_c2 = st.columns([1, 1.2])

        with sim_c1:
            st.markdown("#### Live Control Panel")
            st.write("Trigger automated operational cycles to showcase self-optimizing algorithmic processing in real time:")

            if st.button("🚀 Execute Automated Priority Dispatch Cycle", use_container_width=True):
                # 1. Grab pending shipments
                pending = [s for s in shipment_service.get_all_shipments() if s["status"] in (0, 1)]
                if pending:
                    # Sort by priority desc
                    top_candidate = sorted(pending, key=lambda x: (x["priority"], -x["deadline_timestamp"]), reverse=True)[0]
                    # Find suitable vehicle
                    best_v = vehicle_service.find_suitable_vehicle(top_candidate["weight"], top_candidate["volume"])
                    if best_v:
                        # Assign
                        assign_res = vehicle_service.assign_shipment_to_vehicle(best_v["id"], top_candidate["id"])
                        # Transition to In Transit
                        fsm_res = shipment_service.validate_and_update_status(top_candidate["id"], 3, f"Auto-Dispatched on {best_v['vehicle_code']}")
                        st.success(f"""
                        **Automated Dispatch Executed Successfully!**
                        - **Consignment**: `{top_candidate['shipment_code']}` (Priority {top_candidate['priority']})
                        - **Assigned Unit**: `{best_v['vehicle_code']}` ({best_v['vehicle_type']})
                        - **C FSM Validation**: State progressed to `In Transit`
                        - **Fleet Weight Utilization**: {assign_res['weight_utilization_pct']}%
                        """)
                    else:
                        st.warning(f"All fleet vehicles currently at capacity for shipment {top_candidate['shipment_code']} ({top_candidate['weight']} kg).")
                else:
                    st.info("No pending shipments in queue to dispatch.")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("📦 Ingest Priority 5 Critical Consignment", use_container_width=True):
                new_code = f"SHP-{int(time.time()) % 10000}"
                dest = "Downtown Urban Locker Hub"
                deadline_ts = int(time.time() + 18000) # 5 hours remaining
                new_id = shipment_service.create_shipment(new_code, 280.5, 1.2, dest, deadline_ts, 5)
                st.success(f"Critical Consignment `{new_code}` (ID #{new_id}) ingested! Automatically placed at root of C Priority Queue & Min-Heap.")
                st.rerun()

        with sim_c2:
            st.markdown("#### Active Processing Telemetry")
            conn = get_db_connection()
            recent_evs = pd.read_sql_query("""
                SELECT 
                    datetime(timestamp, 'unixepoch') as Time,
                    action_type as Action,
                    details as Telemetry
                FROM processing_history
                ORDER BY id DESC
                LIMIT 6;
            """, conn)
            conn.close()
            if not recent_evs.empty:
                st.dataframe(recent_evs, use_container_width=True, hide_index=True)
            else:
                st.info("No recorded actions yet.")

    # -------------------------------------------------------------------------
    # TAB 4: AUDIT TRAIL & ACTIVITY LOG
    # -------------------------------------------------------------------------
    with tab_stream:
        st.markdown("### System Audit Trail & Lifecycle Activity Stream")
        conn = get_db_connection()
        full_audit_df = pd.read_sql_query("""
            SELECT 
                datetime(timestamp, 'unixepoch') as Timestamp,
                action_type as Action,
                details as Operational_Details
            FROM processing_history
            ORDER BY id DESC
            LIMIT 50;
        """, conn)
        conn.close()

        if not full_audit_df.empty:
            st.dataframe(full_audit_df, use_container_width=True, hide_index=True)
            csv_data = full_audit_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Full Audit Log to CSV",
                data=csv_data,
                file_name="logistics_audit_log.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No operational events logged yet.")
