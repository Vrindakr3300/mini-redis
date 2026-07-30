class RESPError(Exception):
    """Represents a Redis protocol error."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def to_resp(self) -> bytes:
        return f"-{self.message}\r\n".encode("utf-8")

def serialize(value) -> bytes:
    """Converts Python data types into raw RESP bytes."""
    if value is None:
        return b"$-1\r\n"
    
    if isinstance(value, RESPError):
        return value.to_resp()
    
    if isinstance(value, Exception):
        return f"-ERR {str(value)}\r\n".encode("utf-8")
    
    if isinstance(value, bool):
        return b":1\r\n" if value else b":0\r\n"
    
    if isinstance(value, int):
        return f":{value}\r\n".encode("utf-8")
    
    if isinstance(value, str):
        # Differentiate between formatted simple strings and bulk strings
        if value.startswith("+") and value.endswith("\r\n"):
            return value.encode("utf-8")
        if value.startswith("+"):
            return f"{value}\r\n".encode("utf-8")
        return f"${len(value)}\r\n{value}\r\n".encode("utf-8")
    
    if isinstance(value, bytes):
        return f"${len(value)}\r\n".encode("utf-8") + value + b"\r\n"
    
    if isinstance(value, (list, tuple)):
        parts = [f"*{len(value)}\r\n".encode("utf-8")]
        for item in value:
            parts.append(serialize(item))
        return b"".join(parts)
    
    # Fallback to string serialization
    str_val = str(value)
    return f"${len(str_val)}\r\n{str_val}\r\n".encode("utf-8")
