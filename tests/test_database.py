import pytest
import sqlite3
from backend.database import get_db_connection, init_db, seed_sample_data

def test_database_schema_and_tables():
    init_db()
    seed_sample_data()

    conn = get_db_connection()
    cursor = conn.cursor()

    required_tables = [
        "shipments",
        "vehicles",
        "locations",
        "roads",
        "vehicle_assignments",
        "shipment_status_history",
        "processing_history",
        "algorithm_performance"
    ]

    for table in required_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        assert count >= 0, f"Table {table} must exist."

    # Verify minimum initial record counts
    cursor.execute("SELECT COUNT(*) FROM shipments;")
    assert cursor.fetchone()[0] >= 100, "Must have at least 100 sample shipments."

    cursor.execute("SELECT COUNT(*) FROM vehicles;")
    assert cursor.fetchone()[0] >= 15, "Must have at least 15 vehicles."

    cursor.execute("SELECT COUNT(*) FROM locations;")
    assert cursor.fetchone()[0] >= 15, "Must have at least 15 delivery locations."

    cursor.execute("SELECT COUNT(*) FROM roads;")
    assert cursor.fetchone()[0] >= 25, "Must have at least 25 road connections."

    conn.close()

def test_duplicate_shipment_code_rejected():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT shipment_code FROM shipments LIMIT 1;")
    existing_code = cursor.fetchone()[0]

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
        INSERT INTO shipments (shipment_code, weight, volume, destination, deadline_timestamp, priority, status, created_at, updated_at)
        VALUES (?, 10.0, 1.0, 'Test', 1000, 1, 0, '2026-01-01', '2026-01-01');
        """, (existing_code,))
        conn.commit()

    conn.close()

def test_foreign_key_enforcement():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Attempt to insert road with non-existent locations
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
        INSERT INTO roads (source_id, dest_id, distance_km, is_active)
        VALUES (9999, 8888, 50.0, 1);
        """)
        conn.commit()

    conn.close()
