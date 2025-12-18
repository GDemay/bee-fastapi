"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.users.schemas import UserActivateRequest, UserRegisterRequest


class TestUserRegisterRequest:
    def test_valid_registration(self):
        data = UserRegisterRequest(
            email="test@example.com",
            password="TestPassword123",
        )

        assert data.email == "test@example.com"
        assert data.password == "TestPassword123"

    def test_valid_email_with_subdomain(self):
        data = UserRegisterRequest(
            email="test@mail.example.com",
            password="TestPassword123",
        )

        assert data.email == "test@mail.example.com"

    def test_valid_email_with_plus(self):
        data = UserRegisterRequest(
            email="test+tag@example.com",
            password="TestPassword123",
        )

        assert data.email == "test+tag@example.com"

    def test_invalid_email_no_at(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="invalid-email", password="TestPassword123")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_invalid_email_no_domain(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="test@", password="TestPassword123")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_invalid_email_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="", password="TestPassword123")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_password_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="test@example.com", password="Short1")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_password_too_long(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="test@example.com", password="A" * 129 + "a1")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_password_no_uppercase(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="test@example.com", password="testpassword123")

        errors = exc_info.value.errors()
        assert any("uppercase" in str(e["msg"]).lower() for e in errors)

    def test_password_no_lowercase(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="test@example.com", password="TESTPASSWORD123")

        errors = exc_info.value.errors()
        assert any("lowercase" in str(e["msg"]).lower() for e in errors)

    def test_password_no_digit(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(email="test@example.com", password="TestPassword")

        errors = exc_info.value.errors()
        assert any("digit" in str(e["msg"]).lower() for e in errors)

    def test_password_minimum_valid(self):
        data = UserRegisterRequest(
            email="test@example.com",
            password="Abcdefg1",
        )

        assert len(data.password) == 8


class TestUserActivateRequest:
    def test_valid_code(self):
        data = UserActivateRequest(code="1234")

        assert data.code == "1234"

    def test_code_with_leading_zero(self):
        data = UserActivateRequest(code="0123")

        assert data.code == "0123"

    def test_code_all_zeros(self):
        data = UserActivateRequest(code="0000")

        assert data.code == "0000"

    def test_code_all_nines(self):
        data = UserActivateRequest(code="9999")

        assert data.code == "9999"

    def test_code_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            UserActivateRequest(code="123")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_code_too_long(self):
        with pytest.raises(ValidationError) as exc_info:
            UserActivateRequest(code="12345")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_code_non_numeric(self):
        with pytest.raises(ValidationError) as exc_info:
            UserActivateRequest(code="abcd")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_code_with_spaces(self):
        with pytest.raises(ValidationError) as exc_info:
            UserActivateRequest(code="12 4")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_code_with_special_chars(self):
        with pytest.raises(ValidationError) as exc_info:
            UserActivateRequest(code="12-4")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_code_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            UserActivateRequest(code="")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)
