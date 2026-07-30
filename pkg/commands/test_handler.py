import unittest
from pkg.store.db import Database
from pkg.commands.handler import CommandHandler
from pkg.resp.types import RESPError

class TestCommandHandler(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.handler = CommandHandler(self.db)

    def test_ping(self):
        self.assertEqual(self.handler.handle(["PING"]), "+PONG")
        self.assertEqual(self.handler.handle(["PING", "hello"]), "hello")
        self.assertTrue(isinstance(self.handler.handle(["PING", "hello", "world"]), RESPError))

    def test_set_and_get(self):
        self.assertEqual(self.handler.handle(["SET", "key", "val"]), "+OK")
        self.assertEqual(self.handler.handle(["GET", "key"]), "val")

    def test_del(self):
        self.handler.handle(["SET", "k1", "v1"])
        self.handler.handle(["SET", "k2", "v2"])
        self.assertEqual(self.handler.handle(["DEL", "k1", "k2", "k3"]), 2)
        self.assertIsNone(self.handler.handle(["GET", "k1"]))

    def test_exists(self):
        self.handler.handle(["SET", "k1", "v1"])
        self.assertEqual(self.handler.handle(["EXISTS", "k1", "k2"]), 1)

    def test_keys(self):
        self.handler.handle(["SET", "k1", "v1"])
        self.handler.handle(["SET", "k2", "v2"])
        keys = self.handler.handle(["KEYS"])
        self.assertEqual(set(keys), {"k1", "k2"})

    def test_list_commands(self):
        self.assertEqual(self.handler.handle(["LPUSH", "mylist", "a", "b"]), 2)
        self.assertEqual(self.handler.handle(["RPUSH", "mylist", "c"]), 3)
        self.assertEqual(self.handler.handle(["LRANGE", "mylist", "0", "-1"]), ["b", "a", "c"])
        self.assertEqual(self.handler.handle(["LPOP", "mylist"]), "b")
        self.assertEqual(self.handler.handle(["RPOP", "mylist"]), "c")

    def test_hash_commands(self):
        self.assertEqual(self.handler.handle(["HSET", "myhash", "f1", "v1", "f2", "v2"]), 2)
        self.assertEqual(self.handler.handle(["HGET", "myhash", "f1"]), "v1")
        self.assertIsNone(self.handler.handle(["HGET", "myhash", "unknown"]))
        self.assertEqual(self.handler.handle(["HDEL", "myhash", "f1"]), 1)

if __name__ == "__main__":
    unittest.main()
