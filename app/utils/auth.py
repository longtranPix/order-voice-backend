import base64
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def encode_credentials(username: str, password: str) -> str:
    """Encode username:password to base64."""
    raw_string = f"{username}:{password}"
    encoded_bytes = base64.b64encode(raw_string.encode("utf-8"))
    return encoded_bytes.decode("utf-8")
