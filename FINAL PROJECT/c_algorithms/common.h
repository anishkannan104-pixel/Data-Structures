#ifndef COMMON_H
#define COMMON_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#define EXPORT_API __declspec(dllexport)
#else
#define EXPORT_API __attribute__((visibility("default")))
#endif

#define MAX_CODE_LEN 32
#define MAX_NAME_LEN 64
#define MAX_VERTICES 64
#define MAX_EDGES 256
#define HASH_TABLE_SIZE 37

// High precision timing function returning microseconds
static inline double get_high_res_time_us(void) {
#ifdef _WIN32
    static LARGE_INTEGER freq;
    static int initialized = 0;
    if (!initialized) {
        QueryPerformanceFrequency(&freq);
        initialized = 1;
    }
    LARGE_INTEGER counter;
    QueryPerformanceCounter(&counter);
    return (double)(counter.QuadPart * 1000000.0 / freq.QuadPart);
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)(ts.tv_sec * 1000000.0 + ts.tv_nsec / 1000.0);
#endif
}

// Common C Structures exported to Python ctypes
#pragma pack(push, 1)

typedef struct {
    int id;
    char shipment_code[MAX_CODE_LEN];
    double weight;
    double volume;
    char destination[MAX_NAME_LEN];
    long long deadline_timestamp; // Unix timestamp in seconds
    int priority;                 // 1=Low, 2=Medium, 3=High, 4=Urgent, 5=Critical
    int status;                   // 0=Created, 1=Pending, 2=Assigned, 3=In Transit, 4=Delivered, 5=Cancelled
} CShipment;

typedef struct {
    int id;
    char vehicle_code[MAX_CODE_LEN];
    char vehicle_type[MAX_NAME_LEN];
    double max_weight;
    double max_volume;
    double current_weight;
    double current_volume;
    int is_available;
} CVehicle;

typedef struct {
    double execution_time_us;
    long long comparisons;
    long long operations;
} CPerformanceResult;

typedef struct {
    int id;
    char name[MAX_NAME_LEN];
    char code[16];
    double x_coord;
    double y_coord;
} CLocation;

typedef struct {
    int source_id;
    int dest_id;
    double distance_km;
    int road_id;
    int is_active;
} CRoad;

typedef struct {
    int total_path_len;
    int path[MAX_VERTICES];
    double total_distance;
    int visited_count;
    int visited_nodes[MAX_VERTICES];
    double execution_time_us;
    long long comparisons;
} CRouteResult;

typedef struct {
    int edge_count;
    int u[MAX_EDGES];
    int v[MAX_EDGES];
    double weights[MAX_EDGES];
    double total_cost;
    double execution_time_us;
    long long operations;
} CMSTResult;

#pragma pack(pop)

#endif // COMMON_H
