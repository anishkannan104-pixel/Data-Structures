# ADAPTIVE LOGISTICS INTELLIGENCE SYSTEM
### USING SELF-OPTIMIZING DATA STRUCTURES AND DYNAMIC GRAPH ALGORITHMS

A high-performance logistics management platform powered by native **C language algorithms**, connected through a **Python `ctypes` interoperability bridge**, backed by an **SQLite relational database**, and presented via a **Streamlit** user interface.

---

## 1. System Architecture Overview

The system strictly decouples high-speed computational data structures (implemented in C) from user interface, database management, and data reporting (implemented in Python):

```
┌────────────────────────────────────────────────────────────────────────┐
│                   STREAMLIT FRONTEND & VISUALIZATION                   │
│    Dashboard  •  Module 1  •  Module 2  •  Module 3  •  Performance    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                  PYTHON BACKEND & SERVICE LAYER                        │
│    shipment_service  •  vehicle_service  •  graph_service  •  database │
└───────────────┬────────────────────────────────────────┬───────────────┘
                │ (ctypes Interoperability)              │ (SQL Queries)
┌───────────────▼────────────────────────┐  ┌────────────▼───────────────┐
│       NATIVE C SHARED LIBRARY          │  │       SQLITE DATABASE      │
│          `logistics_c.dll`             │  │       `logistics.db`       │
│  • Linked List     • Stack / Queue     │  │  • shipments               │
│  • Priority Queue  • Min-Heap          │  │  • vehicles                │
│  • BST / AVL / RB  • B-Tree / Splay    │  │  • locations / roads       │
│  • Hash Table      • FSM Lifecycle     │  │  • vehicle_assignments     │
│  • Quick/Merge/Heap Sort               │  │  • status_history          │
│  • BFS / DFS / Dijkstra / Prim/Kruskal │  │  • algorithm_performance   │
└────────────────────────────────────────┘  └────────────────────────────┘
```

---

## 2. Core Modules & C Algorithms Catalog

### Module 1: Adaptive Shipment Processing & Deadline Management
- **Dynamic Linked List (`linked_list.c`)**: Dynamic allocation, O(1) head/tail insertion, O(N) deletion and updating of active shipments.
- **Audit & Undo Stack (`stack.c`)**: LIFO recording of recent shipment lifecycle transitions (Push, Pop, Peek).
- **Arrival FIFO Queue (`queue.c`)**: Sequential staging and first-come first-served processing of incoming consignments.
- **Urgent Priority Queue (`priority_queue.c`)**: Max-Heap priority scheduler giving precedence to critical cargo (Priority 5 & 4).
- **Deadline Min-Heap (`min_heap.c`)**: Continuous real-time deadline surveillance with O(1) minimum deadline identification and predictive alert generation.

### Module 2: Self-Optimizing Data Management & Integrity
- **5 Tree Search Structures**:
  1. *Binary Search Tree (`bst.c`)*
  2. *AVL Tree (`avl_tree.c`)* - Height-balanced rotations (LL, RR, LR, RL)
  3. *Red-Black Tree (`red_black_tree.c`)* - Color balancing and recoloring
  4. *B-Tree (`b_tree.c`)* - Multi-key node splitting (Order 4 / degree 2)
  5. *Splay Tree (`splay_tree.c`)* - Self-adjusting access with Zig, Zig-Zig, and Zig-Zag splays
- **Polynomial Hash Table (`hash_table.c`)**: Polynomial rolling hash function with separate chaining collision handling and O(1) duplicate shipment ID prevention.
- **Deterministic Finite State Machine (`finite_state_machine.c`)**: Strict transition matrix validation preventing invalid skips across states (`Created`, `Pending`, `Assigned`, `In Transit`, `Delivered`, `Cancelled`).
- **Sorting Engine (`quick_sort.c`, `merge_sort.c`, `heap_sort.c`)**: Real C sorting implementations parameterized by Shipment ID, Weight, Priority, or Deadline, measuring exact comparison counts and execution microseconds.

### Module 3: Intelligent Vehicle Assignment & Dynamic Route Optimization
- **Dual-Constraint Capacity Engine (`vehicle_service.py`)**: Validates BOTH Weight and Volume limits to prevent vehicle overloading.
- **Weighted Graph Network (`graph.c`)**: Adjacency list representation connecting 16 regional delivery hubs across 36 bi-directional roads.
- **Graph Algorithms**:
  - *Breadth-First Search (`bfs.c`)* - Radial level-by-level inspection
  - *Depth-First Search (`dfs.c`)* - Corridor exploration
  - *Dijkstra's Algorithm (`dijkstra.c`)* - Shortest path calculation with path reconstruction
  - *Prim's Algorithm (`prim.c`)* - Vertex-cut minimum spanning tree
  - *Kruskal's Algorithm (`kruskal.c`)* - Edge-sorted MST with Disjoint Set Union (DSU / Union-Find)
- **Dynamic Route Recalculation**: Simulates road disruptions, identifies impacted segments, recalculates detour paths via Dijkstra, and computes distance deltas.

---

## 3. Quick Start & Execution

The application is fully configured for single-command launch from Visual Studio Code or the Windows Command Prompt:

```cmd
.\run.bat
```

### Automatic Actions Performed by `run.bat`:
1. Identifies its directory dynamically using `%~dp0`.
2. Detects the local Python 3 environment.
3. Automatically sets up the virtual environment (`.venv`) on first execution.
4. Verifies the pre-compiled `bin/logistics_c.dll` (or recompiles via GCC if missing).
5. Initializes the SQLite database and loads the 110-shipment demonstration dataset.
6. **Dynamic Port Detection**: Scans available ports starting from `8502` (leaving `8501` untouched for other running projects).
7. Launches the Streamlit application server and opens the browser automatically.

---

## 4. Database Schema

The SQLite database (`database/logistics.db`) consists of 8 tables with foreign keys and integrity constraints:
1. `shipments`: Core cargo attributes, weights, volumes, deadlines, priorities, and statuses.
2. `vehicles`: Fleet inventory with maximum weight/volume thresholds and current utilization.
3. `locations`: Regional hub metadata with 2D spatial coordinate mapping.
4. `roads`: Weighted network edges with distance (km) and active/disabled flags.
5. `vehicle_assignments`: Relationship mapping between assigned vehicles and shipments.
6. `shipment_status_history`: Audit trail tracking every state transition.
7. `processing_history`: Stack-backed action log with timestamps.
8. `algorithm_performance`: Persisted empirical benchmark measurements (time in μs, comparisons, operations).

---

## 5. Automated Testing Suite

To execute the test suite:
```cmd
pytest tests/ -v
```
All 17 automated unit tests verify the C shared library functions, database constraints, tree search invariance, graph shortest paths, and MST cost equality.
