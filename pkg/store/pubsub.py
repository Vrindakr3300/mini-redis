import threading
from pkg.resp.types import serialize

class PubSubManager:
    """Manages Publish/Subscribe (Pub/Sub) messaging for client connections."""
    def __init__(self):
        # Maps channel (str) -> set of client sockets
        self._subscribers = {}
        # Maps client socket -> set of channels they are subscribed to
        self._client_channels = {}
        self._lock = threading.Lock()

    def subscribe(self, client_socket, channels: list[str]) -> list[tuple[str, int]]:
        """Subscribes a client connection to a list of channels. Returns list of (channel, count)."""
        with self._lock:
            if client_socket not in self._client_channels:
                self._client_channels[client_socket] = set()
            
            results = []
            for channel in channels:
                if channel not in self._subscribers:
                    self._subscribers[channel] = set()
                self._subscribers[channel].add(client_socket)
                self._client_channels[client_socket].add(channel)
                results.append((channel, len(self._client_channels[client_socket])))
            return results

    def unsubscribe_all(self, client_socket):
        """Unsubscribes a client connection from all channels they are active in."""
        with self._lock:
            channels = self._client_channels.pop(client_socket, set())
            for channel in channels:
                if channel in self._subscribers:
                    self._subscribers[channel].discard(client_socket)
                    if not self._subscribers[channel]:
                        del self._subscribers[channel]

    def publish(self, channel: str, message: str) -> int:
        """Publishes a message to a channel. Returns the number of active subscribers reached."""
        with self._lock:
            sockets = list(self._subscribers.get(channel, []))
        
        count = 0
        resp_data = serialize(["message", channel, message])
        
        dead_sockets = []
        for sock in sockets:
            try:
                sock.sendall(resp_data)
                count += 1
            except Exception:
                # Socket is disconnected, flag for cleanup
                dead_sockets.append(sock)
        
        # Clean up any dead sockets found during publication
        for sock in dead_sockets:
            self.unsubscribe_all(sock)
            
        return count
