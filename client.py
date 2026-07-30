import socket
import sys

def main():
    host = "127.0.0.1"
    port = 6379
    
    print(f"Connecting to Mini-Redis at {host}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print("Connected! Type your commands (e.g., PING, SET name John, GET name, LPUSH list v1).")
        print("Type 'exit' or press Ctrl+C to close.\n")
        
        while True:
            cmd = input("mini-redis> ").strip()
            if not cmd:
                continue
            if cmd.lower() == "exit":
                break
                
            # Send command terminated with CRLF (inline command protocol)
            s.sendall(f"{cmd}\r\n".encode("utf-8"))
            
            # Read and print response
            response = s.recv(4096)
            print(response.decode("utf-8", errors="ignore"), end="")
            
    except KeyboardInterrupt:
        print("\nDisconnecting...")
    except ConnectionRefusedError:
        print("\n[ERROR] Could not connect to Mini-Redis. Is your server running (python cmd/server/main.py)?")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    main()
