import streamlit as st
import pandas as pd
from backend.database import get_db_connection

def render_reports():
    st.markdown('<h1 class="main-title">Intelligence Reports & Data Export Center</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Audit Trail Aggregation, Operational Verification, and One-Click CSV Export Powered by Pandas</p>', unsafe_allow_html=True)

    report_type = st.selectbox(
        "Select Report Category:",
        [
            "1. Comprehensive Shipments Ledger",
            "2. Fleet Capacity & Vehicle Assignments",
            "3. Delivery Deadlines Surveillance",
            "4. Road Network Topology & Connections",
            "5. Algorithm Performance Benchmark Audit",
            "6. Shipment Status History Audit Trail"
        ]
    )

    conn = get_db_connection()

    if report_type.startswith("1."):
        st.markdown("### Master Shipments Ledger")
        df = pd.read_sql_query("""
            SELECT 
                id,
                shipment_code as Code,
                weight as Weight_kg,
                volume as Volume_m3,
                destination as Destination,
                datetime(deadline_timestamp, 'unixepoch') as Deadline,
                CASE priority
                    WHEN 1 THEN '1 - Low'
                    WHEN 2 THEN '2 - Medium'
                    WHEN 3 THEN '3 - High'
                    WHEN 4 THEN '4 - Urgent'
                    WHEN 5 THEN '5 - Critical'
                END as Priority,
                CASE status
                    WHEN 0 THEN 'Created'
                    WHEN 1 THEN 'Pending'
                    WHEN 2 THEN 'Assigned'
                    WHEN 3 THEN 'In Transit'
                    WHEN 4 THEN 'Delivered'
                    WHEN 5 THEN 'Cancelled'
                END as Status,
                created_at as Created_At,
                updated_at as Updated_At
            FROM shipments
            ORDER BY id ASC;
        """, conn)

        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Shipments CSV Report", data=csv, file_name="shipments_master_report.csv", mime="text/csv")

    elif report_type.startswith("2."):
        st.markdown("### Fleet Vehicle Capacity & Assignment Manifest")
        df_v = pd.read_sql_query("""
            SELECT 
                v.id,
                v.vehicle_code as Code,
                v.vehicle_type as Type,
                v.max_weight as Max_Weight_kg,
                v.current_weight as Assigned_Weight_kg,
                ROUND(v.max_weight - v.current_weight, 2) as Remaining_Weight_kg,
                ROUND((v.current_weight / v.max_weight) * 100.0, 1) as Weight_Util_Pct,
                v.max_volume as Max_Volume_m3,
                v.current_volume as Assigned_Volume_m3,
                ROUND(v.max_volume - v.current_volume, 2) as Remaining_Volume_m3,
                CASE v.is_available WHEN 1 THEN 'Available' ELSE 'Inactive' END as Availability
            FROM vehicles v
            ORDER BY v.id ASC;
        """, conn)

        st.dataframe(df_v, use_container_width=True, hide_index=True)
        csv_v = df_v.to_csv(index=False).encode("utf-8")
        st.download_button("Download Fleet Vehicles CSV Report", data=csv_v, file_name="fleet_capacity_report.csv", mime="text/csv")

        st.markdown("#### Active Shipment Assignments to Vehicles")
        df_va = pd.read_sql_query("""
            SELECT 
                va.id as Assignment_ID,
                v.vehicle_code as Vehicle,
                v.vehicle_type as Vehicle_Type,
                s.shipment_code as Shipment,
                s.weight as Weight_kg,
                s.destination as Destination,
                va.assigned_at as Assigned_At,
                va.status as Status
            FROM vehicle_assignments va
            JOIN vehicles v ON va.vehicle_id = v.id
            JOIN shipments s ON va.shipment_id = s.id
            ORDER BY va.id DESC;
        """, conn)
        st.dataframe(df_va, use_container_width=True, hide_index=True)
        csv_va = df_va.to_csv(index=False).encode("utf-8")
        st.download_button("Download Vehicle Assignments CSV Report", data=csv_va, file_name="active_assignments_report.csv", mime="text/csv")

    elif report_type.startswith("3."):
        st.markdown("### Delivery Deadlines & Urgency Surveillance")
        df_d = pd.read_sql_query("""
            SELECT 
                id,
                shipment_code as Code,
                destination as Destination,
                weight as Weight_kg,
                datetime(deadline_timestamp, 'unixepoch') as Deadline,
                ROUND((deadline_timestamp - strftime('%s', 'now')) / 3600.0, 1) as Hours_Remaining,
                CASE priority
                    WHEN 1 THEN 'Low'
                    WHEN 2 THEN 'Medium'
                    WHEN 3 THEN 'High'
                    WHEN 4 THEN 'Urgent'
                    WHEN 5 THEN 'Critical'
                END as Priority,
                CASE status
                    WHEN 0 THEN 'Created'
                    WHEN 1 THEN 'Pending'
                    WHEN 2 THEN 'Assigned'
                    WHEN 3 THEN 'In Transit'
                    WHEN 4 THEN 'Delivered'
                    WHEN 5 THEN 'Cancelled'
                END as Status
            FROM shipments
            WHERE status NOT IN (4, 5)
            ORDER BY deadline_timestamp ASC;
        """, conn)

        st.dataframe(df_d, use_container_width=True, hide_index=True)
        csv_d = df_d.to_csv(index=False).encode("utf-8")
        st.download_button("Download Deadlines CSV Report", data=csv_d, file_name="deadlines_surveillance_report.csv", mime="text/csv")

    elif report_type.startswith("4."):
        st.markdown("### Road Network Topology Ledger")
        df_r = pd.read_sql_query("""
            SELECT 
                r.id as Road_ID,
                l1.name as Origin_Hub,
                l1.code as Origin_Code,
                l2.name as Destination_Hub,
                l2.code as Destination_Code,
                r.distance_km as Distance_km,
                CASE r.is_active WHEN 1 THEN 'Active' ELSE 'Disabled / Closed' END as Road_Status
            FROM roads r
            JOIN locations l1 ON r.source_id = l1.id
            JOIN locations l2 ON r.dest_id = l2.id
            ORDER BY r.id ASC;
        """, conn)

        st.dataframe(df_r, use_container_width=True, hide_index=True)
        csv_r = df_r.to_csv(index=False).encode("utf-8")
        st.download_button("Download Roads Topology CSV Report", data=csv_r, file_name="roads_network_report.csv", mime="text/csv")

    elif report_type.startswith("5."):
        st.markdown("### Algorithm Performance Benchmark Audit Log")
        df_p = pd.read_sql_query("""
            SELECT 
                id,
                recorded_at as Recorded_At,
                category as Category,
                algorithm_name as Algorithm,
                input_size as Input_Scale_N,
                execution_time_us as Execution_Time_us,
                comparisons as Comparisons,
                operations as Operations
            FROM algorithm_performance
            ORDER BY id DESC;
        """, conn)

        st.dataframe(df_p, use_container_width=True, hide_index=True)
        csv_p = df_p.to_csv(index=False).encode("utf-8")
        st.download_button("Download Benchmarks CSV Report", data=csv_p, file_name="algorithm_performance_report.csv", mime="text/csv")

    elif report_type.startswith("6."):
        st.markdown("### Shipment Status Lifecycle Audit Trail")
        df_h = pd.read_sql_query("""
            SELECT 
                h.id,
                s.shipment_code as Shipment_Code,
                CASE h.from_status
                    WHEN 0 THEN 'Created' WHEN 1 THEN 'Pending' WHEN 2 THEN 'Assigned'
                    WHEN 3 THEN 'In Transit' WHEN 4 THEN 'Delivered' WHEN 5 THEN 'Cancelled'
                END as From_Status,
                CASE h.to_status
                    WHEN 0 THEN 'Created' WHEN 1 THEN 'Pending' WHEN 2 THEN 'Assigned'
                    WHEN 3 THEN 'In Transit' WHEN 4 THEN 'Delivered' WHEN 5 THEN 'Cancelled'
                END as To_Status,
                h.changed_at as Changed_At,
                h.notes as Notes
            FROM shipment_status_history h
            JOIN shipments s ON h.shipment_id = s.id
            ORDER BY h.id DESC;
        """, conn)

        st.dataframe(df_h, use_container_width=True, hide_index=True)
        csv_h = df_h.to_csv(index=False).encode("utf-8")
        st.download_button("Download Status History CSV Report", data=csv_h, file_name="status_history_report.csv", mime="text/csv")

    conn.close()
