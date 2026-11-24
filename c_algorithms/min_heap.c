#include "common.h"

#define MAX_MINHEAP_CAPACITY 2048

static CShipment g_min_heap[MAX_MINHEAP_CAPACITY];
static int g_min_heap_size = 0;

EXPORT_API void minheap_init(void) {
    g_min_heap_size = 0;
}

static inline int minheap_compare(const CShipment* a, const CShipment* b) {
    // Smallest deadline_timestamp comes first (min-heap)
    if (a->deadline_timestamp != b->deadline_timestamp) {
        return a->deadline_timestamp < b->deadline_timestamp ? 1 : -1;
    }
    // Tie-breaker: higher priority comes first
    return a->priority > b->priority ? 1 : -1;
}

static void minheap_heapify_up(int idx) {
    while (idx > 0) {
        int parent = (idx - 1) / 2;
        if (minheap_compare(&g_min_heap[idx], &g_min_heap[parent]) > 0) {
            CShipment temp = g_min_heap[idx];
            g_min_heap[idx] = g_min_heap[parent];
            g_min_heap[parent] = temp;
            idx = parent;
        } else {
            break;
        }
    }
}

static void minheap_heapify_down(int idx) {
    while (1) {
        int left = 2 * idx + 1;
        int right = 2 * idx + 2;
        int smallest = idx;

        if (left < g_min_heap_size && minheap_compare(&g_min_heap[left], &g_min_heap[smallest]) > 0) {
            smallest = left;
        }
        if (right < g_min_heap_size && minheap_compare(&g_min_heap[right], &g_min_heap[smallest]) > 0) {
            smallest = right;
        }

        if (smallest != idx) {
            CShipment temp = g_min_heap[idx];
            g_min_heap[idx] = g_min_heap[smallest];
            g_min_heap[smallest] = temp;
            idx = smallest;
        } else {
            break;
        }
    }
}

EXPORT_API int minheap_insert(const CShipment* s) {
    if (!s || g_min_heap_size >= MAX_MINHEAP_CAPACITY) return 0;
    g_min_heap[g_min_heap_size] = *s;
    minheap_heapify_up(g_min_heap_size);
    g_min_heap_size++;
    return 1;
}

EXPORT_API int minheap_extract_min(CShipment* out_s) {
    if (g_min_heap_size <= 0) return 0;
    if (out_s) *out_s = g_min_heap[0];

    g_min_heap_size--;
    if (g_min_heap_size > 0) {
        g_min_heap[0] = g_min_heap[g_min_heap_size];
        minheap_heapify_down(0);
    }
    return 1;
}

EXPORT_API int minheap_peek_min(CShipment* out_s) {
    if (g_min_heap_size <= 0) return 0;
    if (out_s) *out_s = g_min_heap[0];
    return 1;
}

EXPORT_API int minheap_size(void) {
    return g_min_heap_size;
}

EXPORT_API int minheap_get_all(CShipment* out_array, int max_count, int* out_count) {
    if (!out_array || !out_count) return 0;
    int cnt = (g_min_heap_size < max_count) ? g_min_heap_size : max_count;
    for (int i = 0; i < cnt; i++) {
        out_array[i] = g_min_heap[i];
    }
    *out_count = cnt;
    return cnt;
}

EXPORT_API int minheap_get_imminent(long long threshold_timestamp, CShipment* out_array, int max_count, int* out_count) {
    if (!out_array || !out_count) return 0;
    int cnt = 0;
    for (int i = 0; i < g_min_heap_size && cnt < max_count; i++) {
        if (g_min_heap[i].deadline_timestamp <= threshold_timestamp) {
            out_array[cnt++] = g_min_heap[i];
        }
    }
    *out_count = cnt;
    return cnt;
}
