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

EXPORT_API int run_bfs(int start_vertex, int* out_visited_order, int* out_levels, int max_vertices, int* out_visited_count, double* out_time_us) {
    double start_t = get_high_res_time_us();
    CGraph* g = get_global_graph_internal();

    if (!g || start_vertex < 0 || start_vertex >= g->vertex_count || !out_visited_order) {
        if (out_visited_count) *out_visited_count = 0;
        if (out_time_us) *out_time_us = 0.0;
        return 0;
    }

    int visited[MAX_VERTICES] = {0};
    int levels[MAX_VERTICES] = {0};
    int queue[MAX_VERTICES];
    int front = 0, rear = 0;
    int order_idx = 0;

    visited[start_vertex] = 1;
    levels[start_vertex] = 0;
    queue[rear++] = start_vertex;

    while (front < rear && order_idx < max_vertices) {
        int u = queue[front++];
        out_visited_order[order_idx] = u;
        if (out_levels) out_levels[order_idx] = levels[u];
        order_idx++;

        EdgeNode* edge = g->adj[u];
        while (edge) {
            if (edge->is_active && edge->dest >= 0 && edge->dest < g->vertex_count) {
                int v = edge->dest;
                if (!visited[v]) {
                    visited[v] = 1;
                    levels[v] = levels[u] + 1;
                    if (rear < MAX_VERTICES) {
                        queue[rear++] = v;
                    }
                }
            }
            edge = edge->next;
        }
    }

    double end_t = get_high_res_time_us();
    if (out_visited_count) *out_visited_count = order_idx;
    if (out_time_us) *out_time_us = (end_t - start_t);
    return order_idx;
}
