"""Round-trip tests for AES-256-GCM helpers."""

from __future__ import annotations

import os

import pytest

from app.crypto import decrypt, encrypt


def test_encrypt_decrypt_roundtrip():
    key = os.urandom(32)
    plaintext = "sk-ant-api03-secret-token-12345"
    ct = encrypt(plaintext, key)
    assert ct != plaintext
    assert decrypt(ct, key) == plaintext


def test_different_nonce_each_time():
    """Same plaintext, same key → different ciphertext (random nonce)."""
    key = os.urandom(32)
    a = encrypt("hello", key)
    b = encrypt("hello", key)
    assert a != b
    assert decrypt(a, key) == "hello"
    assert decrypt(b, key) == "hello"


def test_wrong_key_fails():
    key1 = os.urandom(32)
    key2 = os.urandom(32)
    ct = encrypt("topsecret", key1)
    with pytest.raises(Exception):  # cryptography.InvalidTag
        decrypt(ct, key2)


def test_empty_string():
    key = os.urandom(32)
    ct = encrypt("", key)
    assert decrypt(ct, key) == ""


def test_unicode():
    key = os.urandom(32)
    ct = encrypt("中文 🔑 secret", key)
    assert decrypt(ct, key) == "中文 🔑 secret"


def test_invalid_key_length():
    short_key = os.urandom(16)
    with pytest.raises(ValueError):
        encrypt("hi", short_key)
    with pytest.raises(ValueError):
        decrypt("ZmFrZQ==", short_key)
