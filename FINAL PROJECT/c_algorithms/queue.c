#include "common.h"

typedef struct QueueItem {
    CShipment data;
    struct QueueItem* next;
} QueueItem;

static QueueItem* g_queue_front = NULL;
static QueueItem* g_queue_rear = NULL;
static int g_queue_count = 0;

EXPORT_API void queue_init(void) {
    QueueItem* curr = g_queue_front;
    while (curr) {
        QueueItem* temp = curr;
        curr = curr->next;
        free(temp);
    }
    g_queue_front = NULL;
    g_queue_rear = NULL;
    g_queue_count = 0;
}

EXPORT_API int queue_enqueue(const CShipment* s) {
    if (!s) return 0;
    QueueItem* node = (QueueItem*)malloc(sizeof(QueueItem));
    if (!node) return 0;
    node->data = *s;
    node->next = NULL;

    if (!g_queue_rear) {
        g_queue_front = g_queue_rear = node;
    } else {
        g_queue_rear->next = node;
        g_queue_rear = node;
    }
    g_queue_count++;
    return 1;
}

EXPORT_API int queue_dequeue(CShipment* out_s) {
    if (!g_queue_front) return 0;

    QueueItem* temp = g_queue_front;
    if (out_s) *out_s = temp->data;

    g_queue_front = g_queue_front->next;
    if (!g_queue_front) {
        g_queue_rear = NULL;
    }
    free(temp);
    g_queue_count--;
    return 1;
}

EXPORT_API int queue_peek(CShipment* out_s) {
    if (!g_queue_front) return 0;
    if (out_s) *out_s = g_queue_front->data;
    return 1;
}

EXPORT_API int queue_size(void) {
    return g_queue_count;
}

EXPORT_API int queue_get_all(CShipment* out_array, int max_count, int* out_count) {
    if (!out_array || !out_count) return 0;
    int cnt = 0;
    QueueItem* curr = g_queue_front;
    while (curr && cnt < max_count) {
        out_array[cnt++] = curr->data;
        curr = curr->next;
    }
    *out_count = cnt;
    return cnt;
}
