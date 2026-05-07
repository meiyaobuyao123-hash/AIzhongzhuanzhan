"""AES-256-GCM encryption for upstream API keys.

Each ciphertext is layout: nonce(12) || tag-and-ciphertext, then base64url-encoded.

Why GCM: AEAD (auth + encrypt), no padding, fast, NIST-approved. 12-byte nonce
is the standard for GCM.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt(plaintext: str, master_key: bytes) -> str:
    """Encrypt with AES-256-GCM. Returns urlsafe base64.

    Layout: nonce(12 bytes) || ciphertext-with-tag(N+16 bytes)
    """
    if len(master_key) != 32:
        raise ValueError("master_key must be 32 bytes")
    aesgcm = AESGCM(master_key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return base64.urlsafe_b64encode(nonce + ct).decode("ascii")


def decrypt(ciphertext_b64: str, master_key: bytes) -> str:
    """Inverse of encrypt()."""
    if len(master_key) != 32:
        raise ValueError("master_key must be 32 bytes")
    raw = base64.urlsafe_b64decode(ciphertext_b64.encode("ascii"))
    if len(raw) < 12 + 16:
        raise ValueError("ciphertext too short")
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(master_key)
    pt = aesgcm.decrypt(nonce, ct, associated_data=None)
    return pt.decode("utf-8")
