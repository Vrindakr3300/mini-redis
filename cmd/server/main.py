import sys
import os
# Add project root to sys.path to avoid collisions with standard library 'cmd'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import socket
import threading
from pkg.store.db import Database
from pkg.commands.handler import CommandHandler
from pkg.resp.parser import BufferReader
from pkg.resp.types import serialize, RESPError
from pkg.store.aof import AOFManager

# Default Redis port
PORT = 6379
HOST = "127.0.0.1"

# Shared database, command handler, and AOF manager
db = Database()
handler = CommandHandler(db)
aof_manager = AOFManager("appendonly.aof")

def handle_client(client_socket, client_address):
    print(f"[INFO] New connection from {client_address}")
    reader = BufferReader()
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                print(f"[INFO] Client {client_address} disconnected")
                break
            
            reader.feed(data)
            
            # Parse and execute all complete messages in the buffer
            while True:
                try:
                    command_args = reader.parse_next()
                    if command_args is None:
                        break  # Incomplete command, wait for more data
                    
                    # Execute the command
                    result = handler.handle(command_args)
                    
                    # Send response
                    response_bytes = serialize(result)
                    client_socket.sendall(response_bytes)

                    # Log successful write commands to AOF
                    if not isinstance(result, RESPError):
                        cmd_name = str(command_args[0]).upper()
                        if cmd_name in ("SET", "DEL", "LPUSH", "RPUSH", "LPOP", "RPOP", "HSET", "HDEL"):
                            aof_manager.write(command_args)
                except Exception as parse_error:
                    # Write protocol error back to the client
                    error_bytes = serialize(parse_error)
                    client_socket.sendall(error_bytes)
                    
    except Exception as e:
        print(f"[ERROR] Error handling client {client_address}: {e}")
    finally:
        client_socket.close()

def main():
    # Load AOF to restore database state
    print("[INFO] Replaying AOF file to restore state...")
    loaded_count = aof_manager.load(handler)
    print(f"[INFO] Replayed {loaded_count} commands from AOF.")
    
    # Open AOF file for logging new writes
    aof_manager.open()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
