from __future__ import annotations

from dataclasses import dataclass, fields

_NO_ATTRIBUTES_LINE = "- Дополнительные атрибуты не указаны"
_DESCRIPTION_INSTRUCTION = (
    "Напишите одно готовое к публикации описание товара на русском языке. "
    "Опирайтесь только на переданные атрибуты, не добавляйте вымышленные свойства и "
    "упоминайте только наблюдаемые или явно указанные характеристики товара."
)

PromptValue = str | list[str] | None


@dataclass(slots=True)
class ProductPromptContext:
    brand: PromptValue = None
    fur_type: PromptValue = None
    color: PromptValue = None
    length: PromptValue = None
    size_range: PromptValue = None
    features: PromptValue = None
    material_composition: PromptValue = None
    target_audience: PromptValue = None
    season: PromptValue = None
    style_tags: PromptValue = None
    price: PromptValue = None
    category_name: PromptValue = None
    parent_category_name: PromptValue = None
    category_path: PromptValue = None


ATTRIBUTE_LABELS: dict[str, str] = {
    "brand": "Бренд",
    "fur_type": "Тип меха",
    "color": "Цвет",
    "length": "Длина",
    "size_range": "Размерный ряд",
    "features": "Особенности",
    "material_composition": "Состав материалов",
    "target_audience": "Для кого",
    "season": "Сезон",
    "style_tags": "Теги стиля",
    "price": "Цена",
    "category_name": "Категория",
    "parent_category_name": "Родительская категория",
    "category_path": "Путь категории",
}

def _is_empty_prompt_value(value: PromptValue) -> bool:
    return value in (None, "", [])


def _serialize_prompt_value(value: str | list[str]) -> str:
    if isinstance(value, list):
        return ", ".join(value)
    return value

def _build_attribute_lines(context: ProductPromptContext) -> list[str]:
    attribute_lines: list[str] = []
    normalized_attributes = {
        field.name: getattr(context, field.name)
        for field in fields(ProductPromptContext)
    }
    for key, label in ATTRIBUTE_LABELS.items():
        value = normalized_attributes[key]
        if _is_empty_prompt_value(value):
            continue
        serialized = _serialize_prompt_value(value)
        attribute_lines.append(f"- {label}: {serialized}")

    if not attribute_lines:
        return [_NO_ATTRIBUTES_LINE]
    return attribute_lines


def _build_user_prompt(*, product_name: str, attribute_lines: list[str]) -> str:
    attributes_block = "\n".join(attribute_lines)
    return (

        f"Название товара: {product_name}\n"
        "Атрибуты товара:\n"
        f"{attributes_block}\n\n"
        f"{_DESCRIPTION_INSTRUCTION}"
    )

def build_product_description_messages(*, product_name: str, context: ProductPromptContext) -> list[dict[str, str]]:
    attribute_lines = _build_attribute_lines(context)
    user_prompt = _build_user_prompt(product_name=product_name, attribute_lines=attribute_lines)
    return [{"role": "user", "content": user_prompt}]
