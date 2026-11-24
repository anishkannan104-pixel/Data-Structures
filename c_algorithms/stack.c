#include "common.h"

typedef struct StackItem {
    int action_id;
    char action_name[32];
    int shipment_id;
    long long timestamp;
    char details[128];
    struct StackItem* next;
} StackItem;

static StackItem* g_stack_top = NULL;
static int g_stack_count = 0;

EXPORT_API void stack_init(void) {
    StackItem* curr = g_stack_top;
    while (curr) {
        StackItem* temp = curr;
        curr = curr->next;
        free(temp);
    }
    g_stack_top = NULL;
    g_stack_count = 0;
}

EXPORT_API int stack_push(int action_id, const char* action_name, int shipment_id, long long timestamp, const char* details) {
    StackItem* item = (StackItem*)malloc(sizeof(StackItem));
    if (!item) return 0;

    item->action_id = action_id;
    strncpy(item->action_name, action_name ? action_name : "", sizeof(item->action_name) - 1);
    item->action_name[sizeof(item->action_name) - 1] = '\0';

    item->shipment_id = shipment_id;
    item->timestamp = timestamp;

    strncpy(item->details, details ? details : "", sizeof(item->details) - 1);
    item->details[sizeof(item->details) - 1] = '\0';

    item->next = g_stack_top;
    g_stack_top = item;
    g_stack_count++;
    return 1;
}

EXPORT_API int stack_pop(int* out_action_id, char* out_action_name, int* out_shipment_id, long long* out_timestamp, char* out_details) {
    if (!g_stack_top) return 0;

    StackItem* top = g_stack_top;
    if (out_action_id) *out_action_id = top->action_id;
    if (out_action_name) strcpy(out_action_name, top->action_name);
    if (out_shipment_id) *out_shipment_id = top->shipment_id;
    if (out_timestamp) *out_timestamp = top->timestamp;
    if (out_details) strcpy(out_details, top->details);

    g_stack_top = top->next;
    free(top);
    g_stack_count--;
    return 1;
}

EXPORT_API int stack_peek(int* out_action_id, char* out_action_name, int* out_shipment_id, long long* out_timestamp, char* out_details) {
    if (!g_stack_top) return 0;

    StackItem* top = g_stack_top;
    if (out_action_id) *out_action_id = top->action_id;
    if (out_action_name) strcpy(out_action_name, top->action_name);
    if (out_shipment_id) *out_shipment_id = top->shipment_id;
    if (out_timestamp) *out_timestamp = top->timestamp;
    if (out_details) strcpy(out_details, top->details);

    return 1;
}

EXPORT_API int stack_size(void) {
    return g_stack_count;
}
