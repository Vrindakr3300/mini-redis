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
                "expires_at": expires_at
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
