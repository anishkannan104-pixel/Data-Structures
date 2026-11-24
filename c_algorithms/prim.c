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

#define INF 1e18

EXPORT_API int run_prim_mst(int start_vertex, CMSTResult* out_result) {
    double start_t = get_high_res_time_us();
    CGraph* g = get_global_graph_internal();

    if (!out_result) return 0;
    memset(out_result, 0, sizeof(CMSTResult));

    if (!g || g->vertex_count <= 0) return 0;
    int n = g->vertex_count;

    if (start_vertex < 0 || start_vertex >= n) start_vertex = 0;

    double key[MAX_VERTICES];
    int parent[MAX_VERTICES];
    int in_mst[MAX_VERTICES] = {0};
    long long operations = 0;

    for (int i = 0; i < n; i++) {
        key[i] = INF;
        parent[i] = -1;
    }
    key[start_vertex] = 0.0;

    for (int count = 0; count < n; count++) {
        double min_val = INF;
        int u = -1;

        for (int v = 0; v < n; v++) {
            operations++;
            if (!in_mst[v] && key[v] < min_val) {
                min_val = key[v];
                u = v;
            }
        }

        if (u == -1 || min_val >= INF) break;
        in_mst[u] = 1;

        EdgeNode* edge = g->adj[u];
        while (edge) {
            operations++;
            if (edge->is_active && edge->dest >= 0 && edge->dest < n) {
                int v = edge->dest;
                double w = edge->weight;
                if (!in_mst[v] && w < key[v]) {
                    key[v] = w;
                    parent[v] = u;
                }
            }
            edge = edge->next;
        }
    }

    int edge_cnt = 0;
    double total_cost = 0.0;

    for (int i = 0; i < n; i++) {
        if (parent[i] != -1 && key[i] < INF && edge_cnt < MAX_EDGES) {
            out_result->u[edge_cnt] = parent[i];
            out_result->v[edge_cnt] = i;
            out_result->weights[edge_cnt] = key[i];
            total_cost += key[i];
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
