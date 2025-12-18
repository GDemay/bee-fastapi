"""Tests for security utilities."""

from app.users.security import (
    generate_activation_code,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_hash(self):
        password = "TestPassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_hash_password_produces_different_hashes(self):
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password("WrongPassword123", hashed) is False

    def test_verify_password_empty_password(self):
        hashed = hash_password("TestPassword123")

        assert verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self):
        assert verify_password("password", "invalid_hash") is False

    def test_verify_password_empty_hash(self):
        assert verify_password("password", "") is False


class TestActivationCode:
    def test_generate_activation_code_is_4_digits(self):
        code = generate_activation_code()

        assert len(code) == 4
        assert code.isdigit()

    def test_generate_activation_code_randomness(self):
        codes = {generate_activation_code() for _ in range(100)}

        assert len(codes) > 90

    def test_generate_activation_code_preserves_leading_zeros(self):
        codes = [generate_activation_code() for _ in range(1000)]

        assert all(len(code) == 4 for code in codes)

    def test_generate_activation_code_range(self):
        codes = [generate_activation_code() for _ in range(100)]

        for code in codes:
            assert 0 <= int(code) <= 9999
