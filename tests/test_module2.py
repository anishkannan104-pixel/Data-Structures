import pytest
import ctypes
from backend.c_bridge import c_bridge, CShipment
from backend.performance_service import performance_service
from backend.shipment_service import shipment_service

def test_trees_insertion_and_search():
    keys = [50, 30, 70, 20, 40, 60, 80]
    target = 60

    # BST
    c_bridge.lib.bst_clear()
    for k in keys: c_bridge.lib.bst_insert(k, None)
    comp = ctypes.c_longlong(0); t = ctypes.c_double(0.0)
    assert c_bridge.lib.bst_search(target, None, ctypes.byref(comp), ctypes.byref(t)) == 1
    assert comp.value > 0

    # AVL Tree
    c_bridge.lib.avl_clear()
    for k in keys: c_bridge.lib.avl_insert(k, None)
    assert c_bridge.lib.avl_search(target, None, ctypes.byref(comp), ctypes.byref(t)) == 1
    assert c_bridge.lib.avl_height() <= 4

    # Red-Black Tree
    c_bridge.lib.rb_clear()
    for k in keys: c_bridge.lib.rb_insert(k, None)
    assert c_bridge.lib.rb_search(target, None, ctypes.byref(comp), ctypes.byref(t)) == 1
    assert c_bridge.lib.rb_height() <= 5

    # B-Tree
    c_bridge.lib.btree_clear()
    for k in keys: c_bridge.lib.btree_insert(k, None)
    assert c_bridge.lib.btree_search(target, None, ctypes.byref(comp), ctypes.byref(t)) == 1

    # Splay Tree
    c_bridge.lib.splay_clear()
    for k in keys: c_bridge.lib.splay_insert(k, None)
    assert c_bridge.lib.splay_search(target, None, ctypes.byref(comp), ctypes.byref(t)) == 1

def test_hash_table_duplicate_detection():
    c_bridge.lib.hash_init()

    dup = ctypes.c_int(0)
    s1 = CShipment(); s1.id = 1; s1.shipment_code = b"SHP-UNIQ-1"
    assert c_bridge.lib.hash_insert(b"SHP-UNIQ-1", ctypes.byref(s1), ctypes.byref(dup)) == 1
    assert dup.value == 0

    # Insert identical key: duplicate must be flagged
    assert c_bridge.lib.hash_insert(b"SHP-UNIQ-1", ctypes.byref(s1), ctypes.byref(dup)) == 0
    assert dup.value == 1

def test_finite_state_machine_transitions():
    msg = ctypes.create_string_buffer(256)

    # Valid: Created (0) -> Pending (1)
    assert c_bridge.lib.fsm_validate_transition(0, 1, msg, 256) == 1

    # Valid: Pending (1) -> Assigned (2)
    assert c_bridge.lib.fsm_validate_transition(1, 2, msg, 256) == 1

    # Valid: Assigned (2) -> In Transit (3)
    assert c_bridge.lib.fsm_validate_transition(2, 3, msg, 256) == 1

    # Valid: In Transit (3) -> Delivered (4)
    assert c_bridge.lib.fsm_validate_transition(3, 4, msg, 256) == 1

    # INVALID: Created (0) -> Delivered (4)
    assert c_bridge.lib.fsm_validate_transition(0, 4, msg, 256) == 0

    # INVALID: Delivered (4) -> In Transit (3) (terminal state)
    assert c_bridge.lib.fsm_validate_transition(4, 3, msg, 256) == 0

    # INVALID: Cancelled (5) -> Assigned (2) (terminal state)
    assert c_bridge.lib.fsm_validate_transition(5, 2, msg, 256) == 0

def test_c_sorting_algorithms():
    shipments = [
        {"id": 1, "shipment_code": "S-1", "weight": 250.0, "volume": 2.0, "destination": "Hub A", "deadline_timestamp": 500, "priority": 2, "status": 1},
        {"id": 2, "shipment_code": "S-2", "weight": 50.0,  "volume": 0.5, "destination": "Hub B", "deadline_timestamp": 200, "priority": 5, "status": 1},
        {"id": 3, "shipment_code": "S-3", "weight": 500.0, "volume": 4.0, "destination": "Hub C", "deadline_timestamp": 900, "priority": 1, "status": 1},
        {"id": 4, "shipment_code": "S-4", "weight": 120.0, "volume": 1.2, "destination": "Hub D", "deadline_timestamp": 100, "priority": 4, "status": 1}
    ]

    # Quick sort by weight (ascending)
    qs_res = shipment_service.sort_shipments_c(shipments, criterion="weight", algorithm="Quick Sort")
    weights = [s["weight"] for s in qs_res["sorted"]]
    assert weights == [50.0, 120.0, 250.0, 500.0]

    # Merge sort by priority (descending: 5->1)
    ms_res = shipment_service.sort_shipments_c(shipments, criterion="priority", algorithm="Merge Sort")
    priorities = [s["priority"] for s in ms_res["sorted"]]
    assert priorities == [5, 4, 2, 1]

    # Heap sort by deadline (ascending: earliest first)
    hs_res = shipment_service.sort_shipments_c(shipments, criterion="deadline", algorithm="Heap Sort")
    deadlines = [s["deadline_timestamp"] for s in hs_res["sorted"]]
    assert deadlines == [100, 200, 500, 900]
