#include "common.h"

typedef struct SplayNode {
    int key;
    CShipment data;
    struct SplayNode* left;
    struct SplayNode* right;
} SplayNode;

static SplayNode* g_splay_root = NULL;

static void splay_free_subtree(SplayNode* node) {
    if (!node) return;
    splay_free_subtree(node->left);
    splay_free_subtree(node->right);
    free(node);
}

EXPORT_API void splay_clear(void) {
    splay_free_subtree(g_splay_root);
    g_splay_root = NULL;
}

static SplayNode* splay_right_rotate(SplayNode* x) {
    SplayNode* y = x->left;
    x->left = y->right;
    y->right = x;
    return y;
}

static SplayNode* splay_left_rotate(SplayNode* x) {
    SplayNode* y = x->right;
    x->right = y->left;
    y->left = x;
    return y;
}

// Splay operation: brings key to root if present, or brings the last accessed node to root
static SplayNode* splay_op(SplayNode* root, int key, long long* comparisons) {
    if (!root) return NULL;

    if (comparisons) (*comparisons)++;
    if (root->key == key) return root;

    // Key lies in left subtree
    if (key < root->key) {
        if (!root->left) return root;

        if (comparisons) (*comparisons)++;
        // Zig-Zig (Left Left)
        if (key < root->left->key) {
            root->left->left = splay_op(root->left->left, key, comparisons);
            root = splay_right_rotate(root);
        }
        // Zig-Zag (Left Right)
        else if (key > root->left->key) {
            root->left->right = splay_op(root->left->right, key, comparisons);
            if (root->left->right) {
                root->left = splay_left_rotate(root->left);
            }
        }

        return (root->left == NULL) ? root : splay_right_rotate(root);
    }
    // Key lies in right subtree
    else {
        if (!root->right) return root;

        if (comparisons) (*comparisons)++;
        // Zag-Zig (Right Left)
        if (key < root->right->key) {
            root->right->left = splay_op(root->right->left, key, comparisons);
            if (root->right->left) {
                root->right = splay_right_rotate(root->right);
            }
        }
        // Zag-Zag (Right Right)
        else if (key > root->right->key) {
            root->right->right = splay_op(root->right->right, key, comparisons);
            root = splay_left_rotate(root);
        }

        return (root->right == NULL) ? root : splay_left_rotate(root);
    }
}

EXPORT_API int splay_insert(int key, const CShipment* s) {
    if (!g_splay_root) {
        SplayNode* node = (SplayNode*)malloc(sizeof(SplayNode));
        if (!node) return 0;
        node->key = key;
        if (s) node->data = *s;
        else memset(&node->data, 0, sizeof(CShipment));
        node->left = node->right = NULL;
        g_splay_root = node;
        return 1;
    }

    long long comp = 0;
    g_splay_root = splay_op(g_splay_root, key, &comp);

    if (g_splay_root->key == key) {
        if (s) g_splay_root->data = *s;
        return 1;
    }

    SplayNode* node = (SplayNode*)malloc(sizeof(SplayNode));
    if (!node) return 0;
    node->key = key;
    if (s) node->data = *s;
    else memset(&node->data, 0, sizeof(CShipment));

    if (key < g_splay_root->key) {
        node->right = g_splay_root;
        node->left = g_splay_root->left;
        g_splay_root->left = NULL;
    } else {
        node->left = g_splay_root;
        node->right = g_splay_root->right;
        g_splay_root->right = NULL;
    }
    g_splay_root = node;
    return 1;
}

EXPORT_API int splay_search(int key, CShipment* out_s, long long* out_comparisons, double* out_time_us) {
    double start_t = get_high_res_time_us();
    long long comp = 0;
    int found = 0;

    g_splay_root = splay_op(g_splay_root, key, &comp);
    if (g_splay_root && g_splay_root->key == key) {
        found = 1;
        if (out_s) *out_s = g_splay_root->data;
    }

    double end_t = get_high_res_time_us();
    if (out_comparisons) *out_comparisons = comp;
    if (out_time_us) *out_time_us = (end_t - start_t);
    return found;
}

static int splay_calc_height(SplayNode* node) {
    if (!node) return 0;
    int lh = splay_calc_height(node->left);
    int rh = splay_calc_height(node->right);
    return (lh > rh ? lh : rh) + 1;
}

EXPORT_API int splay_height(void) {
    return splay_calc_height(g_splay_root);
}

EXPORT_API int splay_get_structure(int* parents, int* children, int* is_left, int max_edges, int* out_edge_count) {
    if (!g_splay_root) {
        if (out_edge_count) *out_edge_count = 0;
        return 0;
    }
    SplayNode* queue[512];
    int front = 0, rear = 0;
    int edge_idx = 0;

    queue[rear++] = g_splay_root;
    while (front < rear && edge_idx < max_edges) {
        SplayNode* curr = queue[front++];
        if (curr->left) {
            parents[edge_idx] = curr->key;
            children[edge_idx] = curr->left->key;
            is_left[edge_idx] = 1;
            edge_idx++;
            if (rear < 512) queue[rear++] = curr->left;
        }
        if (curr->right && edge_idx < max_edges) {
            parents[edge_idx] = curr->key;
            children[edge_idx] = curr->right->key;
            is_left[edge_idx] = 0;
            edge_idx++;
            if (rear < 512) queue[rear++] = curr->right;
        }
    }
    if (out_edge_count) *out_edge_count = edge_idx;
    return edge_idx;
}
