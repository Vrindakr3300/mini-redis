import unittest
import time
from pkg.store.db import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database()

    def test_set_and_get(self):
        self.db.set("name", "antigravity")
        self.assertEqual(self.db.get("name"), "antigravity")

    def test_get_non_existent(self):
        self.assertIsNone(self.db.get("unknown"))

    def test_delete(self):
        self.db.set("name", "antigravity")
        self.assertTrue(self.db.delete("name"))
        self.assertIsNone(self.db.get("name"))
        self.assertFalse(self.db.delete("name"))  # already deleted

    def test_exists(self):
        self.assertFalse(self.db.exists("name"))
        self.db.set("name", "antigravity")
        self.assertTrue(self.db.exists("name"))

    def test_passive_expiration(self):
        # Set with 0.1 seconds TTL
        self.db.set("temp", "value", ttl_seconds=0.1)
        self.assertEqual(self.db.get("temp"), "value")
        
        # Wait for key to expire
        time.sleep(0.15)
        self.assertIsNone(self.db.get("temp"))
        self.assertFalse(self.db.exists("temp"))

    def test_active_expiration(self):
        # Set with 0.1 seconds TTL (active cleaner runs every 1 second)
        self.db.set("temp", "value", ttl_seconds=0.1)
        self.assertTrue(self.db.exists("temp"))
        
        # Wait for the background thread to run (1.2s sleep is enough)
        time.sleep(1.2)
        
        # Access internal state directly to ensure active deletion removed the key
        with self.db._lock:
            self.assertNotIn("temp", self.db._data)

    def test_list_operations(self):
        # Test LPUSH and RPUSH
        self.assertEqual(self.db.lpush("mylist", ["a", "b"]), 2)  # Should yield ["b", "a"]
        self.assertEqual(self.db.rpush("mylist", ["c", "d"]), 4)  # Should yield ["b", "a", "c", "d"]
        
        # Test LRANGE
        self.assertEqual(self.db.lrange("mylist", 0, -1), ["b", "a", "c", "d"])
        self.assertEqual(self.db.lrange("mylist", 1, 2), ["a", "c"])
        
        # Test LPOP and RPOP
        self.assertEqual(self.db.lpop("mylist"), "b")
        self.assertEqual(self.db.rpop("mylist"), "d")
        self.assertEqual(self.db.lrange("mylist", 0, -1), ["a", "c"])
        
        # Test type validation
        self.db.set("mystr", "hello")
        with self.assertRaises(TypeError):
            self.db.lpush("mystr", ["a"])

    def test_hash_operations(self):
        # Test HSET and HGET
        self.assertEqual(self.db.hset("myhash", {"f1": "v1", "f2": "v2"}), 2)
        self.assertEqual(self.db.hget("myhash", "f1"), "v1")
        self.assertIsNone(self.db.hget("myhash", "unknown"))
        
        # Test HDEL
        self.assertEqual(self.db.hdel("myhash", ["f1", "f3"]), 1)
        self.assertIsNone(self.db.hget("myhash", "f1"))
        
        # Test type validation
        self.db.set("mystr", "hello")
        with self.assertRaises(TypeError):
            self.db.hset("mystr", {"f1": "v1"})

if __name__ == "__main__":
    unittest.main()

