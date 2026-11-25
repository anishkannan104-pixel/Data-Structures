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

EXPORT_API int run_dijkstra(int source, int destination, CRouteResult* out_result) {
    double start_t = get_high_res_time_us();
    CGraph* g = get_global_graph_internal();

    if (!out_result) return 0;
    memset(out_result, 0, sizeof(CRouteResult));

    if (!g || source < 0 || source >= g->vertex_count || destination < 0 || destination >= g->vertex_count) {
        return 0;
    }

    int n = g->vertex_count;
    double dist[MAX_VERTICES];
    int visited[MAX_VERTICES] = {0};
    int parent[MAX_VERTICES];
    long long comparisons = 0;
    int visited_nodes_order[MAX_VERTICES];
    int visited_count = 0;

    for (int i = 0; i < n; i++) {
        dist[i] = INF;
        parent[i] = -1;
    }
    dist[source] = 0.0;

    for (int step = 0; step < n; step++) {
        double min_dist = INF;
        int u = -1;

        for (int i = 0; i < n; i++) {
            comparisons++;
            if (!visited[i] && dist[i] < min_dist) {
                min_dist = dist[i];
                u = i;
            }
        }

        if (u == -1 || min_dist >= INF) break;

        visited[u] = 1;
        visited_nodes_order[visited_count++] = u;

        if (u == destination) break; // Destination reached

        EdgeNode* edge = g->adj[u];
        while (edge) {
            comparisons++;
            if (edge->is_active && edge->dest >= 0 && edge->dest < n) {
                int v = edge->dest;
                double w = edge->weight;
                if (!visited[v] && dist[u] + w < dist[v]) {
                    dist[v] = dist[u] + w;
                    parent[v] = u;
                }
            }
            edge = edge->next;
        }
    }

    double end_t = get_high_res_time_us();

    out_result->execution_time_us = (end_t - start_t);
    out_result->comparisons = comparisons;
    out_result->visited_count = visited_count;
    for (int i = 0; i < visited_count; i++) {
        out_result->visited_nodes[i] = visited_nodes_order[i];
    }

    if (dist[destination] >= INF) {
        // No path exists
        out_result->total_path_len = 0;
        out_result->total_distance = -1.0;
        return 0;
    }

    // Reconstruct path
    int temp_path[MAX_VERTICES];
    int path_len = 0;
    int curr = destination;
    while (curr != -1) {
        temp_path[path_len++] = curr;
        curr = parent[curr];
    }

    // Reverse path into out_result
    out_result->total_path_len = path_len;
    out_result->total_distance = dist[destination];
    for (int i = 0; i < path_len; i++) {
        out_result->path[i] = temp_path[path_len - 1 - i];
    }

    return 1;
}
