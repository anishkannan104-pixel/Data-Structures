import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from backend.performance_service import performance_service
from backend.database import get_db_connection

def render_performance():
    st.markdown('<h1 class="main-title">Algorithm Performance Evaluation & Empirical Complexity Analysis</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Rigorous Empirical Telemetry: High-Resolution Timers, Precise Comparison Counters, and Controlled Benchmarking across Identical Datasets</p>', unsafe_allow_html=True)

    perf_tabs = st.tabs([
        "1. Searching Algorithms (5 Trees)",
        "2. Sorting Algorithms (3 Methods)",
        "3. Graph Algorithms (5 Graph Engines)",
        "4. Historical Benchmark Audit Log"
    ])

    # 1. SEARCHING ALGORITHMS
    with perf_tabs[0]:
        st.markdown("### Search Trees Benchmark: BST vs AVL vs Red-Black vs B-Tree vs Splay Tree")
        st.info("Measures empirical lookup cost on an identical dataset of randomly generated integer keys, recording real microseconds and comparison counts in C.")

        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            input_n = st.select_slider("Dataset Size (Keys):", options=[50, 100, 250, 500, 1000], value=250)
            target_idx = st.slider("Target Key Position in Sorted Order:", 0, 100, 50, help="0: Minimum key, 50: Median key, 100: Maximum key")
            btn_run_search_bench = st.button("Run Real Search Tree Benchmark")

        with col_s2:
            if btn_run_search_bench:
                import random
                rng = random.Random(1337)
                keys = list(set([rng.randint(100, 99999) for _ in range(input_n * 2)]))[:input_n]
                keys_sorted = sorted(keys)
                target = keys_sorted[int((target_idx / 100.0) * (len(keys_sorted) - 1))]

                tree_perf = performance_service.benchmark_search_trees(keys, target)

                df_trees = pd.DataFrame([
                    {
                        "Algorithm": name,
                        "Measured Time (μs)": res["execution_time_us"],
                        "Comparisons": res["comparisons"],
                        "Tree Height": res["height"],
                        "Time Complexity": res["time_complexity"],
                        "Space Complexity": res["space_complexity"]
                    } for name, res in tree_perf.items()
                ])
                st.dataframe(df_trees, use_container_width=True, hide_index=True)

                # Charts
                fig, (ax_c, ax_t) = plt.subplots(1, 2, figsize=(8, 3.2))
                names = list(tree_perf.keys())
                comps = [tree_perf[k]["comparisons"] for k in names]
                times = [tree_perf[k]["execution_time_us"] for k in names]

                bars1 = ax_c.bar(names, comps, color="#3b82f6", width=0.55)
                ax_c.set_ylabel("Comparison Count", fontweight="bold", fontsize=8)
                ax_c.set_title(f"Search Comparisons (N={input_n})", fontweight="bold", fontsize=9)
                ax_c.tick_params(axis="x", rotation=30, labelsize=7)
                for b in bars1:
                    ax_c.text(b.get_x() + b.get_width()/2, b.get_height() + 0.1, f"{int(b.get_height())}", ha="center", fontsize=7, fontweight="bold")

                bars2 = ax_t.bar(names, times, color="#10b981", width=0.55)
                ax_t.set_ylabel("Execution Time (μs)", fontweight="bold", fontsize=8)
                ax_t.set_title(f"Measured Execution Time (N={input_n})", fontweight="bold", fontsize=9)
                ax_t.tick_params(axis="x", rotation=30, labelsize=7)
                for b in bars2:
                    ax_t.text(b.get_x() + b.get_width()/2, b.get_height() + 0.05, f"{b.get_height():.2f}", ha="center", fontsize=7, fontweight="bold")

                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("Select parameters and click 'Run Real Search Tree Benchmark'.")

    # 2. SORTING ALGORITHMS
    with perf_tabs[1]:
        st.markdown("### Sorting Benchmark: Quick Sort vs Merge Sort vs Heap Sort")
        st.info("Executes pure C sorting algorithms on identical pseudo-random integer arrays of varying scales.")

        col_sort1, col_sort2 = st.columns([1, 2])
        with col_sort1:
            sort_scale = st.select_slider("Array Size (N Elements):", options=[500, 1000, 2500, 5000, 10000], value=2500)
            btn_run_sort_bench = st.button("Run Sorting Scale Benchmark")

        with col_sort2:
            if btn_run_sort_bench:
                sort_res = performance_service.benchmark_sorting(input_size=sort_scale)

                df_sort = pd.DataFrame([
                    {
                        "Algorithm": name,
                        "Measured Time (μs)": res["execution_time_us"],
                        "Comparisons": res["comparisons"],
                        "Operations": res["operations"],
                        "Time Complexity": res["time_complexity"],
                        "Space Complexity": res["space_complexity"]
                    } for name, res in sort_res.items()
                ])
                st.dataframe(df_sort, use_container_width=True, hide_index=True)

                fig, (ax_st, ax_sc) = plt.subplots(1, 2, figsize=(8, 3.2))
                s_names = list(sort_res.keys())
                s_times = [sort_res[k]["execution_time_us"] for k in s_names]
                s_comps = [sort_res[k]["comparisons"] for k in s_names]

                bars_t = ax_st.bar(s_names, s_times, color=["#2563eb", "#059669", "#d97706"], width=0.5)
                ax_st.set_ylabel("Execution Time (μs)", fontweight="bold", fontsize=8)
                ax_st.set_title(f"Runtime in Microseconds (N={sort_scale})", fontweight="bold", fontsize=9)
                for b in bars_t:
                    ax_st.text(b.get_x() + b.get_width()/2, b.get_height() + 5, f"{b.get_height():.1f} μs", ha="center", fontsize=7, fontweight="bold")

                bars_c = ax_sc.bar(s_names, s_comps, color=["#60a5fa", "#34d399", "#fbbf24"], width=0.5)
                ax_sc.set_ylabel("Comparison Count", fontweight="bold", fontsize=8)
                ax_sc.set_title(f"Total Comparisons (N={sort_scale})", fontweight="bold", fontsize=9)
                for b in bars_c:
                    ax_sc.text(b.get_x() + b.get_width()/2, b.get_height() + 50, f"{int(b.get_height())}", ha="center", fontsize=7, fontweight="bold")

                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("Select array scale and click 'Run Sorting Scale Benchmark'.")

    # 3. GRAPH ALGORITHMS
    with perf_tabs[2]:
        st.markdown("### Graph Algorithms Benchmark: BFS vs DFS vs Dijkstra vs Prim vs Kruskal")
        st.info("Compares the execution duration and algorithmic operation complexity of graph traversal, single-source shortest path, and minimum spanning tree algorithms on the active road network in C.")

        if st.button("Run Graph Algorithms Evaluation"):
            g_bench = performance_service.benchmark_graph_algorithms(source=0, dest=14)

            df_graph = pd.DataFrame([
                {
                    "Algorithm": name,
                    "Execution Time (μs)": res["execution_time_us"],
                    "Comparisons / Visited": res["comparisons"],
                    "Operations": res["operations"],
                    "Time Complexity": res["time_complexity"],
                    "Space Complexity": res["space_complexity"]
                } for name, res in g_bench.items()
            ])
            st.dataframe(df_graph, use_container_width=True, hide_index=True)

            fig, ax = plt.subplots(figsize=(7, 3.2))
            g_names = list(g_bench.keys())
            g_times = [g_bench[k]["execution_time_us"] for k in g_names]
            bars_g = ax.bar(g_names, g_times, color="#6366f1", width=0.55)
            ax.set_ylabel("Execution Time (μs)", fontweight="bold", fontsize=8)
            ax.set_title("C Graph Algorithm Runtimes on 16-Node 36-Edge Topology", fontweight="bold", fontsize=9)
            for b in bars_g:
                ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.1, f"{b.get_height():.2f} μs", ha="center", fontsize=7, fontweight="bold")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # 4. AUDIT LOG
    with perf_tabs[3]:
        st.markdown("### Historical Algorithm Performance Audit Log (Persisted in SQLite)")
        st.info("Every benchmark execution is captured in the `algorithm_performance` table with exact timestamps, input sizes, and hardware runtime measurements.")

        conn = get_db_connection()
        perf_df = pd.read_sql_query("""
            SELECT 
                recorded_at as Recorded_At,
                category as Category,
                algorithm_name as Algorithm,
                input_size as N,
                execution_time_us as Time_us,
                comparisons as Comparisons,
                operations as Operations
            FROM algorithm_performance
            ORDER BY id DESC
            LIMIT 30;
        """, conn)
        conn.close()

        if not perf_df.empty:
            st.dataframe(perf_df, use_container_width=True, hide_index=True)
        else:
            st.info("No benchmark history logged yet. Run any benchmark above to persist results.")
