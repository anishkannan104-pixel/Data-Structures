#include "common.h"

typedef struct LLNode {
    CShipment data;
    struct LLNode* next;
} LLNode;

static LLNode* g_ll_head = NULL;

EXPORT_API void ll_init(void) {
    LLNode* curr = g_ll_head;
    while (curr) {
        LLNode* temp = curr;
        curr = curr->next;
        free(temp);
    }
    g_ll_head = NULL;
}

EXPORT_API int ll_insert_head(const CShipment* s) {
    if (!s) return 0;
    LLNode* node = (LLNode*)malloc(sizeof(LLNode));
    if (!node) return 0;
    node->data = *s;
    node->next = g_ll_head;
    g_ll_head = node;
    return 1;
}

EXPORT_API int ll_insert_tail(const CShipment* s) {
    if (!s) return 0;
    LLNode* node = (LLNode*)malloc(sizeof(LLNode));
    if (!node) return 0;
    node->data = *s;
    node->next = NULL;

    if (!g_ll_head) {
        g_ll_head = node;
        return 1;
    }

    LLNode* curr = g_ll_head;
    while (curr->next) {
        curr = curr->next;
    }
    curr->next = node;
    return 1;
}

EXPORT_API int ll_delete_by_id(int id) {
    LLNode* curr = g_ll_head;
    LLNode* prev = NULL;

    while (curr) {
        if (curr->data.id == id) {
            if (prev) {
                prev->next = curr->next;
            } else {
                g_ll_head = curr->next;
            }
            free(curr);
            return 1;
        }
        prev = curr;
        curr = curr->next;
    }
    return 0;
}

EXPORT_API int ll_update(int id, double weight, double volume, int priority, int status) {
    LLNode* curr = g_ll_head;
    while (curr) {
        if (curr->data.id == id) {
            curr->data.weight = weight;
            curr->data.volume = volume;
            curr->data.priority = priority;
            curr->data.status = status;
            return 1;
        }
        curr = curr->next;
    }
    return 0;
}

EXPORT_API int ll_find(int id, CShipment* out_s) {
    LLNode* curr = g_ll_head;
    while (curr) {
        if (curr->data.id == id) {
            if (out_s) *out_s = curr->data;
            return 1;
        }
        curr = curr->next;
    }
    return 0;
}

EXPORT_API int ll_count(void) {
    int cnt = 0;
    LLNode* curr = g_ll_head;
    while (curr) {
        cnt++;
        curr = curr->next;
    }
    return cnt;
}

EXPORT_API int ll_get_all(CShipment* out_array, int max_count, int* out_count) {
    if (!out_array || !out_count) return 0;
    int cnt = 0;
    LLNode* curr = g_ll_head;
    while (curr && cnt < max_count) {
        out_array[cnt++] = curr->data;
        curr = curr->next;
    }
    *out_count = cnt;
    return cnt;
}
