from app.auth.dependencies import get_current_user_id
from app.utils.security import create_access_token, hash_password, verify_password


def test_password_hash_and_verify():
    password_hash = hash_password("password123")

    assert verify_password("password123", password_hash)
    assert not verify_password("wrong", password_hash)


def test_get_current_user_id_from_bearer_token():
    token = create_access_token(subject="42", secret_key="dev-secret", expires_minutes=15)

    user_id = get_current_user_id(authorization=f"Bearer {token}")
    assert user_id == 42