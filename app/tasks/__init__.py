from importlib import import_module

__all__ = ["enrich_contact_details", "enrich_order_address", "enrich_user_contacts", "generate_product_description"]

_MODULE_BY_EXPORT = {
    "enrich_contact_details": "app.tasks.enrichment_tasks",
    "enrich_order_address": "app.tasks.enrichment_tasks",
    "enrich_user_contacts": "app.tasks.enrichment_tasks",
    "generate_product_description": "app.tasks.product_description_tasks",
}


def __getattr__(name: str):
    module_name = _MODULE_BY_EXPORT.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name)
    return getattr(module, name)

