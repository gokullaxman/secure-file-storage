import typing
from cryptography.fernet import Fernet
from flask import current_app

def get_cipher() -> Fernet:
    """
    Retrieves the encryption key from the current app configuration.
    Returns a configured Fernet object.
    Raises ValueError if the configuration is missing or invalid.
    """
    key = current_app.config.get('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY is not set in the configuration.")
    try:
        # Fernet expects bytes or base64 url safe string. 
        # By providing a string, it must be correctly encoded base64.
        if isinstance(key, str):
            key = key.encode('utf-8')
        return Fernet(key)
    except Exception as e:
        raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")

def encrypt_file(file_data: bytes) -> bytes:
    """Encrypts file data using Fernet symmetric encryption."""
    cipher = get_cipher()
    return cipher.encrypt(file_data)

def decrypt_file(encrypted_data: bytes) -> bytes:
    """Decrypts file data using Fernet symmetric encryption."""
    cipher = get_cipher()
    return cipher.decrypt(encrypted_data)
