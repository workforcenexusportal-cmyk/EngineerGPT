"""Password hashing round-trip (guards the bcrypt integration)."""

from __future__ import annotations

from app.core.security import hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("s3cret-password!")
    assert hashed != "s3cret-password!"
    assert verify_password("s3cret-password!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_over_72_bytes_is_handled() -> None:
    long_pw = "a" * 200
    hashed = hash_password(long_pw)
    assert verify_password(long_pw, hashed)
