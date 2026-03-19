from __future__ import annotations

from typing import Any

PROMPT_VERSION = "v1"

_SYSTEM_PROMPT = (
    "You write premium ecommerce product descriptions for a fur coat boutique. "
    "Keep the tone clear, elegant, and specific to the provided product attributes."
)


ATTRIBUTE_LABELS = {
    "brand": "Brand",
    "fur_type": "Fur type",
    "color": "Color",
    "length": "Length",
    "size_range": "Size range",
    "features": "Features",
    "material_composition": "Material composition",
    "target_audience": "Target audience",
    "season": "Season",
    "style_tags": "Style tags",
    "price": "Price",
    "category_id": "Category ID",
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
        attribute_lines.append("- No additional attributes provided")

    attributes_block = "\n".join(attribute_lines)
    user_prompt = (
        f"Product name: {product_name}\n"
        "Product attributes:\n"
        f"{attributes_block}\n\n"
        "Write one polished product description in Russian for an ecommerce admin panel. "
        "Mention tangible characteristics only, avoid hallucinations, and keep it ready to publish."
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
