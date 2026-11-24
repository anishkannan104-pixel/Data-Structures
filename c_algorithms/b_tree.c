#include "common.h"

// B-Tree with minimum degree T = 2 (2-3-4 tree)
// Max keys per node = 2*T - 1 = 3
// Max children = 2*T = 4
#define BTREE_T 2
#define MAX_KEYS (2 * BTREE_T - 1)
#define MAX_CHILDREN (2 * BTREE_T)

typedef struct BTreeNode {
    int n; // current number of keys
    int keys[MAX_KEYS];
    CShipment data[MAX_KEYS];
    struct BTreeNode* children[MAX_CHILDREN];
    int leaf;
} BTreeNode;

static BTreeNode* g_btree_root = NULL;

static BTreeNode* btree_create_node(int leaf) {
    BTreeNode* node = (BTreeNode*)malloc(sizeof(BTreeNode));
    if (!node) return NULL;
    node->n = 0;
    node->leaf = leaf;
    for (int i = 0; i < MAX_CHILDREN; i++) {
        node->children[i] = NULL;
    }
    return node;
}

static void btree_free_subtree(BTreeNode* node) {
    if (!node) return;
    if (!node->leaf) {
        for (int i = 0; i <= node->n; i++) {
            btree_free_subtree(node->children[i]);
        }
    }
    free(node);
}

EXPORT_API void btree_clear(void) {
    btree_free_subtree(g_btree_root);
    g_btree_root = NULL;
}

static void btree_split_child(BTreeNode* x, int i, BTreeNode* y) {
    BTreeNode* z = btree_create_node(y->leaf);
    z->n = BTREE_T - 1;

    for (int j = 0; j < BTREE_T - 1; j++) {
        z->keys[j] = y->keys[j + BTREE_T];
        z->data[j] = y->data[j + BTREE_T];
    }

    if (!y->leaf) {
        for (int j = 0; j < BTREE_T; j++) {
            z->children[j] = y->children[j + BTREE_T];
        }
    }

    y->n = BTREE_T - 1;

    for (int j = x->n; j >= i + 1; j--) {
        x->children[j + 1] = x->children[j];
    }
    x->children[i + 1] = z;

    for (int j = x->n - 1; j >= i; j--) {
        x->keys[j + 1] = x->keys[j];
        x->data[j + 1] = x->data[j];
    }

    x->keys[i] = y->keys[BTREE_T - 1];
    x->data[i] = y->data[BTREE_T - 1];
    x->n++;
}

static void btree_insert_non_full(BTreeNode* x, int key, const CShipment* s) {
    int i = x->n - 1;

    if (x->leaf) {
        while (i >= 0 && key < x->keys[i]) {
            x->keys[i + 1] = x->keys[i];
            x->data[i + 1] = x->data[i];
            i--;
        }
        if (i >= 0 && key == x->keys[i]) {
            if (s) x->data[i] = *s;
            return;
        }
        x->keys[i + 1] = key;
        if (s) x->data[i + 1] = *s;
        else memset(&x->data[i + 1], 0, sizeof(CShipment));
        x->n++;
    } else {
        while (i >= 0 && key < x->keys[i]) {
            i--;
        }
        if (i >= 0 && key == x->keys[i]) {
            if (s) x->data[i] = *s;
            return;
        }
        i++;
        if (x->children[i]->n == MAX_KEYS) {
            btree_split_child(x, i, x->children[i]);
            if (key > x->keys[i]) {
                i++;
            }
        }
        btree_insert_non_full(x->children[i], key, s);
    }
}

EXPORT_API int btree_insert(int key, const CShipment* s) {
    if (!g_btree_root) {
        g_btree_root = btree_create_node(1);
        if (!g_btree_root) return 0;
        g_btree_root->keys[0] = key;
        if (s) g_btree_root->data[0] = *s;
        else memset(&g_btree_root->data[0], 0, sizeof(CShipment));
        g_btree_root->n = 1;
        return 1;
    }

    if (g_btree_root->n == MAX_KEYS) {
        BTreeNode* s_node = btree_create_node(0);
        s_node->children[0] = g_btree_root;
        btree_split_child(s_node, 0, g_btree_root);
        int i = 0;
        if (s_node->keys[0] < key) {
            i++;
        }
        btree_insert_non_full(s_node->children[i], key, s);
        g_btree_root = s_node;
    } else {
        btree_insert_non_full(g_btree_root, key, s);
    }
    return 1;
}

static int btree_search_node(BTreeNode* x, int key, CShipment* out_s, long long* comparisons) {
    int i = 0;
    while (i < x->n) {
        (*comparisons)++;
        if (key <= x->keys[i]) break;
        i++;
    }

    if (i < x->n && key == x->keys[i]) {
        if (out_s) *out_s = x->data[i];
        return 1;
    }

    if (x->leaf) return 0;
    return btree_search_node(x->children[i], key, out_s, comparisons);
}

EXPORT_API int btree_search(int key, CShipment* out_s, long long* out_comparisons, double* out_time_us) {
    double start_t = get_high_res_time_us();
    long long comp = 0;
    int found = 0;

    if (g_btree_root) {
        found = btree_search_node(g_btree_root, key, out_s, &comp);
    }

    double end_t = get_high_res_time_us();
    if (out_comparisons) *out_comparisons = comp;
    if (out_time_us) *out_time_us = (end_t - start_t);
    return found;
}

static int btree_calc_height(BTreeNode* node) {
    if (!node) return 0;
    if (node->leaf) return 1;
    return 1 + btree_calc_height(node->children[0]);
}

EXPORT_API int btree_height(void) {
    return btree_calc_height(g_btree_root);
}
