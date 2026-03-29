"""
Password hashing utilities using bcrypt directly.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')

    # Truncate to 72 bytes (bcrypt limitation)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches
    """
    try:
        # Encode passwords to bytes
        password_bytes = plain_password.encode('utf-8')

        # Truncate to 72 bytes (bcrypt limitation)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        hashed_bytes = hashed_password.encode('utf-8')

        # Verify
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False
