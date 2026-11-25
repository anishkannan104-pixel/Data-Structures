import ctypes
import random
import time
from datetime import datetime
from backend.database import get_db_connection
from backend.c_bridge import c_bridge, CPerformanceResult
from backend.graph_service import graph_service

class PerformanceService:
    def __init__(self):
        self.c = c_bridge

    def benchmark_search_trees(self, keys, target_key):
        """Compares BST, AVL, Red-Black, B-Tree, and Splay Tree on identical dataset."""
        n = len(keys)
        results = {}

        # 1. BST
        self.c.lib.bst_clear()
        for k in keys:
            self.c.lib.bst_insert(k, None)
        comp_bst = ctypes.c_longlong(0)
        time_bst = ctypes.c_double(0.0)
        found_bst = self.c.lib.bst_search(target_key, None, ctypes.byref(comp_bst), ctypes.byref(time_bst))
        h_bst = self.c.lib.bst_height()
        results["BST"] = {
            "found": bool(found_bst),
            "comparisons": comp_bst.value,
            "execution_time_us": round(time_bst.value, 3),
            "height": h_bst,
            "time_complexity": "O(log n) avg, O(n) worst",
            "space_complexity": "O(n)"
        }

        # 2. AVL Tree
        self.c.lib.avl_clear()
        for k in keys:
            self.c.lib.avl_insert(k, None)
        comp_avl = ctypes.c_longlong(0)
        time_avl = ctypes.c_double(0.0)
        found_avl = self.c.lib.avl_search(target_key, None, ctypes.byref(comp_avl), ctypes.byref(time_avl))
        h_avl = self.c.lib.avl_height()
        results["AVL Tree"] = {
            "found": bool(found_avl),
            "comparisons": comp_avl.value,
            "execution_time_us": round(time_avl.value, 3),
            "height": h_avl,
            "time_complexity": "O(log n) strict",
            "space_complexity": "O(n)"
        }

        # 3. Red-Black Tree
        self.c.lib.rb_clear()
        for k in keys:
            self.c.lib.rb_insert(k, None)
        comp_rb = ctypes.c_longlong(0)
        time_rb = ctypes.c_double(0.0)
        found_rb = self.c.lib.rb_search(target_key, None, ctypes.byref(comp_rb), ctypes.byref(time_rb))
        h_rb = self.c.lib.rb_height()
        results["Red-Black Tree"] = {
            "found": bool(found_rb),
            "comparisons": comp_rb.value,
            "execution_time_us": round(time_rb.value, 3),
            "height": h_rb,
            "time_complexity": "O(log n)",
            "space_complexity": "O(n)"
        }

        # 4. B-Tree
        self.c.lib.btree_clear()
        for k in keys:
            self.c.lib.btree_insert(k, None)
        comp_bt = ctypes.c_longlong(0)
        time_bt = ctypes.c_double(0.0)
        found_bt = self.c.lib.btree_search(target_key, None, ctypes.byref(comp_bt), ctypes.byref(time_bt))
        h_bt = self.c.lib.btree_height()
        results["B-Tree"] = {
            "found": bool(found_bt),
            "comparisons": comp_bt.value,
            "execution_time_us": round(time_bt.value, 3),
            "height": h_bt,
            "time_complexity": "O(log n)",
            "space_complexity": "O(n)"
        }

        # 5. Splay Tree
        self.c.lib.splay_clear()
        for k in keys:
            self.c.lib.splay_insert(k, None)
        comp_sp = ctypes.c_longlong(0)
        time_sp = ctypes.c_double(0.0)
        found_sp = self.c.lib.splay_search(target_key, None, ctypes.byref(comp_sp), ctypes.byref(time_sp))
        h_sp = self.c.lib.splay_height()
        results["Splay Tree"] = {
            "found": bool(found_sp),
            "comparisons": comp_sp.value,
            "execution_time_us": round(time_sp.value, 3),
            "height": h_sp,
            "time_complexity": "O(log n) amortized",
            "space_complexity": "O(n)"
        }

        # Save to DB
        self._record_benchmark("Searching", n, results)
        return results

    def benchmark_sorting(self, input_size=1000, seed=42):
        """Compares Quick Sort, Merge Sort, and Heap Sort on identical integer arrays."""
        rng = random.Random(seed)
        base_array = [rng.randint(1, 100000) for _ in range(input_size)]
        results = {}

        # 1. Quick Sort
        arr1 = (ctypes.c_int * input_size)(*base_array)
        perf_qs = CPerformanceResult()
        self.c.lib.benchmark_quick_sort_ints(arr1, input_size, ctypes.byref(perf_qs))
        results["Quick Sort"] = {
            "execution_time_us": round(perf_qs.execution_time_us, 2),
            "comparisons": perf_qs.comparisons,
            "operations": perf_qs.operations,
            "time_complexity": "O(n log n) avg, O(n²) worst",
            "space_complexity": "O(log n)"
        }

        # 2. Merge Sort
        arr2 = (ctypes.c_int * input_size)(*base_array)
        perf_ms = CPerformanceResult()
        self.c.lib.benchmark_merge_sort_ints(arr2, input_size, ctypes.byref(perf_ms))
        results["Merge Sort"] = {
            "execution_time_us": round(perf_ms.execution_time_us, 2),
            "comparisons": perf_ms.comparisons,
            "operations": perf_ms.operations,
            "time_complexity": "O(n log n) guaranteed",
            "space_complexity": "O(n)"
        }

        # 3. Heap Sort
        arr3 = (ctypes.c_int * input_size)(*base_array)
        perf_hs = CPerformanceResult()
        self.c.lib.benchmark_heap_sort_ints(arr3, input_size, ctypes.byref(perf_hs))
        results["Heap Sort"] = {
            "execution_time_us": round(perf_hs.execution_time_us, 2),
            "comparisons": perf_hs.comparisons,
            "operations": perf_hs.operations,
            "time_complexity": "O(n log n)",
            "space_complexity": "O(1) in-place"
        }

        self._record_benchmark("Sorting", input_size, results)
        return results

    def benchmark_graph_algorithms(self, source=0, dest=14):
        """Compares BFS, DFS, Dijkstra, Prim, and Kruskal on current network graph."""
        results = {}

        # BFS
        bfs_res = graph_service.run_bfs(source)
        results["BFS"] = {
            "execution_time_us": bfs_res["execution_time_us"],
            "comparisons": bfs_res["total_visited"],
            "operations": bfs_res["total_visited"] * 2,
            "time_complexity": "O(V + E)",
            "space_complexity": "O(V)"
        }

        # DFS
        dfs_res = graph_service.run_dfs(source)
        results["DFS"] = {
            "execution_time_us": dfs_res["execution_time_us"],
            "comparisons": dfs_res["total_visited"],
            "operations": dfs_res["total_visited"] * 2,
            "time_complexity": "O(V + E)",
            "space_complexity": "O(V)"
        }

        # Dijkstra
        dijk_res = graph_service.run_dijkstra(source, dest)
        results["Dijkstra"] = {
            "execution_time_us": dijk_res["execution_time_us"],
            "comparisons": dijk_res["comparisons"],
            "operations": dijk_res["comparisons"] * 2,
            "time_complexity": "O(V² + E)",
            "space_complexity": "O(V)"
        }

        # Prim's MST
        prim_res = graph_service.run_prim_mst(source)
        results["Prim's MST"] = {
            "execution_time_us": prim_res["execution_time_us"],
            "comparisons": prim_res["operations"],
            "operations": prim_res["operations"],
            "time_complexity": "O(V²)",
            "space_complexity": "O(V)"
        }

        # Kruskal's MST
        krusk_res = graph_service.run_kruskal_mst()
        results["Kruskal's MST"] = {
            "execution_time_us": krusk_res["execution_time_us"],
            "comparisons": krusk_res["operations"],
            "operations": krusk_res["operations"],
            "time_complexity": "O(E log E)",
            "space_complexity": "O(V + E)"
        }

        self._record_benchmark("Graph", 16, results)
        return results

    def _record_benchmark(self, category, input_size, results_dict):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            for alg_name, data in results_dict.items():
                cursor.execute("""
                INSERT INTO algorithm_performance (algorithm_name, category, input_size, execution_time_us, comparisons, operations, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    alg_name,
                    category,
                    input_size,
                    data.get("execution_time_us", 0.0),
                    data.get("comparisons", 0),
                    data.get("operations", 0),
                    now_str
                ))
            conn.commit()
        finally:
            conn.close()

    def get_historical_benchmarks(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM algorithm_performance ORDER BY id DESC LIMIT 50;").fetchall()
        conn.close()
        return [dict(r) for r in rows]

performance_service = PerformanceService()
