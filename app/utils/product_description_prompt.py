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

def build_product_description_messages(*, product_name: str, attributes: dict[str, Any]) -> list[dict[str, str]]:
    attribute_lines: list[str] = []
    for key, label in ATTRIBUTE_LABELS.items():
        value = attributes.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            serialized = ", ".join(str(item) for item in value)
        else:
            serialized = str(value)
        attribute_lines.append(f"- {label}: {serialized}")

    if not attribute_lines:
        attribute_lines.append("- Дополнительные атрибуты не указаны")

    user_prompt = (
        f"Название товара: {product_name}\n"
        "Атрибуты товара:\n"
        f"{chr(10).join(attribute_lines)}\n\n"
        "Напишите одно готовое к публикации описание товара на русском языке. "
        "Опирайтесь только на переданные атрибуты, не добавляйте вымышленные свойства и упоминайте "
        "только наблюдаемые или явно указанные характеристики товара."
    )
    return [{"role": "user", "content": user_prompt}]
