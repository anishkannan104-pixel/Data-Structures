#include "common.h"

#define RB_RED 0
#define RB_BLACK 1

typedef struct RBNode {
    int key;
    CShipment data;
    int color;
    struct RBNode* left;
    struct RBNode* right;
    struct RBNode* parent;
} RBNode;

static RBNode* g_rb_root = NULL;

static void rb_free_subtree(RBNode* node) {
    if (!node) return;
    rb_free_subtree(node->left);
    rb_free_subtree(node->right);
    free(node);
}

EXPORT_API void rb_clear(void) {
    rb_free_subtree(g_rb_root);
    g_rb_root = NULL;
}

static void rb_left_rotate(RBNode* x) {
    RBNode* y = x->right;
    x->right = y->left;
    if (y->left) y->left->parent = x;
    y->parent = x->parent;

    if (!x->parent) {
        g_rb_root = y;
    } else if (x == x->parent->left) {
        x->parent->left = y;
    } else {
        x->parent->right = y;
    }
    y->left = x;
    x->parent = y;
}

static void rb_right_rotate(RBNode* y) {
    RBNode* x = y->left;
    y->left = x->right;
    if (x->right) x->right->parent = y;
    x->parent = y->parent;

    if (!y->parent) {
        g_rb_root = x;
    } else if (y == y->parent->right) {
        y->parent->right = x;
    } else {
        y->parent->left = x;
    }
    x->right = y;
    y->parent = x;
}

static void rb_insert_fixup(RBNode* z) {
    while (z->parent && z->parent->color == RB_RED) {
        if (z->parent == z->parent->parent->left) {
            RBNode* y = z->parent->parent->right;
            if (y && y->color == RB_RED) {
                z->parent->color = RB_BLACK;
                y->color = RB_BLACK;
                z->parent->parent->color = RB_RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->right) {
                    z = z->parent;
                    rb_left_rotate(z);
                }
                z->parent->color = RB_BLACK;
                z->parent->parent->color = RB_RED;
                rb_right_rotate(z->parent->parent);
            }
        } else {
            RBNode* y = z->parent->parent->left;
            if (y && y->color == RB_RED) {
                z->parent->color = RB_BLACK;
                y->color = RB_BLACK;
                z->parent->parent->color = RB_RED;
                z = z->parent->parent;
            } else {
                if (z == z->parent->left) {
                    z = z->parent;
                    rb_right_rotate(z);
                }
                z->parent->color = RB_BLACK;
                z->parent->parent->color = RB_RED;
                rb_left_rotate(z->parent->parent);
            }
        }
        if (z == g_rb_root) break;
    }
    g_rb_root->color = RB_BLACK;
}

EXPORT_API int rb_insert(int key, const CShipment* s) {
    RBNode* z = (RBNode*)malloc(sizeof(RBNode));
    if (!z) return 0;
    z->key = key;
    if (s) z->data = *s;
    else memset(&z->data, 0, sizeof(CShipment));
    z->color = RB_RED;
    z->left = z->right = z->parent = NULL;

    RBNode* y = NULL;
    RBNode* x = g_rb_root;

    while (x) {
        y = x;
        if (z->key < x->key) {
            x = x->left;
        } else if (z->key > x->key) {
            x = x->right;
        } else {
            // Key already exists, update data
            if (s) x->data = *s;
            free(z);
            return 1;
        }
    }

    z->parent = y;
    if (!y) {
        g_rb_root = z;
    } else if (z->key < y->key) {
        y->left = z;
    } else {
        y->right = z;
    }

    rb_insert_fixup(z);
    return 1;
}

EXPORT_API int rb_search(int key, CShipment* out_s, long long* out_comparisons, double* out_time_us) {
    double start_t = get_high_res_time_us();
    long long comp = 0;
    RBNode* curr = g_rb_root;
    int found = 0;

    while (curr) {
        comp++;
        if (key == curr->key) {
            found = 1;
            if (out_s) *out_s = curr->data;
            break;
        } else if (key < curr->key) {
            curr = curr->left;
        } else {
            curr = curr->right;
        }
    }

    double end_t = get_high_res_time_us();
    if (out_comparisons) *out_comparisons = comp;
    if (out_time_us) *out_time_us = (end_t - start_t);
    return found;
}

static int rb_calc_height(RBNode* node) {
    if (!node) return 0;
    int lh = rb_calc_height(node->left);
    int rh = rb_calc_height(node->right);
    return (lh > rh ? lh : rh) + 1;
}

EXPORT_API int rb_height(void) {
    return rb_calc_height(g_rb_root);
}

EXPORT_API int rb_get_structure(int* parents, int* children, int* is_left, int* colors, int max_edges, int* out_edge_count) {
    if (!g_rb_root) {
        if (out_edge_count) *out_edge_count = 0;
        return 0;
    }
    RBNode* queue[512];
    int front = 0, rear = 0;
    int edge_idx = 0;

    queue[rear++] = g_rb_root;
    while (front < rear && edge_idx < max_edges) {
        RBNode* curr = queue[front++];
        if (curr->left) {
            parents[edge_idx] = curr->key;
            children[edge_idx] = curr->left->key;
            is_left[edge_idx] = 1;
            colors[edge_idx] = curr->left->color;
            edge_idx++;
            if (rear < 512) queue[rear++] = curr->left;
        }
        if (curr->right && edge_idx < max_edges) {
            parents[edge_idx] = curr->key;
            children[edge_idx] = curr->right->key;
            is_left[edge_idx] = 0;
            colors[edge_idx] = curr->right->color;
            edge_idx++;
            if (rear < 512) queue[rear++] = curr->right;
        }
    }
    if (out_edge_count) *out_edge_count = edge_idx;
    return edge_idx;
}
