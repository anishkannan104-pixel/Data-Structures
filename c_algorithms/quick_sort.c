#include "common.h"

// Criterion:
// 0: Shipment ID
// 1: Weight
// 2: Priority (descending: 5->1)
// 3: Deadline timestamp (ascending)
static inline int compare_shipments(const CShipment* a, const CShipment* b, int criterion, long long* comparisons) {
    if (comparisons) (*comparisons)++;
    switch (criterion) {
        case 0: // ID
            return (a->id < b->id) ? -1 : (a->id > b->id ? 1 : 0);
        case 1: // Weight
            return (a->weight < b->weight) ? -1 : (a->weight > b->weight ? 1 : 0);
        case 2: // Priority (higher priority first)
            return (a->priority > b->priority) ? -1 : (a->priority < b->priority ? 1 : 0);
        case 3: // Deadline (earliest first)
            return (a->deadline_timestamp < b->deadline_timestamp) ? -1 : (a->deadline_timestamp > b->deadline_timestamp ? 1 : 0);
        default:
            return (a->id < b->id) ? -1 : (a->id > b->id ? 1 : 0);
    }
}

static int partition(CShipment* arr, int low, int high, int criterion, long long* comparisons) {
    // Median-of-three or middle pivot to avoid O(N^2) on sorted data
    int mid = low + (high - low) / 2;
    CShipment pivot = arr[mid];
    arr[mid] = arr[high];
    arr[high] = pivot;

    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (compare_shipments(&arr[j], &pivot, criterion, comparisons) <= 0) {
            i++;
            CShipment temp = arr[i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
    }
    CShipment temp = arr[i + 1];
    arr[i + 1] = arr[high];
    arr[high] = temp;
    return i + 1;
}

static void quick_sort_rec(CShipment* arr, int low, int high, int criterion, long long* comparisons) {
    if (low < high) {
        int pi = partition(arr, low, high, criterion, comparisons);
        quick_sort_rec(arr, low, pi - 1, criterion, comparisons);
        quick_sort_rec(arr, pi + 1, high, criterion, comparisons);
    }
}

EXPORT_API void run_quick_sort(CShipment* arr, int n, int criterion, CPerformanceResult* out_result) {
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

    quick_sort_rec(arr, 0, n - 1, criterion, &comparisons);

    double end_t = get_high_res_time_us();
    if (out_result) {
        out_result->execution_time_us = end_t - start_t;
        out_result->comparisons = comparisons;
        out_result->operations = comparisons * 2; // Partition swaps + comparisons
    }
}

// Microbenchmark on pure integers for performance page
EXPORT_API void benchmark_quick_sort_ints(int* arr, int n, CPerformanceResult* out_result) {
    if (!arr || n <= 1) return;
    long long comparisons = 0;
    double start_t = get_high_res_time_us();

    // Standard int quicksort with median pivot
    int* stack = (int*)malloc(n * 2 * sizeof(int));
    int top = -1;
    stack[++top] = 0;
    stack[++top] = n - 1;

    while (top >= 0) {
        int high = stack[top--];
        int low = stack[top--];

        int mid = low + (high - low) / 2;
        int pivot = arr[mid];
        arr[mid] = arr[high];
        arr[high] = pivot;

        int i = low - 1;
        for (int j = low; j < high; j++) {
            comparisons++;
            if (arr[j] <= pivot) {
                i++;
                int t = arr[i]; arr[i] = arr[j]; arr[j] = t;
            }
        }
        int t = arr[i + 1]; arr[i + 1] = arr[high]; arr[high] = t;
        int pi = i + 1;

        if (pi - 1 > low) {
            stack[++top] = low;
            stack[++top] = pi - 1;
        }
        if (pi + 1 < high) {
            stack[++top] = pi + 1;
            stack[++top] = high;
        }
    }
    free(stack);

    double end_t = get_high_res_time_us();
    if (out_result) {
        out_result->execution_time_us = end_t - start_t;
        out_result->comparisons = comparisons;
        out_result->operations = comparisons * 2;
    }
}
