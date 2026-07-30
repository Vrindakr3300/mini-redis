from .types import RESPError

class BufferReader:
    """Manages a byte buffer for streaming socket data."""
    def __init__(self):
        self.buf = bytearray()

    def feed(self, data: bytes):
        """Append raw socket data to the buffer."""
        self.buf.extend(data)

    def parse_next(self):
        """
        Parses the next complete RESP object from the buffer.
        Returns the parsed value (str, int, list, RESPError, or None).
        Returns None if the buffer does not yet contain a complete message.
        """
        if not self.buf:
            return None

        first_byte = self.buf[0:1]

        if first_byte == b"+":  # Simple String
            idx = self.buf.find(b"\r\n")
            if idx == -1:
                return None
            line = self.buf[1:idx].decode("utf-8")
            del self.buf[:idx + 2]
            return line

        elif first_byte == b"-":  # Error
            idx = self.buf.find(b"\r\n")
            if idx == -1:
                return None
            line = self.buf[1:idx].decode("utf-8")
            del self.buf[:idx + 2]
            return RESPError(line)

        elif first_byte == b":":  # Integer
            idx = self.buf.find(b"\r\n")
            if idx == -1:
                return None
            try:
                val = int(self.buf[1:idx])
            except ValueError:
                raise ValueError("Protocol error: invalid integer format")
            del self.buf[:idx + 2]
            return val

        elif first_byte == b"$":  # Bulk String
            idx = self.buf.find(b"\r\n")
            if idx == -1:
                return None
            
            try:
                length = int(self.buf[1:idx])
            except ValueError:
                raise ValueError("Protocol error: invalid bulk string length format")

            if length == -1:  # Null Bulk String
                del self.buf[:idx + 2]
                return None

            header_len = idx + 2
            total_len = header_len + length + 2  # data length + CRLF

            if len(self.buf) < total_len:
                return None

            if self.buf[header_len + length:header_len + length + 2] != b"\r\n":
                raise ValueError("Protocol error: bulk string not terminated with CRLF")

            data = self.buf[header_len:header_len + length].decode("utf-8")
            del self.buf[:total_len]
            return data

        elif first_byte == b"*":  # Array
            idx = self.buf.find(b"\r\n")
            if idx == -1:
                return None

            try:
                count = int(self.buf[1:idx])
            except ValueError:
                raise ValueError("Protocol error: invalid array count format")

            if count == -1:  # Null Array
                del self.buf[:idx + 2]
                return None

            # Backtracking: Save buffer state in case array elements are incomplete
            saved_buf = bytearray(self.buf)
            del self.buf[:idx + 2]

            arr = []
            for _ in range(count):
                item = self.parse_next()
                if item is None:
                    # Incomplete array, restore the buffer
                    self.buf = saved_buf
                    return None
                arr.append(item)
            return arr

        else:
            # If we don't recognize the type byte, it might be inline commands (like PING from telnet)
            # Let's support inline command parsing for convenience (simple space-separated string)
            idx = self.buf.find(b"\r\n")
            if idx == -1:
                return None
            line = self.buf[:idx].decode("utf-8")
            del self.buf[:idx + 2]
            # Split by space and return as an array
            return line.split()
