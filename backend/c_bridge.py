import ctypes
import os
import sys
import platform

# Locate compiled C library
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(PROJECT_ROOT, "bin")

if sys.platform == "win32":
    LIB_NAME = "logistics_c.dll"
elif sys.platform == "darwin":
    LIB_NAME = "liblogistics_c.dylib"
else:
    LIB_NAME = "liblogistics_c.so"

DLL_PATH = os.path.join(BIN_DIR, LIB_NAME)

# C-compatible Structures
class CShipment(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_int),
        ("shipment_code", ctypes.c_char * 32),
        ("weight", ctypes.c_double),
        ("volume", ctypes.c_double),
        ("destination", ctypes.c_char * 64),
        ("deadline_timestamp", ctypes.c_longlong),
        ("priority", ctypes.c_int),  # 1=Low, 2=Medium, 3=High, 4=Urgent, 5=Critical
        ("status", ctypes.c_int),    # 0=Created, 1=Pending, 2=Assigned, 3=In Transit, 4=Delivered, 5=Cancelled
    ]

    def to_dict(self):
        return {
            "id": self.id,
            "shipment_code": self.shipment_code.decode("utf-8", errors="ignore"),
            "weight": round(self.weight, 2),
            "volume": round(self.volume, 2),
            "destination": self.destination.decode("utf-8", errors="ignore"),
            "deadline_timestamp": self.deadline_timestamp,
            "priority": self.priority,
            "status": self.status,
        }

class CVehicle(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_int),
        ("vehicle_code", ctypes.c_char * 32),
        ("vehicle_type", ctypes.c_char * 64),
        ("max_weight", ctypes.c_double),
        ("max_volume", ctypes.c_double),
        ("current_weight", ctypes.c_double),
        ("current_volume", ctypes.c_double),
        ("is_available", ctypes.c_int),
    ]

class CPerformanceResult(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("execution_time_us", ctypes.c_double),
        ("comparisons", ctypes.c_longlong),
        ("operations", ctypes.c_longlong),
    ]

class CLocation(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_int),
        ("name", ctypes.c_char * 64),
        ("code", ctypes.c_char * 16),
        ("x_coord", ctypes.c_double),
        ("y_coord", ctypes.c_double),
    ]

class CRoad(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("source_id", ctypes.c_int),
        ("dest_id", ctypes.c_int),
        ("distance_km", ctypes.c_double),
        ("road_id", ctypes.c_int),
        ("is_active", ctypes.c_int),
    ]

MAX_VERTICES = 64
MAX_EDGES = 256

class CRouteResult(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("total_path_len", ctypes.c_int),
        ("path", ctypes.c_int * MAX_VERTICES),
        ("total_distance", ctypes.c_double),
        ("visited_count", ctypes.c_int),
        ("visited_nodes", ctypes.c_int * MAX_VERTICES),
        ("execution_time_us", ctypes.c_double),
        ("comparisons", ctypes.c_longlong),
    ]

class CMSTResult(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("edge_count", ctypes.c_int),
        ("u", ctypes.c_int * MAX_EDGES),
        ("v", ctypes.c_int * MAX_EDGES),
        ("weights", ctypes.c_double * MAX_EDGES),
        ("total_cost", ctypes.c_double),
        ("execution_time_us", ctypes.c_double),
        ("operations", ctypes.c_longlong),
    ]

class CBridge:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CBridge, cls).__new__(cls)
            cls._instance._init_library()
        return cls._instance

    def _init_library(self):
        if not os.path.exists(DLL_PATH):
            raise FileNotFoundError(f"C Shared library not found at: {DLL_PATH}")
        self.lib = ctypes.CDLL(DLL_PATH)
        self._bind_functions()

    def _bind_functions(self):
        # Linked List
        self.lib.ll_init.argtypes = []
        self.lib.ll_init.restype = None

        self.lib.ll_insert_head.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.ll_insert_head.restype = ctypes.c_int

        self.lib.ll_insert_tail.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.ll_insert_tail.restype = ctypes.c_int

        self.lib.ll_delete_by_id.argtypes = [ctypes.c_int]
        self.lib.ll_delete_by_id.restype = ctypes.c_int

        self.lib.ll_update.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int]
        self.lib.ll_update.restype = ctypes.c_int

        self.lib.ll_find.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment)]
        self.lib.ll_find.restype = ctypes.c_int

        self.lib.ll_count.argtypes = []
        self.lib.ll_count.restype = ctypes.c_int

        self.lib.ll_get_all.argtypes = [ctypes.POINTER(CShipment), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.ll_get_all.restype = ctypes.c_int

        # Stack
        self.lib.stack_init.argtypes = []
        self.lib.stack_init.restype = None

        self.lib.stack_push.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_longlong, ctypes.c_char_p]
        self.lib.stack_push.restype = ctypes.c_int

        self.lib.stack_pop.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_longlong), ctypes.c_char_p]
        self.lib.stack_pop.restype = ctypes.c_int

        self.lib.stack_peek.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_longlong), ctypes.c_char_p]
        self.lib.stack_peek.restype = ctypes.c_int

        self.lib.stack_size.argtypes = []
        self.lib.stack_size.restype = ctypes.c_int

        # Queue
        self.lib.queue_init.argtypes = []
        self.lib.queue_init.restype = None

        self.lib.queue_enqueue.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.queue_enqueue.restype = ctypes.c_int

        self.lib.queue_dequeue.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.queue_dequeue.restype = ctypes.c_int

        self.lib.queue_peek.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.queue_peek.restype = ctypes.c_int

        self.lib.queue_size.argtypes = []
        self.lib.queue_size.restype = ctypes.c_int

        self.lib.queue_get_all.argtypes = [ctypes.POINTER(CShipment), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.queue_get_all.restype = ctypes.c_int

        # Priority Queue
        self.lib.pq_init.argtypes = []
        self.lib.pq_init.restype = None

        self.lib.pq_insert.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.pq_insert.restype = ctypes.c_int

        self.lib.pq_extract_max.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.pq_extract_max.restype = ctypes.c_int

        self.lib.pq_peek_max.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.pq_peek_max.restype = ctypes.c_int

        self.lib.pq_size.argtypes = []
        self.lib.pq_size.restype = ctypes.c_int

        self.lib.pq_get_all.argtypes = [ctypes.POINTER(CShipment), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.pq_get_all.restype = ctypes.c_int

        # Min-Heap
        self.lib.minheap_init.argtypes = []
        self.lib.minheap_init.restype = None

        self.lib.minheap_insert.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.minheap_insert.restype = ctypes.c_int

        self.lib.minheap_extract_min.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.minheap_extract_min.restype = ctypes.c_int

        self.lib.minheap_peek_min.argtypes = [ctypes.POINTER(CShipment)]
        self.lib.minheap_peek_min.restype = ctypes.c_int

        self.lib.minheap_size.argtypes = []
        self.lib.minheap_size.restype = ctypes.c_int

        self.lib.minheap_get_all.argtypes = [ctypes.POINTER(CShipment), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.minheap_get_all.restype = ctypes.c_int

        self.lib.minheap_get_imminent.argtypes = [ctypes.c_longlong, ctypes.POINTER(CShipment), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.minheap_get_imminent.restype = ctypes.c_int

        # BST
        self.lib.bst_clear.argtypes = []
        self.lib.bst_clear.restype = None
        self.lib.bst_insert.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment)]
        self.lib.bst_insert.restype = ctypes.c_int
        self.lib.bst_search.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment), ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_double)]
        self.lib.bst_search.restype = ctypes.c_int
        self.lib.bst_height.argtypes = []
        self.lib.bst_height.restype = ctypes.c_int
        self.lib.bst_get_structure.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.bst_get_structure.restype = ctypes.c_int

        # AVL
        self.lib.avl_clear.argtypes = []
        self.lib.avl_clear.restype = None
        self.lib.avl_insert.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment)]
        self.lib.avl_insert.restype = ctypes.c_int
        self.lib.avl_search.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment), ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_double)]
        self.lib.avl_search.restype = ctypes.c_int
        self.lib.avl_height.argtypes = []
        self.lib.avl_height.restype = ctypes.c_int

        # Red-Black
        self.lib.rb_clear.argtypes = []
        self.lib.rb_clear.restype = None
        self.lib.rb_insert.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment)]
        self.lib.rb_insert.restype = ctypes.c_int
        self.lib.rb_search.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment), ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_double)]
        self.lib.rb_search.restype = ctypes.c_int
        self.lib.rb_height.argtypes = []
        self.lib.rb_height.restype = ctypes.c_int

        # B-Tree
        self.lib.btree_clear.argtypes = []
        self.lib.btree_clear.restype = None
        self.lib.btree_insert.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment)]
        self.lib.btree_insert.restype = ctypes.c_int
        self.lib.btree_search.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment), ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_double)]
        self.lib.btree_search.restype = ctypes.c_int
        self.lib.btree_height.argtypes = []
        self.lib.btree_height.restype = ctypes.c_int

        # Splay Tree
        self.lib.splay_clear.argtypes = []
        self.lib.splay_clear.restype = None
        self.lib.splay_insert.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment)]
        self.lib.splay_insert.restype = ctypes.c_int
        self.lib.splay_search.argtypes = [ctypes.c_int, ctypes.POINTER(CShipment), ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_double)]
        self.lib.splay_search.restype = ctypes.c_int
        self.lib.splay_height.argtypes = []
        self.lib.splay_height.restype = ctypes.c_int

        # Hash Table
        self.lib.hash_init.argtypes = []
        self.lib.hash_init.restype = None
        self.lib.hash_insert.argtypes = [ctypes.c_char_p, ctypes.POINTER(CShipment), ctypes.POINTER(ctypes.c_int)]
        self.lib.hash_insert.restype = ctypes.c_int
        self.lib.hash_search.argtypes = [ctypes.c_char_p, ctypes.POINTER(CShipment), ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_double)]
        self.lib.hash_search.restype = ctypes.c_int
        self.lib.hash_get_stats.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        self.lib.hash_get_stats.restype = ctypes.c_int
        self.lib.hash_get_bucket_entries.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.hash_get_bucket_entries.restype = ctypes.c_int

        # Finite State Machine
        self.lib.fsm_get_state_name.argtypes = [ctypes.c_int]
        self.lib.fsm_get_state_name.restype = ctypes.c_char_p
        self.lib.fsm_validate_transition.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        self.lib.fsm_validate_transition.restype = ctypes.c_int

        # Sorting Algorithms
        self.lib.run_quick_sort.argtypes = [ctypes.POINTER(CShipment), ctypes.c_int, ctypes.c_int, ctypes.POINTER(CPerformanceResult)]
        self.lib.run_quick_sort.restype = None
        self.lib.run_merge_sort.argtypes = [ctypes.POINTER(CShipment), ctypes.c_int, ctypes.c_int, ctypes.POINTER(CPerformanceResult)]
        self.lib.run_merge_sort.restype = None
        self.lib.run_heap_sort.argtypes = [ctypes.POINTER(CShipment), ctypes.c_int, ctypes.c_int, ctypes.POINTER(CPerformanceResult)]
        self.lib.run_heap_sort.restype = None

        self.lib.benchmark_quick_sort_ints.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(CPerformanceResult)]
        self.lib.benchmark_quick_sort_ints.restype = None
        self.lib.benchmark_merge_sort_ints.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(CPerformanceResult)]
        self.lib.benchmark_merge_sort_ints.restype = None
        self.lib.benchmark_heap_sort_ints.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(CPerformanceResult)]
        self.lib.benchmark_heap_sort_ints.restype = None

        # Graph Algorithms
        self.lib.graph_init.argtypes = []
        self.lib.graph_init.restype = None
        self.lib.graph_add_location.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_double, ctypes.c_double]
        self.lib.graph_add_location.restype = ctypes.c_int
        self.lib.graph_add_road.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_int, ctypes.c_int]
        self.lib.graph_add_road.restype = ctypes.c_int
        self.lib.graph_update_road_weight.argtypes = [ctypes.c_int, ctypes.c_double]
        self.lib.graph_update_road_weight.restype = ctypes.c_int
        self.lib.graph_set_road_active.argtypes = [ctypes.c_int, ctypes.c_int]
        self.lib.graph_set_road_active.restype = ctypes.c_int
        self.lib.graph_get_vertex_count.argtypes = []
        self.lib.graph_get_vertex_count.restype = ctypes.c_int
        self.lib.graph_get_all_roads.argtypes = [ctypes.POINTER(CRoad), ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self.lib.graph_get_all_roads.restype = ctypes.c_int

        self.lib.run_bfs.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double)]
        self.lib.run_bfs.restype = ctypes.c_int

        self.lib.run_dfs.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double)]
        self.lib.run_dfs.restype = ctypes.c_int

        self.lib.run_dijkstra.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(CRouteResult)]
        self.lib.run_dijkstra.restype = ctypes.c_int

        self.lib.run_prim_mst.argtypes = [ctypes.c_int, ctypes.POINTER(CMSTResult)]
        self.lib.run_prim_mst.restype = ctypes.c_int

        self.lib.run_kruskal_mst.argtypes = [ctypes.POINTER(CMSTResult)]
        self.lib.run_kruskal_mst.restype = ctypes.c_int

# Singleton instance
c_bridge = CBridge()
