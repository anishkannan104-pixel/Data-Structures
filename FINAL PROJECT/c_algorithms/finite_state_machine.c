#include "common.h"

// Supported shipment states:
// 0: Created
// 1: Pending
// 2: Assigned
// 3: In Transit
// 4: Delivered
// 5: Cancelled

static const char* STATE_NAMES[6] = {
    "Created",
    "Pending",
    "Assigned",
    "In Transit",
    "Delivered",
    "Cancelled"
};

// State transition validation matrix: [from_state][to_state]
// 1 = Valid transition, 0 = Invalid transition
static const int TRANSITION_MATRIX[6][6] = {
    // Created -> Pending (1), Cancelled (5)
    {0, 1, 0, 0, 0, 1},
    // Pending -> Assigned (2), Cancelled (5)
    {0, 0, 1, 0, 0, 1},
    // Assigned -> In Transit (3), Pending (1 - unassign), Cancelled (5)
    {0, 1, 0, 1, 0, 1},
    // In Transit -> Delivered (4), Cancelled (5 - lost/damaged)
    {0, 0, 0, 0, 1, 1},
    // Delivered -> Terminal (no transitions)
    {0, 0, 0, 0, 0, 0},
    // Cancelled -> Terminal (no transitions)
    {0, 0, 0, 0, 0, 0}
};

EXPORT_API const char* fsm_get_state_name(int state) {
    if (state >= 0 && state < 6) {
        return STATE_NAMES[state];
    }
    return "Unknown";
}

EXPORT_API int fsm_validate_transition(int from_state, int to_state, char* out_message, int max_msg_len) {
    if (from_state < 0 || from_state >= 6 || to_state < 0 || to_state >= 6) {
        if (out_message) {
            snprintf(out_message, max_msg_len, "Invalid state index: from=%d, to=%d.", from_state, to_state);
        }
        return 0;
    }

    if (from_state == to_state) {
        if (out_message) {
            snprintf(out_message, max_msg_len, "Shipment is already in state '%s'.", STATE_NAMES[from_state]);
        }
        return 0;
    }

    if (from_state == 4) { // Delivered
        if (out_message) {
            snprintf(out_message, max_msg_len, "Illegal Transition: Shipment is already 'Delivered' (terminal state) and cannot transition to '%s'.", STATE_NAMES[to_state]);
        }
        return 0;
    }

    if (from_state == 5) { // Cancelled
        if (out_message) {
            snprintf(out_message, max_msg_len, "Illegal Transition: Shipment is 'Cancelled' (terminal state) and cannot be reactivated to '%s'.", STATE_NAMES[to_state]);
        }
        return 0;
    }

    int valid = TRANSITION_MATRIX[from_state][to_state];
    if (valid) {
        if (out_message) {
            snprintf(out_message, max_msg_len, "Valid Transition: State changed from '%s' to '%s'.", STATE_NAMES[from_state], STATE_NAMES[to_state]);
        }
        return 1;
    } else {
        if (out_message) {
            snprintf(out_message, max_msg_len, "Illegal Transition: Cannot move directly from '%s' to '%s'. Required intermediate stages must be completed first.", STATE_NAMES[from_state], STATE_NAMES[to_state]);
        }
        return 0;
    }
}
