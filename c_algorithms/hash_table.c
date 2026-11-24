#include "common.h"

typedef struct HashNode {
    char key[MAX_CODE_LEN];
    CShipment data;
    struct HashNode* next;
} HashNode;

typedef struct {
    HashNode* buckets[HASH_TABLE_SIZE];
    int total_elements;
    int collision_count;
} HashTable;

static HashTable g_hash_table;

// Polynomial rolling hash function (djb2 variant)
static unsigned int hash_function(const char* str) {
    unsigned long hash = 5381;
    int c;
    while ((c = (unsigned char)*str++)) {
        hash = ((hash << 5) + hash) + c; /* hash * 33 + c */
    }
    return (unsigned int)(hash % HASH_TABLE_SIZE);
}

EXPORT_API void hash_init(void) {
    for (int i = 0; i < HASH_TABLE_SIZE; i++) {
        HashNode* curr = g_hash_table.buckets[i];
        while (curr) {
            HashNode* temp = curr;
            curr = curr->next;
            free(temp);
        }
        g_hash_table.buckets[i] = NULL;
    }
    g_hash_table.total_elements = 0;
    g_hash_table.collision_count = 0;
}

EXPORT_API int hash_insert(const char* key, const CShipment* s, int* is_duplicate) {
    if (!key || !*key) return 0;
    unsigned int idx = hash_function(key);

    // Check for duplicate in the chain
    HashNode* curr = g_hash_table.buckets[idx];
    while (curr) {
        if (strcmp(curr->key, key) == 0) {
            if (is_duplicate) *is_duplicate = 1;
            if (s) curr->data = *s;
            return 0; // Duplicate detected
        }
        curr = curr->next;
    }

    if (is_duplicate) *is_duplicate = 0;

    // If bucket was already occupied, this is a collision
    if (g_hash_table.buckets[idx] != NULL) {
        g_hash_table.collision_count++;
    }

    HashNode* new_node = (HashNode*)malloc(sizeof(HashNode));
    if (!new_node) return 0;

    strncpy(new_node->key, key, MAX_CODE_LEN - 1);
    new_node->key[MAX_CODE_LEN - 1] = '\0';
    if (s) new_node->data = *s;
    else memset(&new_node->data, 0, sizeof(CShipment));

    new_node->next = g_hash_table.buckets[idx];
    g_hash_table.buckets[idx] = new_node;
    g_hash_table.total_elements++;
    return 1;
}

EXPORT_API int hash_search(const char* key, CShipment* out_s, long long* out_comparisons, double* out_time_us) {
    double start_t = get_high_res_time_us();
    long long comp = 0;
    int found = 0;

    if (key && *key) {
        unsigned int idx = hash_function(key);
        HashNode* curr = g_hash_table.buckets[idx];
        while (curr) {
            comp++;
            if (strcmp(curr->key, key) == 0) {
                found = 1;
                if (out_s) *out_s = curr->data;
                break;
            }
            curr = curr->next;
        }
    }

    double end_t = get_high_res_time_us();
    if (out_comparisons) *out_comparisons = comp;
    if (out_time_us) *out_time_us = (end_t - start_t);
    return found;
}

EXPORT_API int hash_get_stats(int* total_elements, int* collision_count, int* bucket_lengths, int max_buckets) {
    if (total_elements) *total_elements = g_hash_table.total_elements;
    if (collision_count) *collision_count = g_hash_table.collision_count;

    int n = (HASH_TABLE_SIZE < max_buckets) ? HASH_TABLE_SIZE : max_buckets;
    if (bucket_lengths) {
        for (int i = 0; i < n; i++) {
            int len = 0;
            HashNode* curr = g_hash_table.buckets[i];
            while (curr) {
                len++;
                curr = curr->next;
            }
            bucket_lengths[i] = len;
        }
    }
    return HASH_TABLE_SIZE;
}

EXPORT_API int hash_get_bucket_entries(int bucket_idx, char* out_keys_flat, int max_entries, int* out_count) {
    if (bucket_idx < 0 || bucket_idx >= HASH_TABLE_SIZE || !out_keys_flat || !out_count) return 0;
    int cnt = 0;
    HashNode* curr = g_hash_table.buckets[bucket_idx];
    while (curr && cnt < max_entries) {
        strncpy(&out_keys_flat[cnt * MAX_CODE_LEN], curr->key, MAX_CODE_LEN - 1);
        out_keys_flat[cnt * MAX_CODE_LEN + (MAX_CODE_LEN - 1)] = '\0';
        cnt++;
        curr = curr->next;
    }
    *out_count = cnt;
    return cnt;
}
