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

static void dfs_util(CGraph* g, int u, int* visited, int* out_order, int max_vertices, int* count) {
    if (*count >= max_vertices) return;
    visited[u] = 1;
    out_order[(*count)++] = u;

    EdgeNode* edge = g->adj[u];
    while (edge) {
        if (edge->is_active && edge->dest >= 0 && edge->dest < g->vertex_count) {
            int v = edge->dest;
            if (!visited[v]) {
                dfs_util(g, v, visited, out_order, max_vertices, count);
            }
        }
        edge = edge->next;
    }
}

EXPORT_API int run_dfs(int start_vertex, int* out_visited_order, int max_vertices, int* out_visited_count, double* out_time_us) {
    double start_t = get_high_res_time_us();
    CGraph* g = get_global_graph_internal();

    if (!g || start_vertex < 0 || start_vertex >= g->vertex_count || !out_visited_order) {
        if (out_visited_count) *out_visited_count = 0;
        if (out_time_us) *out_time_us = 0.0;
        return 0;
    }

    int visited[MAX_VERTICES] = {0};
    int count = 0;

    dfs_util(g, start_vertex, visited, out_visited_order, max_vertices, &count);

    double end_t = get_high_res_time_us();
    if (out_visited_count) *out_visited_count = count;
    if (out_time_us) *out_time_us = (end_t - start_t);
    return count;
}
