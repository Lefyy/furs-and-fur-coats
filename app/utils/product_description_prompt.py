from __future__ import annotations

from typing import Any

PROMPT_VERSION = "v1"


ATTRIBUTE_LABELS = {
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
    "category_id": "ID категории",
}

def _is_empty_prompt_value(value: Any) -> bool:
    return value in (None, "", [], {})


def _serialize_prompt_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _build_attribute_lines(attributes: dict[str, Any]) -> list[str]:
    attribute_lines: list[str] = []
    for key, label in ATTRIBUTE_LABELS.items():
        value = attributes.get(key)
        if _is_empty_prompt_value(value):
            continue
        serialized = _serialize_prompt_value(value)
        attribute_lines.append(f"- {label}: {serialized}")

    if not attribute_lines:
        return ["- Дополнительные атрибуты не указаны"]
    return attribute_lines


def _build_user_prompt(*, product_name: str, attribute_lines: list[str]) -> str:
    return (

        f"Название товара: {product_name}\n"
        "Атрибуты товара:\n"
        f"{chr(10).join(attribute_lines)}\n\n"
        "Напишите одно готовое к публикации описание товара на русском языке. "
        "Опирайтесь только на переданные атрибуты, не добавляйте вымышленные свойства и упоминайте "
        "только наблюдаемые или явно указанные характеристики товара."
    )

def build_product_description_messages(*, product_name: str, attributes: dict[str, Any]) -> list[dict[str, str]]:
    attribute_lines = _build_attribute_lines(attributes)
    user_prompt = _build_user_prompt(product_name=product_name, attribute_lines=attribute_lines)
    return [{"role": "user", "content": user_prompt}]
