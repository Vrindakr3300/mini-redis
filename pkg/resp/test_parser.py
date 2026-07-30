import unittest
from pkg.resp.parser import BufferReader
from pkg.resp.types import serialize, RESPError

class TestRESP(unittest.TestCase):
    def setUp(self):
        self.reader = BufferReader()

    def test_parse_simple_string(self):
        self.reader.feed(b"+OK\r\n")
        self.assertEqual(self.reader.parse_next(), "OK")

    def test_parse_error(self):
        self.reader.feed(b"-ERR unknown command\r\n")
        val = self.reader.parse_next()
        self.assertTrue(isinstance(val, RESPError))
        self.assertEqual(val.message, "ERR unknown command")

    def test_parse_integer(self):
        self.reader.feed(b":1000\r\n")
        self.assertEqual(self.reader.parse_next(), 1000)

    def test_parse_bulk_string(self):
        self.reader.feed(b"$5\r\nhello\r\n")
        self.assertEqual(self.reader.parse_next(), "hello")

    def test_parse_null_bulk_string(self):
        self.reader.feed(b"$-1\r\n")
        self.assertIsNone(self.reader.parse_next())

    def test_parse_array(self):
        self.reader.feed(b"*2\r\n$5\r\nhello\r\n$5\r\nworld\r\n")
        self.assertEqual(self.reader.parse_next(), ["hello", "world"])

    def test_parse_incomplete(self):
        self.reader.feed(b"*2\r\n$5\r\nhello\r\n$5\r\n")
        self.assertIsNone(self.reader.parse_next())
        # Feed the rest
        self.reader.feed(b"world\r\n")
        self.assertEqual(self.reader.parse_next(), ["hello", "world"])

    def test_serialize(self):
        self.assertEqual(serialize("+OK\r\n"), b"+OK\r\n")
        self.assertEqual(serialize(1000), b":1000\r\n")
        self.assertEqual(serialize(None), b"$-1\r\n")
        self.assertEqual(serialize(["hello", "world"]), b"*2\r\n$5\r\nhello\r\n$5\r\nworld\r\n")

if __name__ == "__main__":
    unittest.main()
