#include "common.h"

typedef struct EdgeNode {
    int dest;
    double weight;
    int road_id;
    int is_active;
    struct EdgeNode* next;
} EdgeNode;

typedef struct {
    int vertex_count;
    int edge_count;
    CLocation locations[MAX_VERTICES];
    EdgeNode* adj[MAX_VERTICES];
} CGraph;

extern CGraph* get_global_graph_internal(void);

typedef struct {
    int u;
    int v;
    double weight;
    int road_id;
} KEdge;

// Disjoint Set Union (DSU) structure
typedef struct {
    int parent[MAX_VERTICES];
    int rank[MAX_VERTICES];
} DSU;

static void dsu_init(DSU* dsu, int n) {
    for (int i = 0; i < n; i++) {
        dsu->parent[i] = i;
        dsu->rank[i] = 0;
    }
}

static int dsu_find(DSU* dsu, int i, long long* operations) {
    if (operations) (*operations)++;
    if (dsu->parent[i] != i) {
        dsu->parent[i] = dsu_find(dsu, dsu->parent[i], operations); // Path compression
    }
    return dsu->parent[i];
}

static int dsu_union(DSU* dsu, int x, int y, long long* operations) {
    int root_x = dsu_find(dsu, x, operations);
    int root_y = dsu_find(dsu, y, operations);

    if (root_x == root_y) return 0; // Same set, adding edge creates cycle

    if (operations) (*operations)++;
    if (dsu->rank[root_x] < dsu->rank[root_y]) {
        dsu->parent[root_x] = root_y;
    } else if (dsu->rank[root_x] > dsu->rank[root_y]) {
        dsu->parent[root_y] = root_x;
    } else {
        dsu->parent[root_y] = root_x;
        dsu->rank[root_x]++;
    }
    return 1;
}

static void kruskal_sort_edges(KEdge* edges, int n, long long* operations) {
    // Insertion sort or quicksort on edges
    for (int i = 1; i < n; i++) {
        KEdge key = edges[i];
        int j = i - 1;
        while (j >= 0 && edges[j].weight > key.weight) {
            if (operations) (*operations)++;
            edges[j + 1] = edges[j];
            j--;
        }
        if (operations) (*operations)++;
        edges[j + 1] = key;
    }
}

EXPORT_API int run_kruskal_mst(CMSTResult* out_result) {
    double start_t = get_high_res_time_us();
    CGraph* g = get_global_graph_internal();

    if (!out_result) return 0;
    memset(out_result, 0, sizeof(CMSTResult));

    if (!g || g->vertex_count <= 0) return 0;
    int n = g->vertex_count;

    KEdge edges[MAX_EDGES];
    int num_edges = 0;

    // Collect all unique active undirected edges
    for (int u = 0; u < n; u++) {
        EdgeNode* curr = g->adj[u];
        while (curr) {
            if (curr->is_active && u < curr->dest && num_edges < MAX_EDGES) {
                edges[num_edges].u = u;
                edges[num_edges].v = curr->dest;
                edges[num_edges].weight = curr->weight;
                edges[num_edges].road_id = curr->road_id;
                num_edges++;
            }
            curr = curr->next;
        }
    }

    long long operations = 0;
    kruskal_sort_edges(edges, num_edges, &operations);

    DSU dsu;
    dsu_init(&dsu, n);

    int edge_cnt = 0;
    double total_cost = 0.0;

    for (int i = 0; i < num_edges && edge_cnt < n - 1; i++) {
        if (dsu_union(&dsu, edges[i].u, edges[i].v, &operations)) {
            out_result->u[edge_cnt] = edges[i].u;
            out_result->v[edge_cnt] = edges[i].v;
            out_result->weights[edge_cnt] = edges[i].weight;
            total_cost += edges[i].weight;
            edge_cnt++;
        }
    }

    double end_t = get_high_res_time_us();

    out_result->edge_count = edge_cnt;
    out_result->total_cost = total_cost;
    out_result->execution_time_us = (end_t - start_t);
    out_result->operations = operations;
    return edge_cnt;
}
