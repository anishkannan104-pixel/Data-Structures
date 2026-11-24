#include "common.h"

#define MAX_PQ_CAPACITY 2048

static CShipment g_pq_heap[MAX_PQ_CAPACITY];
static int g_pq_size = 0;

EXPORT_API void pq_init(void) {
    g_pq_size = 0;
}

static inline int pq_compare(const CShipment* a, const CShipment* b) {
    // Higher priority comes first
    if (a->priority != b->priority) {
        return a->priority > b->priority ? 1 : -1;
    }
    // If priorities are equal, earliest deadline comes first
    if (a->deadline_timestamp != b->deadline_timestamp) {
        return a->deadline_timestamp < b->deadline_timestamp ? 1 : -1;
    }
    return 0;
}

static void pq_heapify_up(int idx) {
    while (idx > 0) {
        int parent = (idx - 1) / 2;
        if (pq_compare(&g_pq_heap[idx], &g_pq_heap[parent]) > 0) {
            CShipment temp = g_pq_heap[idx];
            g_pq_heap[idx] = g_pq_heap[parent];
            g_pq_heap[parent] = temp;
            idx = parent;
        } else {
            break;
        }
    }
}

static void pq_heapify_down(int idx) {
    while (1) {
        int left = 2 * idx + 1;
        int right = 2 * idx + 2;
        int largest = idx;

        if (left < g_pq_size && pq_compare(&g_pq_heap[left], &g_pq_heap[largest]) > 0) {
            largest = left;
        }
        if (right < g_pq_size && pq_compare(&g_pq_heap[right], &g_pq_heap[largest]) > 0) {
            largest = right;
        }

        if (largest != idx) {
            CShipment temp = g_pq_heap[idx];
            g_pq_heap[idx] = g_pq_heap[largest];
            g_pq_heap[largest] = temp;
            idx = largest;
        } else {
            break;
        }
    }
}

EXPORT_API int pq_insert(const CShipment* s) {
    if (!s || g_pq_size >= MAX_PQ_CAPACITY) return 0;
    g_pq_heap[g_pq_size] = *s;
    pq_heapify_up(g_pq_size);
    g_pq_size++;
    return 1;
}

EXPORT_API int pq_extract_max(CShipment* out_s) {
    if (g_pq_size <= 0) return 0;
    if (out_s) *out_s = g_pq_heap[0];

    g_pq_size--;
    if (g_pq_size > 0) {
        g_pq_heap[0] = g_pq_heap[g_pq_size];
        pq_heapify_down(0);
    }
    return 1;
}

EXPORT_API int pq_peek_max(CShipment* out_s) {
    if (g_pq_size <= 0) return 0;
    if (out_s) *out_s = g_pq_heap[0];
    return 1;
}

EXPORT_API int pq_size(void) {
    return g_pq_size;
}

EXPORT_API int pq_get_all(CShipment* out_array, int max_count, int* out_count) {
    if (!out_array || !out_count) return 0;
    int cnt = (g_pq_size < max_count) ? g_pq_size : max_count;
    for (int i = 0; i < cnt; i++) {
        out_array[i] = g_pq_heap[i];
    }
    *out_count = cnt;
    return cnt;
}
