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

static void merge(CShipment* arr, int l, int m, int r, CShipment* temp, int criterion, long long* comparisons) {
    int i = l;
    int j = m + 1;
    int k = l;

    while (i <= m && j <= r) {
        if (compare_shipments(&arr[i], &arr[j], criterion, comparisons) <= 0) {
            temp[k++] = arr[i++];
        } else {
            temp[k++] = arr[j++];
        }
    }
    while (i <= m) {
        temp[k++] = arr[i++];
    }
    while (j <= r) {
        temp[k++] = arr[j++];
    }
    for (i = l; i <= r; i++) {
        arr[i] = temp[i];
    }
}

static void merge_sort_rec(CShipment* arr, int l, int r, CShipment* temp, int criterion, long long* comparisons) {
    if (l < r) {
        int m = l + (r - l) / 2;
        merge_sort_rec(arr, l, m, temp, criterion, comparisons);
        merge_sort_rec(arr, m + 1, r, temp, criterion, comparisons);
        merge(arr, l, m, r, temp, criterion, comparisons);
    }
}

EXPORT_API void run_merge_sort(CShipment* arr, int n, int criterion, CPerformanceResult* out_result) {
    if (!arr || n <= 1) {
        if (out_result) {
            out_result->execution_time_us = 0.0;
            out_result->comparisons = 0;
            out_result->operations = 0;
        }
        return;
    }

    long long comparisons = 0;
    CShipment* temp = (CShipment*)malloc(n * sizeof(CShipment));
    if (!temp) return;

    double start_t = get_high_res_time_us();
    merge_sort_rec(arr, 0, n - 1, temp, criterion, &comparisons);
    double end_t = get_high_res_time_us();

    free(temp);
    if (out_result) {
        out_result->execution_time_us = end_t - start_t;
        out_result->comparisons = comparisons;
        out_result->operations = comparisons * 2;
    }
}

// Microbenchmark on pure integers for performance evaluation page
EXPORT_API void benchmark_merge_sort_ints(int* arr, int n, CPerformanceResult* out_result) {
    if (!arr || n <= 1) return;
    long long comparisons = 0;
    int* temp = (int*)malloc(n * sizeof(int));
    if (!temp) return;

    double start_t = get_high_res_time_us();
    for (int width = 1; width < n; width = 2 * width) {
        for (int i = 0; i < n; i = i + 2 * width) {
            int left = i;
            int mid = i + width;
            int right = i + 2 * width;
            if (mid > n) mid = n;
            if (right > n) right = n;

            int p1 = left, p2 = mid, k = left;
            while (p1 < mid && p2 < right) {
                comparisons++;
                if (arr[p1] <= arr[p2]) {
                    temp[k++] = arr[p1++];
                } else {
                    temp[k++] = arr[p2++];
                }
            }
            while (p1 < mid) temp[k++] = arr[p1++];
            while (p2 < right) temp[k++] = arr[p2++];
            for (int x = left; x < right; x++) arr[x] = temp[x];
        }
    }
    double end_t = get_high_res_time_us();
    free(temp);

    if (out_result) {
        out_result->execution_time_us = end_t - start_t;
        out_result->comparisons = comparisons;
        out_result->operations = comparisons * 2;
    }
}
