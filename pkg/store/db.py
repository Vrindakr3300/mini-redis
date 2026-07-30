import threading
import time

class Database:
    """A thread-safe in-memory key-value database."""
    def __init__(self, run_cleaner: bool = True):
        # Maps key -> {"value": val, "expires_at": timestamp_or_none}
        self._data = {}
        self._lock = threading.Lock()
        if run_cleaner:
            self._cleaner_thread = threading.Thread(target=self._active_expire_loop, daemon=True)
            self._cleaner_thread.start()

    def _active_expire_loop(self):
        """Background loop to periodically trigger active key expiration."""
        while True:
            time.sleep(1.0)
            self._active_expire()

    def _active_expire(self):
        """Removes expired keys from the database."""
        with self._lock:
            now = time.time()
            expired_keys = []
            for key, entry in self._data.items():
                if entry["expires_at"] is not None and now > entry["expires_at"]:
                    expired_keys.append(key)
            for key in expired_keys:
                del self._data[key]


    def set(self, key: str, value: str, ttl_seconds: float | None = None) -> bool:
        """Sets a key to a value with an optional TTL (in seconds)."""
        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + ttl_seconds

        with self._lock:
            self._data[key] = {
                "value": value,
                "expires_at": expires_at,
                "type": "string"
            }
            return True

    def _is_expired(self, entry: dict) -> bool:
        """Checks if a database entry is expired."""
        if entry["expires_at"] is None:
            return False
        return time.time() > entry["expires_at"]

    def get(self, key: str) -> str | None:
        """Gets a key's value. Returns None if key doesn't exist or is expired."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            
            if self._is_expired(entry):
                # Passive deletion
                del self._data[key]
                return None
            
            return entry["value"]

    def delete(self, key: str) -> bool:
        """Deletes a key. Returns True if key existed and was not expired."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            
            expired = self._is_expired(entry)
            del self._data[key]
            return not expired

    def exists(self, key: str) -> bool:
        """Returns True if the key exists and has not expired."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            
            if self._is_expired(entry):
                del self._data[key]
                return False
            
            return True

    def keys(self) -> list[str]:
        """Returns all unexpired keys in the database."""
        with self._lock:
            now = time.time()
            valid_keys = []
            expired_keys = []
            
            for key, entry in self._data.items():
                if entry["expires_at"] is not None and now > entry["expires_at"]:
                    expired_keys.append(key)
                else:
                    valid_keys.append(key)
            
            # Clean up any expired keys found during scan
            for key in expired_keys:
                del self._data[key]
                
            return valid_keys

    # LIST OPERATIONS
    def lpush(self, key: str, values: list[str]) -> int:
        """Pushes values to the head (left) of the list. Returns new length of list."""
        with self._lock:
            entry = self._data.get(key)
            if entry is not None:
                if self._is_expired(entry):
                    del self._data[key]
                    entry = None
                elif entry.get("type", "string") != "list":
                    raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if entry is None:
                entry = {"value": [], "expires_at": None, "type": "list"}
                self._data[key] = entry

            for val in values:
                entry["value"].insert(0, val)
            
            return len(entry["value"])

    def rpush(self, key: str, values: list[str]) -> int:
        """Pushes values to the tail (right) of the list. Returns new length of list."""
        with self._lock:
            entry = self._data.get(key)
            if entry is not None:
                if self._is_expired(entry):
                    del self._data[key]
                    entry = None
                elif entry.get("type", "string") != "list":
                    raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if entry is None:
                entry = {"value": [], "expires_at": None, "type": "list"}
                self._data[key] = entry

            entry["value"].extend(values)
            return len(entry["value"])

    def lpop(self, key: str) -> str | None:
        """Pops and returns the first element from the head (left) of the list."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None or self._is_expired(entry):
                if entry is not None:
                    del self._data[key]
                return None
            if entry.get("type", "string") != "list":
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if not entry["value"]:
                return None
            val = entry["value"].pop(0)
            if not entry["value"]:
                del self._data[key]
            return val

    def rpop(self, key: str) -> str | None:
        """Pops and returns the last element from the tail (right) of the list."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None or self._is_expired(entry):
                if entry is not None:
                    del self._data[key]
                return None
            if entry.get("type", "string") != "list":
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if not entry["value"]:
                return None
            val = entry["value"].pop()
            if not entry["value"]:
                del self._data[key]
            return val

    def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """Returns specified elements of the list. start/stop can be negative."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None or self._is_expired(entry):
                if entry is not None:
                    del self._data[key]
                return []
            if entry.get("type", "string") != "list":
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            n = len(entry["value"])
            if start < 0:
                start = max(n + start, 0)
            if stop < 0:
                stop = n + stop
            
            if start >= n or start > stop:
                return []
                
            return entry["value"][start:stop + 1]

    # HASH OPERATIONS
    def hset(self, key: str, fields: dict[str, str]) -> int:
        """Sets field-value pairs in a hash. Returns the number of fields created."""
        with self._lock:
            entry = self._data.get(key)
            if entry is not None:
                if self._is_expired(entry):
                    del self._data[key]
                    entry = None
                elif entry.get("type", "string") != "hash":
                    raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if entry is None:
                entry = {"value": {}, "expires_at": None, "type": "hash"}
                self._data[key] = entry

            new_fields_count = 0
            for field, val in fields.items():
                if field not in entry["value"]:
                    new_fields_count += 1
                entry["value"][field] = val
                
            return new_fields_count

    def hget(self, key: str, field: str) -> str | None:
        """Gets the value of a hash field."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None or self._is_expired(entry):
                if entry is not None:
                    del self._data[key]
                return None
            if entry.get("type", "string") != "hash":
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            return entry["value"].get(field)

    def hdel(self, key: str, fields: list[str]) -> int:
        """Deletes specified fields from a hash. Returns number of fields deleted."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None or self._is_expired(entry):
                if entry is not None:
                    del self._data[key]
                return 0
            if entry.get("type", "string") != "hash":
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            count = 0
            for field in fields:
                if field in entry["value"]:
                    del entry["value"][field]
                    count += 1
                    
            if not entry["value"]:
                del self._data[key]
                
            return count
