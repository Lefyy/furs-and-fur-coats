from infrastructure.db.repositories import UserRepository


def test_user_repository_create_and_lookup(db_session):
    repository = UserRepository(db_session)

    user = repository.create(email="test@example.com", phone="79000000000", password_hash="hash")

    assert user.id is not None
    assert repository.get_by_email("test@example.com").id == user.id
    assert repository.get_by_phone("79000000000").id == user.id


def test_user_repository_attach_oauth_account(db_session):
    repository = UserRepository(db_session)

    user = repository.create(email="oauth@example.com", phone="79000000001", password_hash="hash")
    updated = repository.attach_oauth_account(user_id=user.id, provider="yandex", oauth_subject="sub1")

    assert updated.id == user.id
    found = repository.get_by_oauth(provider="yandex", oauth_subject="sub1")
    assert found is not None
    assert found.id == user.id
    assert len(found.oauth_accounts) == 1