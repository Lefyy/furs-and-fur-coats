from infrastructure.db.repositories import UserRepository


def test_user_repository_create_and_lookup(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        email="test@example.com",
        email_raw="Test@example.com",
        phone="79000000000",
        phone_raw="+7 900 000-00-00",
        password_hash="hash",
        contacts_enrichment_status="formatted",
        is_staff=False,
    )

    assert user.id is not None
    assert repository.get_by_email("test@example.com").id == user.id
    assert repository.get_by_phone("79000000000").id == user.id
    assert user.email_raw == "Test@example.com"
    assert user.phone_raw == "+7 900 000-00-00"


def test_user_repository_updates_enrichment_fields(db_session):
    repository = UserRepository(db_session)

    user = repository.create(
        email="raw@example.com",
        email_raw="Raw@example.com",
        phone="+7 111",
        phone_raw="+7 111",
        password_hash="hash",
        contacts_enrichment_status="pending_enrichment",
        is_staff=False,
    )

    updated = repository.update_contact_enrichment(
        user_id=user.id,
        email="normalized@example.com",
        phone="79990000000",
        contacts_enrichment_status="formatted",
    )

    assert updated.email == "normalized@example.com"
    assert updated.phone == "79990000000"
    assert updated.contacts_enrichment_status == "formatted"