import socket
import threading

HOST = "127.0.0.1"
PORT = 3333
BUFFER_SIZE = 1024

class State:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()

    def add(self, key, value):
        with self.lock:
            self.data[key] = value
        return f"{key} added"

    def get(self, key):
        with self.lock:
            return self.data.get(key, "Key not found")

    def remove(self, key):
        with self.lock:
            if key in self.data:
                del self.data[key]
                return f"{key} removed"
            return "Key not found"


    def list(self):
        with self.lock:
            return dict(self.data)

    def count(self):
        with self.lock:
            return len(self.data)

    def clear(self):
        with self.lock:
            self.data.clear()
            return "All data deleted"

    def update(self, key, new_value):
        with self.lock:
            if key in self.data:
                self.data[key] = new_value
                return "Data updated"
            return "Key is not in map!"

    def pop(self, key):
        with self.lock:
            if key in self.data:
                return self.data.pop(key)
            return "Key not in map"

state = State()

def process_command(command):
    parts = command.split()

    if len(parts) < 1:
        return "Invalid command format"

    cmd = parts[0]

    if cmd == "list" and len(parts) == 1:
        return state.list()
    elif cmd == "count" and len(parts) == 1:
        return state.count()
    elif cmd == "clear" and len(parts) == 1:
        return state.clear()
    elif cmd == "quit" and len(parts) == 1:
        return None

    if len(parts) < 2:
        return "Invalid command format"


    key = parts[1]
    
    if cmd == "add" and len(parts) > 2:
        return state.add(key, ' '.join(parts[2:]))
    elif cmd == "get" and len(parts) == 2:
        return state.get(key)
    elif cmd == "remove" and len(parts) == 2:
        return state.remove(key)
    elif cmd == "pop" and len(parts) == 2:
        return state.pop(key)

    if len(parts) < 3:
        return "Invalid command format"

    new_value = parts[2]

    if cmd == "update" and len(parts) == 3:
        return state.update(key, new_value)
    
    return "Invalid command"

def handle_client(client_socket):
    with client_socket:
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                command = data.decode('utf-8').strip()
                response = process_command(command)

                if response is None:
                    break

                response_str = str(response)
                response_data = f"{len(response_str)} {response_str}".encode('utf-8')
                client_socket.sendall(response_data)

            except Exception as e:
                client_socket.sendall(f"Error: {str(e)}".encode('utf-8'))
                break

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"[SERVER] Connection from {addr}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()
