import socket
import sys

def is_port_available(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def find_first_free_port(start_port=8502, max_port=8550):
    for p in range(start_port, max_port + 1):
        if is_port_available(p):
            return p
    return start_port

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 8502
    free_port = find_first_free_port(start)
    print(free_port)
