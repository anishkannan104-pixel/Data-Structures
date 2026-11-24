import sqlite3
import os
import time
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "database", "logistics.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Shipments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_code TEXT UNIQUE NOT NULL,
        weight REAL NOT NULL,
        volume REAL NOT NULL,
        destination TEXT NOT NULL,
        deadline_timestamp INTEGER NOT NULL,
        priority INTEGER NOT NULL,
        status INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 2. Vehicles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_code TEXT UNIQUE NOT NULL,
        vehicle_type TEXT NOT NULL,
        max_weight REAL NOT NULL,
        max_volume REAL NOT NULL,
        current_weight REAL NOT NULL DEFAULT 0.0,
        current_volume REAL NOT NULL DEFAULT 0.0,
        is_available INTEGER NOT NULL DEFAULT 1
    );
    """)

    # 3. Locations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        x_coord REAL NOT NULL,
        y_coord REAL NOT NULL,
        description TEXT
    );
    """)

    # 4. Roads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        dest_id INTEGER NOT NULL,
        distance_km REAL NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (source_id) REFERENCES locations(id) ON DELETE CASCADE,
        FOREIGN KEY (dest_id) REFERENCES locations(id) ON DELETE CASCADE
    );
    """)

    # 5. Vehicle Assignments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        shipment_id INTEGER NOT NULL,
        assigned_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
        FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE
    );
    """)

    # 6. Shipment Status History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipment_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER NOT NULL,
        from_status INTEGER NOT NULL,
        to_status INTEGER NOT NULL,
        changed_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE
    );
    """)

    # 7. Processing History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processing_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        shipment_id INTEGER,
        details TEXT,
        timestamp INTEGER NOT NULL
    );
    """)

    # 8. Algorithm Performance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS algorithm_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        algorithm_name TEXT NOT NULL,
        category TEXT NOT NULL,
        input_size INTEGER NOT NULL,
        execution_time_us REAL NOT NULL,
        comparisons INTEGER NOT NULL,
        operations INTEGER NOT NULL,
        recorded_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def seed_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM shipments;")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    now = datetime.now()
    now_ts = int(time.time())

    # 1. Seed Locations (16 logistics hubs with 2D coordinate map)
    locations_data = [
        (0, "Central Distribution Center", "HUB-CEN", 50.0, 50.0, "Main Regional Logistics Apex"),
        (1, "North Metro Depot", "DEP-NTH", 52.0, 78.0, "Northern Consumer Fulfillment"),
        (2, "South Freight Terminal", "TRM-STH", 48.0, 22.0, "Heavy Cargo Freight Intermodal"),
        (3, "East Industrial Park", "IND-EST", 82.0, 55.0, "Automotive & Heavy Industry Hub"),
        (4, "West Port Gateway", "PRT-WST", 18.0, 48.0, "Maritime Container Port Terminal"),
        (5, "Northwest Transit Hub", "NWT-HUB", 25.0, 75.0, "Interstate Interchange Facility"),
        (6, "Northeast Cargo Airport", "AIR-NET", 78.0, 78.0, "Air Express Freight Depot"),
        (7, "Southeast Express Hub", "SE-EXP", 80.0, 25.0, "Suburban Parcel Delivery Station"),
        (8, "Southwest Railway Logistics", "SW-RAIL", 22.0, 25.0, "Rail-to-Road Cargo Exchange"),
        (9, "Downtown Urban Locker Hub", "DTN-LCK", 52.0, 58.0, "Last-Mile Urban Micro-Depot"),
        (10, "Metro Tech Park Station", "TEC-STN", 65.0, 62.0, "High-Value Electronics Depot"),
        (11, "Aerospace Logistics Park", "AER-LOG", 35.0, 65.0, "Precision Handling & Avionics"),
        (12, "Pharmaceutical Cold Hub", "PHM-CLD", 62.0, 38.0, "Temperature Controlled Pharma Hub"),
        (13, "Automated Fulfillment Unit", "AUT-FUL", 38.0, 35.0, "Robotic Sortation Center"),
        (14, "Riverport Barge Terminal", "RIV-BRG", 70.0, 45.0, "Bulk Riverway Logistics Pier"),
        (15, "Outer Ring Consolidation", "OUT-RNG", 50.0, 92.0, "Long-Haul Staging Cross-Dock")
    ]

    cursor.executemany("""
    INSERT INTO locations (id, name, code, x_coord, y_coord, description)
    VALUES (?, ?, ?, ?, ?, ?);
    """, locations_data)

    # 2. Seed Roads (32 connected roads with realistic distances)
    roads_data = [
        (0, 1, 28.5), (0, 2, 28.0), (0, 3, 32.5), (0, 4, 32.0),
        (0, 9, 8.2),  (0, 10, 19.5), (0, 12, 16.8), (0, 13, 19.2),
        (1, 5, 27.2), (1, 6, 26.0), (1, 9, 20.1), (1, 15, 14.2),
        (2, 7, 32.2), (2, 8, 26.2), (2, 12, 21.4), (2, 13, 16.5),
        (3, 6, 23.5), (3, 7, 30.1), (3, 10, 18.4), (3, 14, 15.6),
        (4, 5, 27.8), (4, 8, 23.4), (4, 11, 24.1), (4, 13, 23.8),
        (5, 11, 14.1), (5, 15, 30.4), (6, 10, 20.6), (6, 15, 31.2),
        (7, 12, 22.8), (7, 14, 22.4), (8, 13, 18.9), (9, 10, 13.6),
        (10, 14, 17.7), (11, 13, 30.1), (12, 14, 10.5), (13, 12, 24.2)
    ]

    for u, v, dist in roads_data:
        cursor.execute("""
        INSERT INTO roads (source_id, dest_id, distance_km, is_active)
        VALUES (?, ?, ?, 1);
        """, (u, v, dist))

    # 3. Seed Vehicles (16 vehicles with varied capacities)
    vehicles_data = [
        ("V-101", "Electric Van", 800.0, 6.5, 0.0, 0.0, 1),
        ("V-102", "Electric Van", 800.0, 6.5, 0.0, 0.0, 1),
        ("V-103", "Urban Cargo Sprinter", 1500.0, 12.0, 0.0, 0.0, 1),
        ("V-104", "Urban Cargo Sprinter", 1500.0, 12.0, 0.0, 0.0, 1),
        ("V-105", "Refrigerated Medium Truck", 3500.0, 22.0, 0.0, 0.0, 1),
        ("V-106", "Refrigerated Medium Truck", 3500.0, 22.0, 0.0, 0.0, 1),
        ("V-107", "Heavy Duty Box Truck", 7500.0, 40.0, 0.0, 0.0, 1),
        ("V-108", "Heavy Duty Box Truck", 7500.0, 40.0, 0.0, 0.0, 1),
        ("V-109", "Semi-Trailer Hauler", 18000.0, 85.0, 0.0, 0.0, 1),
        ("V-110", "Semi-Trailer Hauler", 18000.0, 85.0, 0.0, 0.0, 1),
        ("V-111", "Autonomous EV Shuttler", 1200.0, 9.0, 0.0, 0.0, 1),
        ("V-112", "Autonomous EV Shuttler", 1200.0, 9.0, 0.0, 0.0, 1),
        ("V-113", "Flatbed Machinery Transporter", 12000.0, 50.0, 0.0, 0.0, 1),
        ("V-114", "Express Courier Cruiser", 600.0, 4.5, 0.0, 0.0, 1),
        ("V-115", "Heavy Intercity Rig", 24000.0, 110.0, 0.0, 0.0, 1),
        ("V-116", "Heavy Intercity Rig", 24000.0, 110.0, 0.0, 0.0, 1)
    ]

    cursor.executemany("""
    INSERT INTO vehicles (vehicle_code, vehicle_type, max_weight, max_volume, current_weight, current_volume, is_available)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, vehicles_data)

    # 4. Seed 110 Shipments with realistic values and deadlines
    # Priority: 1=Low, 2=Medium, 3=High, 4=Urgent, 5=Critical
    # Status: 0=Created, 1=Pending, 2=Assigned, 3=In Transit, 4=Delivered, 5=Cancelled
    destinations = [
        "North Metro Depot", "South Freight Terminal", "East Industrial Park",
        "West Port Gateway", "Northwest Transit Hub", "Northeast Cargo Airport",
        "Southeast Express Hub", "Southwest Railway Logistics", "Downtown Urban Locker Hub",
        "Metro Tech Park Station", "Aerospace Logistics Park", "Pharmaceutical Cold Hub",
        "Automated Fulfillment Unit", "Riverport Barge Terminal", "Outer Ring Consolidation"
    ]

    import random
    random.seed(42)

    for i in range(1, 111):
        shipment_code = f"SHP-{1000 + i}"
        dest = destinations[(i - 1) % len(destinations)]
        weight = round(random.uniform(15.0, 650.0), 2)
        volume = round(random.uniform(0.1, 4.2), 2)

        # Priority distribution: some low, medium, high, urgent, critical
        r_p = random.random()
        if r_p < 0.20:
            priority = 1 # Low
        elif r_p < 0.50:
            priority = 2 # Medium
        elif r_p < 0.75:
            priority = 3 # High
        elif r_p < 0.90:
            priority = 4 # Urgent
        else:
            priority = 5 # Critical

        # Deadlines: some imminent (< 12 hours), some normal (1-3 days), some distant (4-7 days)
        # Offset in hours
        if priority >= 4:
            hours_offset = random.randint(2, 18)
        elif priority == 3:
            hours_offset = random.randint(12, 48)
        else:
            hours_offset = random.randint(36, 168)

        deadline_ts = now_ts + (hours_offset * 3600)

        # Status distribution: 40% Pending (1), 20% Assigned (2), 20% In Transit (3), 15% Delivered (4), 5% Created (0)
        r_s = random.random()
        if r_s < 0.10:
            status = 0 # Created
        elif r_s < 0.50:
            status = 1 # Pending
        elif r_s < 0.70:
            status = 2 # Assigned
        elif r_s < 0.88:
            status = 3 # In Transit
        else:
            status = 4 # Delivered

        created_str = (now - timedelta(hours=random.randint(1, 72))).strftime("%Y-%m-%d %H:%M:%S")
        updated_str = now.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO shipments (shipment_code, weight, volume, destination, deadline_timestamp, priority, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (shipment_code, weight, volume, dest, deadline_ts, priority, status, created_str, updated_str))

        # Add initial processing history
        cursor.execute("""
        INSERT INTO processing_history (action_type, shipment_id, details, timestamp)
        VALUES (?, ?, ?, ?);
        """, ("CREATED", i, f"Shipment {shipment_code} registered for {dest}", now_ts - random.randint(100, 3600)))

        # Add initial status history
        cursor.execute("""
        INSERT INTO shipment_status_history (shipment_id, from_status, to_status, changed_at, notes)
        VALUES (?, ?, ?, ?, ?);
        """, (i, 0, status, updated_str, "Initial dataset ingestion"))

    # Assign some shipments to vehicles to demonstrate assigned capacity
    cursor.execute("SELECT id, weight, volume FROM shipments WHERE status IN (2, 3);")
    assigned_shipments = cursor.fetchall()
    cursor.execute("SELECT id, max_weight, max_volume FROM vehicles;")
    v_rows = cursor.fetchall()

    for idx, shp in enumerate(assigned_shipments):
        v = v_rows[idx % len(v_rows)]
        cursor.execute("""
        INSERT INTO vehicle_assignments (vehicle_id, shipment_id, assigned_at, status)
        VALUES (?, ?, ?, 'ACTIVE');
        """, (v['id'], shp['id'], now.strftime("%Y-%m-%d %H:%M:%S")))

        # Update vehicle current weight and volume
        cursor.execute("""
        UPDATE vehicles
        SET current_weight = current_weight + ?,
            current_volume = current_volume + ?
        WHERE id = ?;
        """, (shp['weight'], shp['volume'], v['id']))

    conn.commit()
    conn.close()

def export_initial_csv_files():
    import pandas as pd
    conn = get_db_connection()
    df_s = pd.read_sql_query("SELECT * FROM shipments", conn)
    df_v = pd.read_sql_query("SELECT * FROM vehicles", conn)
    df_r = pd.read_sql_query("SELECT * FROM roads", conn)
    conn.close()

    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    df_s.to_csv(os.path.join(data_dir, "sample_shipments.csv"), index=False)
    df_v.to_csv(os.path.join(data_dir, "sample_vehicles.csv"), index=False)
    df_r.to_csv(os.path.join(data_dir, "sample_roads.csv"), index=False)
