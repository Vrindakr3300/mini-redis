import os
from pkg.resp.types import serialize
from pkg.resp.parser import BufferReader

class AOFManager:
    """Manages Append-Only File (AOF) persistence for database state durability."""
    def __init__(self, filepath: str = "appendonly.aof"):
        self.filepath = filepath
        self._file = None

    def open(self):
        """Opens the AOF file in binary append mode with unbuffered writes."""
        self._file = open(self.filepath, "ab", buffering=0)

    def write(self, command_args: list):
        """Serializes and appends a command to the AOF file."""
        if self._file:
            resp_bytes = serialize(command_args)
            self._file.write(resp_bytes)

    def load(self, handler) -> int:
        """Reads the AOF file and replays all write commands through the handler."""
        if not os.path.exists(self.filepath):
            return 0

        count = 0
        reader = BufferReader()
        with open(self.filepath, "rb") as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                reader.feed(chunk)
                while True:
                    try:
                        cmd_args = reader.parse_next()
                        if cmd_args is None:
                            break
                        handler.handle(cmd_args)
                        count += 1
                    except Exception as e:
                        print(f"[ERROR] Failed to replay command {cmd_args}: {e}")
                        break
        return count

    def close(self):
        """Closes the AOF file stream."""
        if self._file:
            self._file.close()
            self._file = None
