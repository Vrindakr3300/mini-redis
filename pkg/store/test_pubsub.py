import unittest
import socket
from pkg.store.pubsub import PubSubManager
from pkg.resp.parser import BufferReader

class MockSocket:
    """Mock socket class to capture data sent during tests."""
    def __init__(self):
        self.sent_data = bytearray()
        self.closed = False

    def sendall(self, data):
        if self.closed:
            raise socket.error("Socket is closed")
        self.sent_data.extend(data)

    def close(self):
        self.closed = True

class TestPubSub(unittest.TestCase):
    def setUp(self):
        self.pubsub = PubSubManager()
        self.sock1 = MockSocket()
        self.sock2 = MockSocket()

    def test_subscribe_and_publish(self):
        # Subscribe sock1 to channel 'news'
        res1 = self.pubsub.subscribe(self.sock1, ["news"])
        self.assertEqual(res1, [("news", 1)])
        
        # Subscribe sock2 to 'news' and 'sports'
        res2 = self.pubsub.subscribe(self.sock2, ["news", "sports"])
        self.assertEqual(res2, [("news", 1), ("sports", 2)])
        
        # Publish message to 'news'
        count = self.pubsub.publish("news", "headline")
        self.assertEqual(count, 2)  # Both mocks reached
        
        # Verify socket 1 received the payload
        reader1 = BufferReader()
        reader1.feed(self.sock1.sent_data)
        self.assertEqual(reader1.parse_next(), ["message", "news", "headline"])
        
        # Verify socket 2 received the payload
        reader2 = BufferReader()
        reader2.feed(self.sock2.sent_data)
        self.assertEqual(reader2.parse_next(), ["message", "news", "headline"])

    def test_unsubscribe_and_dead_sockets(self):
        self.pubsub.subscribe(self.sock1, ["news"])
        self.pubsub.subscribe(self.sock2, ["news"])
        
        # Close sock1 to simulate disconnection
        self.sock1.close()
        
        # Publishing should detect sock1 is dead and clean it up automatically
        count = self.pubsub.publish("news", "test")
        self.assertEqual(count, 1)  # Only sock2 reached
        
        # Verify sock1 was unsubscribed automatically
        with self.pubsub._lock:
            self.assertNotIn(self.sock1, self.pubsub._subscribers.get("news", set()))

if __name__ == "__main__":
    unittest.main()
