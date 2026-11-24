import pytest
import ctypes
import time
from backend.c_bridge import c_bridge, CShipment
from backend.shipment_service import shipment_service

def test_c_linked_list():
    c_bridge.lib.ll_init()
    assert c_bridge.lib.ll_count() == 0

    s1 = CShipment()
    s1.id = 101
    s1.shipment_code = b"TEST-101"
    s1.weight = 50.0
    s1.volume = 1.2
    s1.priority = 3
    s1.status = 1

    s2 = CShipment()
    s2.id = 102
    s2.shipment_code = b"TEST-102"
    s2.weight = 80.0
    s2.volume = 2.0
    s2.priority = 4
    s2.status = 1

    c_bridge.lib.ll_insert_tail(ctypes.byref(s1))
    c_bridge.lib.ll_insert_tail(ctypes.byref(s2))
    assert c_bridge.lib.ll_count() == 2

    # Update
    assert c_bridge.lib.ll_update(101, 55.0, 1.5, 4, 2) == 1
    found_s = CShipment()
    assert c_bridge.lib.ll_find(101, ctypes.byref(found_s)) == 1
    assert found_s.weight == 55.0

    # Delete
    assert c_bridge.lib.ll_delete_by_id(101) == 1
    assert c_bridge.lib.ll_count() == 1
    assert c_bridge.lib.ll_find(101, ctypes.byref(found_s)) == 0

def test_c_stack():
    c_bridge.lib.stack_init()
    assert c_bridge.lib.stack_size() == 0

    c_bridge.lib.stack_push(1, b"ACTION_A", 100, int(time.time()), b"First push")
    c_bridge.lib.stack_push(2, b"ACTION_B", 200, int(time.time()), b"Second push")
    assert c_bridge.lib.stack_size() == 2

    # Peek
    act_id = ctypes.c_int(0)
    act_name = ctypes.create_string_buffer(32)
    shp_id = ctypes.c_int(0)
    ts = ctypes.c_longlong(0)
    det = ctypes.create_string_buffer(128)
    assert c_bridge.lib.stack_peek(ctypes.byref(act_id), act_name, ctypes.byref(shp_id), ctypes.byref(ts), det) == 1
    assert act_name.value == b"ACTION_B"
    assert shp_id.value == 200

    # Pop
    assert c_bridge.lib.stack_pop(ctypes.byref(act_id), act_name, ctypes.byref(shp_id), ctypes.byref(ts), det) == 1
    assert act_name.value == b"ACTION_B"
    assert c_bridge.lib.stack_size() == 1

def test_c_queue():
    c_bridge.lib.queue_init()
    assert c_bridge.lib.queue_size() == 0

    s1 = CShipment()
    s1.id = 1
    s1.shipment_code = b"Q-1"
    s2 = CShipment()
    s2.id = 2
    s2.shipment_code = b"Q-2"

    c_bridge.lib.queue_enqueue(ctypes.byref(s1))
    c_bridge.lib.queue_enqueue(ctypes.byref(s2))
    assert c_bridge.lib.queue_size() == 2

    out_s = CShipment()
    assert c_bridge.lib.queue_dequeue(ctypes.byref(out_s)) == 1
    assert out_s.id == 1
    assert c_bridge.lib.queue_dequeue(ctypes.byref(out_s)) == 1
    assert out_s.id == 2
    assert c_bridge.lib.queue_size() == 0

def test_c_priority_queue():
    c_bridge.lib.pq_init()
    assert c_bridge.lib.pq_size() == 0

    s_low = CShipment()
    s_low.id = 1; s_low.priority = 1; s_low.deadline_timestamp = 1000
    s_high = CShipment()
    s_high.id = 2; s_high.priority = 5; s_high.deadline_timestamp = 2000
    s_med = CShipment()
    s_med.id = 3; s_med.priority = 3; s_med.deadline_timestamp = 1500

    c_bridge.lib.pq_insert(ctypes.byref(s_low))
    c_bridge.lib.pq_insert(ctypes.byref(s_high))
    c_bridge.lib.pq_insert(ctypes.byref(s_med))

    # Highest priority (5) must be extracted first
    out_s = CShipment()
    assert c_bridge.lib.pq_extract_max(ctypes.byref(out_s)) == 1
    assert out_s.id == 2
    assert out_s.priority == 5

    # Next highest (3)
    assert c_bridge.lib.pq_extract_max(ctypes.byref(out_s)) == 1
    assert out_s.id == 3

    # Lowest (1)
    assert c_bridge.lib.pq_extract_max(ctypes.byref(out_s)) == 1
    assert out_s.id == 1

def test_c_min_heap():
    c_bridge.lib.minheap_init()
    assert c_bridge.lib.minheap_size() == 0

    s_early = CShipment()
    s_early.id = 1; s_early.deadline_timestamp = 100
    s_late = CShipment()
    s_late.id = 2; s_late.deadline_timestamp = 900
    s_mid = CShipment()
    s_mid.id = 3; s_mid.deadline_timestamp = 500

    c_bridge.lib.minheap_insert(ctypes.byref(s_late))
    c_bridge.lib.minheap_insert(ctypes.byref(s_early))
    c_bridge.lib.minheap_insert(ctypes.byref(s_mid))

    # Peek min
    out_s = CShipment()
    assert c_bridge.lib.minheap_peek_min(ctypes.byref(out_s)) == 1
    assert out_s.id == 1

    # Extract min
    assert c_bridge.lib.minheap_extract_min(ctypes.byref(out_s)) == 1
    assert out_s.id == 1
    assert c_bridge.lib.minheap_extract_min(ctypes.byref(out_s)) == 1
    assert out_s.id == 3
    assert c_bridge.lib.minheap_extract_min(ctypes.byref(out_s)) == 1
    assert out_s.id == 2
