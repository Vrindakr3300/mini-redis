from pkg.resp.types import RESPError
from pkg.store.db import Database

class CommandHandler:
    """Routes and handles Redis commands."""
    def __init__(self, db: Database):
        self.db = db

    def handle(self, args: list) -> any:
        """
        Parses command arguments and executes the corresponding database operation.
        Returns the command result to be serialized back to the client.
        """
        if not args:
            return RESPError("ERR empty command")
        
        cmd_name = str(args[0]).upper()
        cmd_args = args[1:]
        
        if cmd_name == "PING":
            return self._ping(cmd_args)
        elif cmd_name == "SET":
            return self._set(cmd_args)
        elif cmd_name == "GET":
            return self._get(cmd_args)
        elif cmd_name == "DEL":
            return self._del(cmd_args)
        elif cmd_name == "EXISTS":
            return self._exists(cmd_args)
        elif cmd_name == "KEYS":
            return self._keys(cmd_args)
        elif cmd_name == "LPUSH":
            return self._lpush(cmd_args)
        elif cmd_name == "RPUSH":
            return self._rpush(cmd_args)
        elif cmd_name == "LPOP":
            return self._lpop(cmd_args)
        elif cmd_name == "RPOP":
            return self._rpop(cmd_args)
        elif cmd_name == "LRANGE":
            return self._lrange(cmd_args)
        elif cmd_name == "HSET":
            return self._hset(cmd_args)
        elif cmd_name == "HGET":
            return self._hget(cmd_args)
        elif cmd_name == "HDEL":
            return self._hdel(cmd_args)
        else:
            return RESPError(f"ERR unknown command '{cmd_name}'")

    def _ping(self, args: list) -> str:
        if len(args) > 1:
            return RESPError("ERR wrong number of arguments for 'ping' command")
        if len(args) == 1:
            return args[0]
        return "+PONG"  # Returns simple string PONG

    def _set(self, args: list) -> str:
        if len(args) < 2:
            return RESPError("ERR wrong number of arguments for 'set' command")
        
        key = args[0]
        value = args[1]
        ttl = None
        
        # Parse optional EX seconds
        if len(args) > 2:
            if len(args) != 4 or str(args[2]).upper() != "EX":
                return RESPError("ERR syntax error")
            try:
                ttl = float(args[3])
            except ValueError:
                return RESPError("ERR value is not an integer or out of range")
        
        self.db.set(key, value, ttl)
        return "+OK"

    def _get(self, args: list) -> str | None:
        if len(args) != 1:
            return RESPError("ERR wrong number of arguments for 'get' command")
        return self.db.get(args[0])

    def _del(self, args: list) -> int:
        if len(args) < 1:
            return RESPError("ERR wrong number of arguments for 'del' command")
        count = 0
        for key in args:
            if self.db.delete(key):
                count += 1
        return count

    def _exists(self, args: list) -> int:
        if len(args) < 1:
            return RESPError("ERR wrong number of arguments for 'exists' command")
        count = 0
        for key in args:
            if self.db.exists(key):
                count += 1
        return count

    def _keys(self, args: list) -> list[str]:
        if len(args) > 1:
            return RESPError("ERR wrong number of arguments for 'keys' command")
        return self.db.keys()

    def _lpush(self, args: list) -> int | RESPError:
        if len(args) < 2:
            return RESPError("ERR wrong number of arguments for 'lpush' command")
        try:
            return self.db.lpush(args[0], args[1:])
        except TypeError as e:
            return RESPError(str(e))

    def _rpush(self, args: list) -> int | RESPError:
        if len(args) < 2:
            return RESPError("ERR wrong number of arguments for 'rpush' command")
        try:
            return self.db.rpush(args[0], args[1:])
        except TypeError as e:
            return RESPError(str(e))

    def _lpop(self, args: list) -> str | None | RESPError:
        if len(args) != 1:
            return RESPError("ERR wrong number of arguments for 'lpop' command")
        try:
            return self.db.lpop(args[0])
        except TypeError as e:
            return RESPError(str(e))

    def _rpop(self, args: list) -> str | None | RESPError:
        if len(args) != 1:
            return RESPError("ERR wrong number of arguments for 'rpop' command")
        try:
            return self.db.rpop(args[0])
        except TypeError as e:
            return RESPError(str(e))

    def _lrange(self, args: list) -> list[str] | RESPError:
        if len(args) != 3:
            return RESPError("ERR wrong number of arguments for 'lrange' command")
        try:
            start = int(args[1])
            stop = int(args[2])
        except ValueError:
            return RESPError("ERR value is not an integer or out of range")
        try:
            return self.db.lrange(args[0], start, stop)
        except TypeError as e:
            return RESPError(str(e))

    def _hset(self, args: list) -> int | RESPError:
        if len(args) < 3 or len(args) % 2 == 0:
            return RESPError("ERR wrong number of arguments for 'hset' command")
        key = args[0]
        fields = {}
        for i in range(1, len(args), 2):
            fields[args[i]] = args[i+1]
        try:
            return self.db.hset(key, fields)
        except TypeError as e:
            return RESPError(str(e))

    def _hget(self, args: list) -> str | None | RESPError:
        if len(args) != 2:
            return RESPError("ERR wrong number of arguments for 'hget' command")
        try:
            return self.db.hget(args[0], args[1])
        except TypeError as e:
            return RESPError(str(e))

    def _hdel(self, args: list) -> int | RESPError:
        if len(args) < 2:
            return RESPError("ERR wrong number of arguments for 'hdel' command")
        try:
            return self.db.hdel(args[0], args[1:])
        except TypeError as e:
            return RESPError(str(e))
