"""
AetherDB encryption utilities: AES-256 GCM with password-based key derivation.
"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import os

# Constants for security
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # AES-256


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a key from password and salt using Scrypt."""
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=2**15, r=8, p=1)
    return kdf.derive(password.encode())


def encrypt(plaintext: bytes, password: str) -> bytes:
    """Encrypt data with a password. Returns: salt||nonce||ciphertext."""
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ct


def decrypt(ciphertext: bytes, password: str) -> bytes:
    """Decrypt data with a password. Expects: salt||nonce||ciphertext."""
    salt = ciphertext[:SALT_SIZE]
    nonce = ciphertext[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ct = ciphertext[SALT_SIZE + NONCE_SIZE:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)
