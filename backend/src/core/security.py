import hashlib
import base64
import bcrypt

def _get_hashing_input(password: str) -> str:
    """
    Pre-hash password with SHA-256 to handle arbitrarily long passwords
    and avoid bcrypt's 72-byte limit.
    """
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest()).decode("ascii")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
        
    try:
        # Try verifying with pre-hashed input (new style)
        pwd_input = _get_hashing_input(plain_password).encode("utf-8")
        if bcrypt.checkpw(pwd_input, hashed_password.encode("utf-8")):
            return True
    except Exception:
        pass
        
    try:
        # Fallback: try verifying original password (old style)
        if bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8")):
            return True
    except Exception:
        pass
        
    return False

def get_password_hash(password: str) -> str:
    pwd_input = _get_hashing_input(password).encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_input, salt)
    return hashed.decode("utf-8")
