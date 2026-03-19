import pytest

from app.auth.dependencies import get_current_staff_user, get_current_user_id
from app.exceptions import ForbiddenError, UnauthorizedError
from app.utils.security import create_access_token, hash_password, verify_password
from infrastructure.db.repositories import UserRepository


def test_password_hash_and_verify():
    password_hash = hash_password("password123")

    assert verify_password("password123", password_hash)
    assert not verify_password("wrong", password_hash)


def test_get_current_user_id_from_bearer_token():
    token = create_access_token(subject="42", secret_key="dev-secret", expires_minutes=15)

    user_id = get_current_user_id(authorization=f"Bearer {token}")
    assert user_id == 42


def test_get_current_staff_user_allows_staff_user(db_session):
    user = UserRepository(db_session).create(
        email="staff@example.com",
        email_raw="staff@example.com",
        phone="79990000001",
        phone_raw="79990000001",
        password_hash="hash",
        contacts_enrichment_status="formatted",
        is_staff=True,
    )
    token = create_access_token(subject=str(user.id), secret_key="dev-secret", expires_minutes=15)

    current_user = get_current_staff_user(
        user_id=get_current_user_id(authorization=f"Bearer {token}"),
        user_repository=UserRepository(db_session),
    )

    assert current_user.id == user.id
    assert current_user.is_staff is True


def test_get_current_staff_user_rejects_non_staff_user(db_session):
    user = UserRepository(db_session).create(
        email="user@example.com",
        email_raw="user@example.com",
        phone="79990000002",
        phone_raw="79990000002",
        password_hash="hash",
        contacts_enrichment_status="formatted",
        is_staff=False,
    )
    token = create_access_token(subject=str(user.id), secret_key="dev-secret", expires_minutes=15)

    with pytest.raises(ForbiddenError, match="Staff access required"):
        get_current_staff_user(
            user_id=get_current_user_id(authorization=f"Bearer {token}"),
            user_repository=UserRepository(db_session),
        )


def test_get_current_staff_user_rejects_invalid_token(db_session):
    with pytest.raises(UnauthorizedError, match="Invalid token"):
        get_current_staff_user(
            user_id=get_current_user_id(authorization="Bearer invalid-token"),
            user_repository=UserRepository(db_session),
        )
