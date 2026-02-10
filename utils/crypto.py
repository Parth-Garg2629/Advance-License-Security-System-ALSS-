from cryptography.fernet import Fernet
from config import Config


_fernet = Fernet(Config.ENCRYPTION_KEY)


def encrypt_value(value: str) -> str:
    """
    Encrypt a sensitive string.
    """
    return _fernet.encrypt(value.encode()).decode()


def decrypt_value(token: str) -> str:
    """
    Decrypt an encrypted string.
    """
    return _fernet.decrypt(token.encode()).decode()
