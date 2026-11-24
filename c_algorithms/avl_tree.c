#include "common.h"

typedef struct AVLNode {
    int key;
    CShipment data;
    int height;
    struct AVLNode* left;
    struct AVLNode* right;
} AVLNode;

static AVLNode* g_avl_root = NULL;

static int avl_node_height(AVLNode* n) {
    return n ? n->height : 0;
}

static int avl_max(int a, int b) {
    return (a > b) ? a : b;
}

static int avl_get_balance(AVLNode* n) {
    return n ? (avl_node_height(n->left) - avl_node_height(n->right)) : 0;
}

static AVLNode* avl_right_rotate(AVLNode* y) {
    AVLNode* x = y->left;
    AVLNode* T2 = x->right;

    x->right = y;
    y->left = T2;

    y->height = avl_max(avl_node_height(y->left), avl_node_height(y->right)) + 1;
    x->height = avl_max(avl_node_height(x->left), avl_node_height(x->right)) + 1;

    return x;
}

static AVLNode* avl_left_rotate(AVLNode* x) {
    AVLNode* y = x->right;
    AVLNode* T2 = y->left;

    y->left = x;
    x->right = T2;

    x->height = avl_max(avl_node_height(x->left), avl_node_height(x->right)) + 1;
    y->height = avl_max(avl_node_height(y->left), avl_node_height(y->right)) + 1;

    return y;
}

static void avl_free_subtree(AVLNode* node) {
    if (!node) return;
    avl_free_subtree(node->left);
    avl_free_subtree(node->right);
    free(node);
}

EXPORT_API void avl_clear(void) {
    avl_free_subtree(g_avl_root);
    g_avl_root = NULL;
}

static AVLNode* avl_insert_node(AVLNode* node, int key, const CShipment* s, int* rotations) {
    if (!node) {
        AVLNode* n = (AVLNode*)malloc(sizeof(AVLNode));
        if (!n) return NULL;
        n->key = key;
        if (s) n->data = *s;
        else memset(&n->data, 0, sizeof(CShipment));
        n->height = 1;
        n->left = n->right = NULL;
        return n;
    }

    if (key < node->key) {
        node->left = avl_insert_node(node->left, key, s, rotations);
    } else if (key > node->key) {
        node->right = avl_insert_node(node->right, key, s, rotations);
    } else {
        if (s) node->data = *s;
        return node;
    }

    node->height = 1 + avl_max(avl_node_height(node->left), avl_node_height(node->right));
    int balance = avl_get_balance(node);

    // Left Left Case
    if (balance > 1 && key < node->left->key) {
        if (rotations) (*rotations)++;
        return avl_right_rotate(node);
    }
    // Right Right Case
    if (balance < -1 && key > node->right->key) {
        if (rotations) (*rotations)++;
        return avl_left_rotate(node);
    }
    // Left Right Case
    if (balance > 1 && key > node->left->key) {
        if (rotations) (*rotations) += 2;
        node->left = avl_left_rotate(node->left);
        return avl_right_rotate(node);
    }
    // Right Left Case
    if (balance < -1 && key < node->right->key) {
        if (rotations) (*rotations) += 2;
        node->right = avl_right_rotate(node->right);
        return avl_left_rotate(node);
    }

    return node;
}

EXPORT_API int avl_insert(int key, const CShipment* s) {
    int rot = 0;
    g_avl_root = avl_insert_node(g_avl_root, key, s, &rot);
    return g_avl_root != NULL;
}

EXPORT_API int avl_search(int key, CShipment* out_s, long long* out_comparisons, double* out_time_us) {
    double start_t = get_high_res_time_us();
    long long comp = 0;
    AVLNode* curr = g_avl_root;
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

EXPORT_API int avl_height(void) {
    return avl_node_height(g_avl_root);
}

EXPORT_API int avl_get_structure(int* parents, int* children, int* is_left, int max_edges, int* out_edge_count) {
    if (!g_avl_root) {
        if (out_edge_count) *out_edge_count = 0;
        return 0;
    }
    AVLNode* queue[512];
    int front = 0, rear = 0;
    int edge_idx = 0;

    queue[rear++] = g_avl_root;
    while (front < rear && edge_idx < max_edges) {
        AVLNode* curr = queue[front++];
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
