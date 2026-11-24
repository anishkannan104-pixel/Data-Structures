#include "common.h"

static inline int compare_shipments(const CShipment* a, const CShipment* b, int criterion, long long* comparisons) {
    if (comparisons) (*comparisons)++;
    switch (criterion) {
        case 0: return (a->id < b->id) ? -1 : (a->id > b->id ? 1 : 0);
        case 1: return (a->weight < b->weight) ? -1 : (a->weight > b->weight ? 1 : 0);
        case 2: return (a->priority > b->priority) ? -1 : (a->priority < b->priority ? 1 : 0);
        case 3: return (a->deadline_timestamp < b->deadline_timestamp) ? -1 : (a->deadline_timestamp > b->deadline_timestamp ? 1 : 0);
        default: return (a->id < b->id) ? -1 : (a->id > b->id ? 1 : 0);
    }
}

static void heapify(CShipment* arr, int n, int i, int criterion, long long* comparisons) {
    int largest = i;
    int l = 2 * i + 1;
    int r = 2 * i + 2;

    if (l < n && compare_shipments(&arr[l], &arr[largest], criterion, comparisons) > 0) {
        largest = l;
    }

    if (r < n && compare_shipments(&arr[r], &arr[largest], criterion, comparisons) > 0) {
        largest = r;
    }

    if (largest != i) {
        CShipment swap = arr[i];
        arr[i] = arr[largest];
        arr[largest] = swap;
        heapify(arr, n, largest, criterion, comparisons);
    }
}

EXPORT_API void run_heap_sort(CShipment* arr, int n, int criterion, CPerformanceResult* out_result) {
    if (!arr || n <= 1) {
        if (out_result) {
            out_result->execution_time_us = 0.0;
            out_result->comparisons = 0;
            out_result->operations = 0;
        }
        return;
    }

    long long comparisons = 0;
    double start_t = get_high_res_time_us();

    // Build max-heap
    for (int i = n / 2 - 1; i >= 0; i--) {
        heapify(arr, n, i, criterion, &comparisons);
    }

    // One by one extract an element from heap
    for (int i = n - 1; i > 0; i--) {
        CShipment temp = arr[0];
        arr[0] = arr[i];
        arr[i] = temp;
        heapify(arr, i, 0, criterion, &comparisons);
    }

    double end_t = get_high_res_time_us();
    if (out_result) {
        out_result->execution_time_us = end_t - start_t;
        out_result->comparisons = comparisons;
        out_result->operations = comparisons * 2;
    }
}

// Microbenchmark on pure integers for performance evaluation page
static void heapify_ints(int* arr, int n, int i, long long* comparisons) {
    int largest = i;
    int l = 2 * i + 1;
    int r = 2 * i + 2;

    if (l < n) {
        (*comparisons)++;
        if (arr[l] > arr[largest]) largest = l;
    }
    if (r < n) {
        (*comparisons)++;
        if (arr[r] > arr[largest]) largest = r;
    }

    if (largest != i) {
        int swap = arr[i];
        arr[i] = arr[largest];
        arr[largest] = swap;
        heapify_ints(arr, n, largest, comparisons);
    }
}

EXPORT_API void benchmark_heap_sort_ints(int* arr, int n, CPerformanceResult* out_result) {
    if (!arr || n <= 1) return;
    long long comparisons = 0;
    double start_t = get_high_res_time_us();

    for (int i = n / 2 - 1; i >= 0; i--) {
        heapify_ints(arr, n, i, &comparisons);
    }
    for (int i = n - 1; i > 0; i--) {
        int temp = arr[0];
        arr[0] = arr[i];
        arr[i] = temp;
        heapify_ints(arr, i, 0, &comparisons);
    }

    double end_t = get_high_res_time_us();
    if (out_result) {
        out_result->execution_time_us = end_t - start_t;
        out_result->comparisons = comparisons;
        out_result->operations = comparisons * 2;
    }
}
