import socket
import threading
import sys

# Default Redis port
PORT = 6379
HOST = "127.0.0.1"

def handle_client(client_socket, client_address):
    print(f"[INFO] New connection from {client_address}")
    try:
        while True:
            # Read data from client (up to 1024 bytes)
            data = client_socket.recv(1024)
            if not data:
                print(f"[INFO] Client {client_address} disconnected")
                break
            
            # For Phase 1, we just echo back what we received
            print(f"[DEBUG] Received from {client_address}: {data}")
            client_socket.sendall(data)
    except Exception as e:
        print(f"[ERROR] Error handling client {client_address}: {e}")
    finally:
        client_socket.close()

def main():
    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow address reuse so restarting doesn't result in "Address already in use" errors
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[INFO] Mini-Redis server listening on {HOST}:{PORT}...")
    except Exception as e:
        print(f"[ERROR] Failed to bind to {HOST}:{PORT}: {e}")
        sys.exit(1)
        
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            # Handle client in a new thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
