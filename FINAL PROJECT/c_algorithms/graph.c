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

static CGraph g_graph;

EXPORT_API void graph_init(void) {
    for (int i = 0; i < MAX_VERTICES; i++) {
        EdgeNode* curr = g_graph.adj[i];
        while (curr) {
            EdgeNode* temp = curr;
            curr = curr->next;
            free(temp);
        }
        g_graph.adj[i] = NULL;
    }
    g_graph.vertex_count = 0;
    g_graph.edge_count = 0;
}

EXPORT_API int graph_add_location(int id, const char* name, const char* code, double x, double y) {
    if (id < 0 || id >= MAX_VERTICES) return 0;
    g_graph.locations[id].id = id;
    strncpy(g_graph.locations[id].name, name ? name : "", MAX_NAME_LEN - 1);
    g_graph.locations[id].name[MAX_NAME_LEN - 1] = '\0';
    strncpy(g_graph.locations[id].code, code ? code : "", 15);
    g_graph.locations[id].code[15] = '\0';
    g_graph.locations[id].x_coord = x;
    g_graph.locations[id].y_coord = y;

    if (id >= g_graph.vertex_count) {
        g_graph.vertex_count = id + 1;
    }
    return 1;
}

static void add_directed_edge(int u, int v, double weight, int road_id, int is_active) {
    EdgeNode* node = (EdgeNode*)malloc(sizeof(EdgeNode));
    if (!node) return;
    node->dest = v;
    node->weight = weight;
    node->road_id = road_id;
    node->is_active = is_active;
    node->next = g_graph.adj[u];
    g_graph.adj[u] = node;
}

EXPORT_API int graph_add_road(int u, int v, double distance, int road_id, int is_active) {
    if (u < 0 || u >= MAX_VERTICES || v < 0 || v >= MAX_VERTICES) return 0;

    // Add bidirectional edge
    add_directed_edge(u, v, distance, road_id, is_active);
    add_directed_edge(v, u, distance, road_id, is_active);
    g_graph.edge_count++;
    return 1;
}

EXPORT_API int graph_update_road_weight(int road_id, double new_weight) {
    int updated = 0;
    for (int i = 0; i < g_graph.vertex_count; i++) {
        EdgeNode* curr = g_graph.adj[i];
        while (curr) {
            if (curr->road_id == road_id) {
                curr->weight = new_weight;
                updated = 1;
            }
            curr = curr->next;
        }
    }
    return updated;
}

EXPORT_API int graph_set_road_active(int road_id, int is_active) {
    int updated = 0;
    for (int i = 0; i < g_graph.vertex_count; i++) {
        EdgeNode* curr = g_graph.adj[i];
        while (curr) {
            if (curr->road_id == road_id) {
                curr->is_active = is_active;
                updated = 1;
            }
            curr = curr->next;
        }
    }
    return updated;
}

EXPORT_API int graph_get_vertex_count(void) {
    return g_graph.vertex_count;
}

EXPORT_API int graph_get_location(int id, CLocation* out_loc) {
    if (id < 0 || id >= g_graph.vertex_count || !out_loc) return 0;
    *out_loc = g_graph.locations[id];
    return 1;
}

EXPORT_API int graph_get_all_roads(CRoad* out_roads, int max_roads, int* out_count) {
    if (!out_roads || !out_count) return 0;
    int count = 0;

    for (int u = 0; u < g_graph.vertex_count && count < max_roads; u++) {
        EdgeNode* curr = g_graph.adj[u];
        while (curr && count < max_roads) {
            if (u < curr->dest) { // record each undirected road once
                out_roads[count].source_id = u;
                out_roads[count].dest_id = curr->dest;
                out_roads[count].distance_km = curr->weight;
                out_roads[count].road_id = curr->road_id;
                out_roads[count].is_active = curr->is_active;
                count++;
            }
            curr = curr->next;
        }
    }
    *out_count = count;
    return count;
}

// Internal pointer accessor for BFS, DFS, Dijkstra, Prim, Kruskal
CGraph* get_global_graph_internal(void) {
    return &g_graph;
}
