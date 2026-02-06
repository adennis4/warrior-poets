#!/usr/bin/env python3
"""
AES-256-CBC encryption for Kalshi credentials.
Each credential is encrypted with a unique IV for security.
"""

import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 32-byte key for AES-256 (provided as 64-char hex string in env)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')


def get_encryption_key() -> bytes:
    """Get the encryption key as bytes."""
    if not ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY environment variable not set")
    return bytes.fromhex(ENCRYPTION_KEY)


def encrypt_credential(plaintext: str, iv: bytes = None) -> tuple[str, str]:
    """
    Encrypt a credential string.

    Args:
        plaintext: The credential to encrypt (API key or private key)
        iv: Optional IV to use (if None, generates a new one)

    Returns:
        Tuple of (ciphertext_base64, iv_base64)
    """
    key = get_encryption_key()
    if iv is None:
        iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    return (
        base64.b64encode(ciphertext).decode('utf-8'),
        base64.b64encode(iv).decode('utf-8')
    )


def decrypt_credential(ciphertext_b64: str, iv_b64: str) -> str:
    """
    Decrypt a credential string.

    Args:
        ciphertext_b64: Base64-encoded ciphertext
        iv_b64: Base64-encoded initialization vector

    Returns:
        Decrypted plaintext string
    """
    key = get_encryption_key()
    ciphertext = base64.b64decode(ciphertext_b64)
    iv = base64.b64decode(iv_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode('utf-8')
