from cryptography.fernet import Fernet
from django.conf import settings

# Initialize Fernet with your key
fernet = Fernet(settings.FERNET_KEY.encode())

def encrypt_text(plaintext: str) -> str:
    """Encrypts and returns a URL-safe base64 string."""
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_text(token: str) -> str:
    """Decrypts the token back to the original plaintext."""
    return fernet.decrypt(token.encode()).decode()
