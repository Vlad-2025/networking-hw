import socket
import json
import os
import threading

# Configuration
SERVER_HOST = 'localhost'
SERVER_PORT = 5000
FILES_DIR = 'files'
DEFAULT_USER = 'student'
DEFAULT_PASSWORD = '1234'

file_history = {}

def ensure_files_dir():
    """Ensure files directory exists"""
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
        print(f"✓ Directory '{FILES_DIR}' created")


def authenticate(username, password):
    """Authenticate user"""
    return username == DEFAULT_USER and password == DEFAULT_PASSWORD

def log_operation(filename: str, operation_type: str):
    global file_history

    # create new history if file is new
    if filename not in file_history:
        file_history[filename] = []

    file_history[filename].append(operation_type)


def handle_client(conn, addr):
    """Handle client connection"""
    print(f"\n🔗 Client connected from {addr}")
    authenticated = False
    current_user = None
    
    try:
        while True:
            # Receive request
            request_data = conn.recv(4096).decode('utf-8')
            if not request_data:
                break
            
            try:
                request = json.loads(request_data)
                command = request.get('command')
                
                print(f"📨 Command received: {command}")
                
                # Authentication
                if command == 'login':
                    username = request.get('username')
                    password = request.get('password')
                    
                    if authenticate(username, password):
                        authenticated = True
                        current_user = username
                        response = {'status': 'success', 'message': f'Welcome {username}!'}
                        print(f"✓ User {username} authenticated")
                    else:
                        response = {'status': 'error', 'message': 'Invalid credentials'}
                        print(f"✗ Authentication failed for user {username}")
                
                elif not authenticated:
                    response = {'status': 'error', 'message': 'Not authenticated. Use login first'}
                
                # File operations
                elif command == 'create_file':
                    filename = request.get('filename')
                    content = request.get('content', '')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    
                    response = {'status': 'success', 'message': f'File {filename} created on server'}

                    log_operation(filename, "create")

                    print(f"✓ File created: {filename}")
                
                elif command == 'upload':
                    filename = request.get('filename')
                    content = request.get('content')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    
                    response = {'status': 'success', 'message': f'File {filename} uploaded'}

                    log_operation(filename, "upload")

                    print(f"✓ File uploaded: {filename}")
                
                elif command == 'rename_file':

                    filename = request.get('filename')
                    new_filename = request.get('new_filename')

                    filepath = os.path.join(FILES_DIR, filename)
                    new_filepath = os.path.join(FILES_DIR, new_filename)

                    if not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f"File {filename} doesnt exist"
                        }
                    else:
                        os.rename(filepath, new_filepath)
                        response = {
                            'status': 'success',
                            'message': f"File {filename} renamed to {new_filename}"
                        }

                        file_history[new_filename] = file_history.pop(filename, [])
                        log_operation(new_filename, f"renamed from {filename}")

                        print(f"File renamed: {filename} -> {new_filename}")


                elif command == 'read_file':

                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)

                    if not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f'File {filename} doesnt exist!'
                        }
                    else:
                        with open(filepath, 'r') as f:
                            text = f.read()

                        response = {
                            'status': 'success',
                            'message': text
                        }

                        log_operation(filename, "read_file")

                elif command == 'download':

                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)

                    if not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f"File {filename} doesnt exist"
                        }

                    else:
                        with open(filepath, 'r') as f:
                            text = f.read()

                        response = {
                            'status': 'success',
                            'filename': filename,
                            'message': text
                        }

                        log_operation(filename, "download")

                elif command == 'edit_file':

                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)

                    new_text = request.get('new_text')

                    if not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f"File {filename} doenst exist!",
                        }
                    else:
                        with open(filepath, 'w') as f:
                            f.write(new_text)

                        response = {
                            'status': 'success',
                            'filename': filename,
                            'message': new_text
                        }

                        log_operation(filename, "edit_file")

                elif command == 'see_file_operation_history':

                    filename = request.get('filename')
                    history = file_history.get(filename, [])

                    if not history:
                        response = {
                            'status': 'success',
                            'message': f"No history found for {filename}"
                        }
                    else:
                        history_text = "\n".join(f"{i+1}. {op}" for i, op in enumerate(history))
                        response = {
                            'status': 'success',
                            'message': history_text
                        }

                elif command == 'list_files':
                    files = os.listdir(FILES_DIR)
                    response = {'status': 'success', 'files': files}
                    print(f"✓ Files listed: {len(files)} files found")
                
                elif command == 'logout':
                    authenticated = False
                    current_user = None
                    response = {'status': 'success', 'message': 'Logged out'}
                    print(f"✓ User logged out")
                
                else:
                    response = {'status': 'error', 'message': f'Unknown command: {command}'}
                
            except Exception as e:
                response = {'status': 'error', 'message': str(e)}
                print(f"✗ Error: {str(e)}")
            
            # Send response
            conn.send(json.dumps(response).encode('utf-8'))
    
    except Exception as e:
        print(f"✗ Connection error: {str(e)}")
    finally:
        conn.close()
        print(f"🔌 Client disconnected from {addr}")


def start_server():
    """Start FTP server"""
    ensure_files_dir()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    
    print("=" * 60)
    print("🚀 FTP SERVER STARTED")
    print("=" * 60)
    print(f"Host: {SERVER_HOST}")
    print(f"Port: {SERVER_PORT}")
    print(f"Files Directory: {FILES_DIR}")
    print(f"Default User: {DEFAULT_USER}")
    print(f"Default Password: {DEFAULT_PASSWORD}")
    print("=" * 60)
    
    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n\n⛔ Server shutting down...")
    finally:
        server_socket.close()


if __name__ == '__main__':
    start_server()
