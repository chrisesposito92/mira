"""Tests for Fernet encryption utilities."""

import pytest

from app.m3ter.encryption import decrypt_value, encrypt_value


class TestEncryption:
    def test_round_trip(self, fernet_key):
        plaintext = "my-secret-api-key-12345"
        ciphertext = encrypt_value(plaintext)
        assert ciphertext != plaintext
        assert decrypt_value(ciphertext) == plaintext

    def test_different_ciphertexts(self, fernet_key):
        """Fernet produces unique ciphertexts per call (includes timestamp + IV)."""
        ct1 = encrypt_value("same")
        ct2 = encrypt_value("same")
        assert ct1 != ct2
        assert decrypt_value(ct1) == decrypt_value(ct2) == "same"

    def test_invalid_ciphertext(self, fernet_key):
        with pytest.raises(ValueError, match="Failed to decrypt"):
            decrypt_value("not-valid-base64-ciphertext")

    def test_empty_string(self, fernet_key):
        ciphertext = encrypt_value("")
        assert decrypt_value(ciphertext) == ""
