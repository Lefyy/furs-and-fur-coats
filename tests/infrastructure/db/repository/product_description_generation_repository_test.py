from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository


def test_product_description_generation_repository_crud_and_active_check(db_session, category_factory, product_factory):
    category = category_factory()
    db_session.add(category)
    db_session.flush()
    product = product_factory(category_id=category.id)
    db_session.add(product)
    db_session.commit()

    repository = ProductDescriptionGenerationRepository(db_session)

    generation = repository.run_in_transaction(lambda: repository.create(product_id=product.id, status="queued"))
    assert generation.id is not None
    assert repository.has_active_generation(product_id=product.id) is True

    fetched = repository.get_by_id(generation.id)
    assert fetched is not None
    assert fetched.status == "queued"

    repository.run_in_transaction(
        lambda: repository.update_status(generation_id=generation.id, status="processing", error_message=None)
    )
    latest = repository.get_latest_by_product_id(product.id)
    assert latest is not None
    assert latest.status == "processing"

    repository.run_in_transaction(
        lambda: repository.save_generation_result(
            generation_id=generation.id,
            generated_text="New description",
            model_name="openai/gpt-4o-mini",
            prompt_version="v1",
            status="completed",
        )
    )
    completed = repository.get_by_id(generation.id)
    assert completed is not None
    assert completed.generated_text == "New description"
    assert completed.status == "completed"
    assert repository.has_active_generation(product_id=product.id) is False

    repository.run_in_transaction(lambda: repository.mark_as_applied(generation_id=generation.id))
    applied = repository.get_by_id(generation.id)
    assert applied is not None
    assert applied.status == "applied"