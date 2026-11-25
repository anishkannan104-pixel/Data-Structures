#include "common.h"

typedef struct BSTNode {
    int key;
    CShipment data;
    struct BSTNode* left;
    struct BSTNode* right;
} BSTNode;

static BSTNode* g_bst_root = NULL;

static void bst_free_subtree(BSTNode* node) {
    if (!node) return;
    bst_free_subtree(node->left);
    bst_free_subtree(node->right);
    free(node);
}

EXPORT_API void bst_clear(void) {
    bst_free_subtree(g_bst_root);
    g_bst_root = NULL;
}

static BSTNode* bst_insert_node(BSTNode* root, int key, const CShipment* s, long long* comparisons) {
    if (!root) {
        BSTNode* node = (BSTNode*)malloc(sizeof(BSTNode));
        if (!node) return NULL;
        node->key = key;
        if (s) node->data = *s;
        else memset(&node->data, 0, sizeof(CShipment));
        node->left = node->right = NULL;
        return node;
    }

    if (comparisons) (*comparisons)++;
    if (key < root->key) {
        root->left = bst_insert_node(root->left, key, s, comparisons);
    } else if (key > root->key) {
        root->right = bst_insert_node(root->right, key, s, comparisons);
    } else {
        if (s) root->data = *s;
    }
    return root;
}

EXPORT_API int bst_insert(int key, const CShipment* s) {
    long long comp = 0;
    g_bst_root = bst_insert_node(g_bst_root, key, s, &comp);
    return g_bst_root != NULL;
}

EXPORT_API int bst_search(int key, CShipment* out_s, long long* out_comparisons, double* out_time_us) {
    double start_t = get_high_res_time_us();
    long long comp = 0;
    BSTNode* curr = g_bst_root;
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

static BSTNode* bst_min_node(BSTNode* node) {
    BSTNode* curr = node;
    while (curr && curr->left) {
        curr = curr->left;
    }
    return curr;
}

static BSTNode* bst_delete_node(BSTNode* root, int key) {
    if (!root) return NULL;

    if (key < root->key) {
        root->left = bst_delete_node(root->left, key);
    } else if (key > root->key) {
        root->right = bst_delete_node(root->right, key);
    } else {
        if (!root->left) {
            BSTNode* temp = root->right;
            free(root);
            return temp;
        } else if (!root->right) {
            BSTNode* temp = root->left;
            free(root);
            return temp;
        }

        BSTNode* temp = bst_min_node(root->right);
        root->key = temp->key;
        root->data = temp->data;
        root->right = bst_delete_node(root->right, temp->key);
    }
    return root;
}

EXPORT_API int bst_delete(int key) {
    long long comp = 0;
    double t = 0.0;
    if (!bst_search(key, NULL, &comp, &t)) return 0;
    g_bst_root = bst_delete_node(g_bst_root, key);
    return 1;
}

static int bst_calc_height(BSTNode* node) {
    if (!node) return 0;
    int lh = bst_calc_height(node->left);
    int rh = bst_calc_height(node->right);
    return (lh > rh ? lh : rh) + 1;
}

EXPORT_API int bst_height(void) {
    return bst_calc_height(g_bst_root);
}

static void bst_inorder_traverse(BSTNode* node, int* out_keys, int max_count, int* count) {
    if (!node || *count >= max_count) return;
    bst_inorder_traverse(node->left, out_keys, max_count, count);
    if (*count < max_count) {
        out_keys[(*count)++] = node->key;
    }
    bst_inorder_traverse(node->right, out_keys, max_count, count);
}

EXPORT_API int bst_get_inorder(int* out_keys, int max_count, int* out_count) {
    int cnt = 0;
    bst_inorder_traverse(g_bst_root, out_keys, max_count, &cnt);
    if (out_count) *out_count = cnt;
    return cnt;
}

// Tree structure serialization for graphical visualization: returns arrays of (parent, child, direction)
EXPORT_API int bst_get_structure(int* parents, int* children, int* is_left, int max_edges, int* out_edge_count) {
    if (!g_bst_root) {
        if (out_edge_count) *out_edge_count = 0;
        return 0;
    }
    BSTNode* queue[512];
    int front = 0, rear = 0;
    int edge_idx = 0;

    queue[rear++] = g_bst_root;
    while (front < rear && edge_idx < max_edges) {
        BSTNode* curr = queue[front++];
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
