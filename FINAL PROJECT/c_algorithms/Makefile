CC = gcc
CFLAGS = -O3 -Wall -Wextra -shared -fPIC -I.
TARGET = ../bin/logistics_c.dll

SRCS = linked_list.c \
       stack.c \
       queue.c \
       priority_queue.c \
       min_heap.c \
       bst.c \
       avl_tree.c \
       red_black_tree.c \
       b_tree.c \
       splay_tree.c \
       hash_table.c \
       finite_state_machine.c \
       quick_sort.c \
       merge_sort.c \
       heap_sort.c \
       graph.c \
       bfs.c \
       dfs.c \
       dijkstra.c \
       prim.c \
       kruskal.c

all: $(TARGET)

$(TARGET): $(SRCS) common.h
	$(CC) $(CFLAGS) $(SRCS) -o $(TARGET)

clean:
	rm -f $(TARGET)
