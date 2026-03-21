from decimal import Decimal

from app.services.product_description_generation_service import ProductDescriptionGenerationService
from app.utils.product_description_prompt import (
    ProductPromptContext,
    _build_attribute_lines,
    _is_empty_prompt_value,
    _serialize_prompt_value,
    build_product_description_messages,
)
from infrastructure.db.models import Category, Product


def test_is_empty_prompt_value_supports_blank_variants():
    assert _is_empty_prompt_value(None) is True
    assert _is_empty_prompt_value("") is True
    assert _is_empty_prompt_value([]) is True
    assert _is_empty_prompt_value("0") is False


def test_serialize_prompt_value_supports_lists_and_scalars():
    assert _serialize_prompt_value(["hood", "99.90"]) == "hood, 99.90"
    assert _serialize_prompt_value("10.50") == "10.50"


def test_build_attribute_lines_skips_empty_values_and_serializes_lists():
    lines = _build_attribute_lines(
        ProductPromptContext(
            brand="FurHouse",
            features=["hood", "belt"],
            style_tags=[],
            price="100.00",
        )
    )

    assert lines == [
        "- Бренд: FurHouse",
        "- Особенности: hood, belt",
        "- Цена: 100.00",
    ]


def test_build_product_description_messages_uses_fallback_when_no_attributes():
    messages = build_product_description_messages(product_name="Шуба", context=ProductPromptContext())

    assert messages == [
        {
            "role": "user",
            "content": "Название товара: Шуба\n"
            "Атрибуты товара:\n"
            "- Дополнительные атрибуты не указаны\n\n"
            "Напишите одно готовое к публикации описание товара на русском языке. "
            "Опирайтесь только на переданные атрибуты, не добавляйте вымышленные свойства и упоминайте "
            "только наблюдаемые или явно указанные характеристики товара.",
        }
    ]


def test_serialize_price_formats_decimal_and_other_values():
    assert ProductDescriptionGenerationService._serialize_price(Decimal("100.00")) == "100.00"
    assert ProductDescriptionGenerationService._serialize_price(100) == "100"
    assert ProductDescriptionGenerationService._serialize_price(None) is None

def test_build_prompt_context_uses_readable_category_context():
    root_category = Category(id=1, name="Одежда")
    parent_category = Category(id=2, name="Шубы", parent=root_category)
    category = Category(id=3, name="Норковые", parent=parent_category)
    product = Product(
        name="Шуба из норки",
        price=Decimal("100.00"),
        category_id=category.id,
        category=category,
    )

    context = ProductDescriptionGenerationService._build_prompt_context(product)

    assert context.category_name == "Норковые"
    assert context.parent_category_name == "Шубы"
    assert context.category_path == ["Одежда", "Шубы", "Норковые"]

def test_build_prompt_context_serializes_list_fields():
    product = Product(
        name="Шуба из норки",
        price=Decimal("100.00"),
        category_id=1,
        features=["капюшон", 42, None],
        style_tags=["winter", "luxury"],
    )

    context = ProductDescriptionGenerationService._build_prompt_context(product)

    assert context.features == ["капюшон", "42"]
    assert context.style_tags == ["winter", "luxury"]
