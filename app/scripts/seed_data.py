from __future__ import annotations

from decimal import Decimal
from itertools import cycle
import os

from sqlalchemy import func, select

from app.utils.security import hash_password
from infrastructure.db.db_session import SessionLocal
from infrastructure.db.models import Category, OrderStatus, Product, User
from infrastructure.db.models.order_status import OrderStatusName


PRODUCT_TARGET_COUNT = 100
DEFAULT_ADMIN_EMAIL = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PHONE = os.getenv("SUPERUSER_PHONE", "79990000000")
DEFAULT_ADMIN_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "admin12345")

ROOT_CATEGORIES = ["Women", "Men", "Accessories"]
CHILD_CATEGORIES = {
    "Women": ["Mink Fur Coats", "Fox Fur Coats"],
    "Men": ["Shearling Jackets", "Winter Parkas"],
    "Accessories": ["Fur Hats", "Leather Gloves"],
}

COLORS = ["black", "graphite", "brown", "ivory", "emerald"]
FUR_TYPES = ["mink", "fox", "shearling", "sable", "alpaca"]
LENGTHS = ["short", "midi", "maxi"]
SEASONS = ["winter", "demi-season"]
AUDIENCES = ["women", "men", "unisex"]
STYLE_TAGS = [["classic", "premium"], ["modern", "minimal"], ["luxury", "warm"]]
FEATURE_SETS = [["hood", "belt"], ["waterproof lining", "stand collar"], ["detachable hood", "zip pockets"]]
BRANDS = ["Sever Luxe", "Arctic Atelier", "Nordic Line", "Velvet Frost"]
IMAGE_URL_TEMPLATE = "https://placehold.co/600x800?text=Fur+Product+{index}"
ORDER_STATUSES = [status.value for status in OrderStatusName]


def ensure_order_statuses(session) -> list[OrderStatus]:
    statuses_by_name = {status.name: status for status in session.scalars(select(OrderStatus)).all()}
    created = False

    for status_name in ORDER_STATUSES:
        if status_name in statuses_by_name:
            continue
        status = OrderStatus(name=status_name)
        session.add(status)
        session.flush()
        statuses_by_name[status_name] = status
        created = True

    if created:
        session.commit()

    return [statuses_by_name[name] for name in ORDER_STATUSES]


def ensure_categories(session) -> list[Category]:
    categories_by_name = {category.name: category for category in session.scalars(select(Category)).all()}
    created = False

    for root_name in ROOT_CATEGORIES:
        if root_name not in categories_by_name:
            category = Category(name=root_name)
            session.add(category)
            session.flush()
            categories_by_name[root_name] = category
            created = True

        root = categories_by_name[root_name]
        for child_name in CHILD_CATEGORIES[root_name]:
            if child_name in categories_by_name:
                continue
            child = Category(name=child_name, parent_id=root.id)
            session.add(child)
            session.flush()
            categories_by_name[child_name] = child
            created = True

    if created:
        session.commit()

    return [categories_by_name[name] for names in CHILD_CATEGORIES.values() for name in names]


def ensure_superuser(session) -> User:
    user = session.scalar(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
    if user is None:
        user = User(
            email=DEFAULT_ADMIN_EMAIL,
            email_raw=DEFAULT_ADMIN_EMAIL,
            phone=DEFAULT_ADMIN_PHONE,
            phone_raw=DEFAULT_ADMIN_PHONE,
            contacts_enrichment_status="formatted",
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            is_staff=True,
        )
        session.add(user)
        session.commit()
        return user

    changed = False
    if not user.is_staff:
        user.is_staff = True
        changed = True
    if not user.password_hash:
        user.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
        changed = True
    if not user.phone:
        user.phone = DEFAULT_ADMIN_PHONE
        user.phone_raw = DEFAULT_ADMIN_PHONE
        changed = True
    if changed:
        session.commit()
    return user


def ensure_products(session, categories: list[Category]) -> int:
    existing_count = session.scalar(select(func.count(Product.id)))
    if existing_count is None:
        existing_count = 0

    if existing_count >= PRODUCT_TARGET_COUNT:
        return 0

    category_cycle = cycle(categories)
    colors = cycle(COLORS)
    fur_types = cycle(FUR_TYPES)
    lengths = cycle(LENGTHS)
    seasons = cycle(SEASONS)
    audiences = cycle(AUDIENCES)
    style_sets = cycle(STYLE_TAGS)
    feature_sets = cycle(FEATURE_SETS)
    brands = cycle(BRANDS)

    created = 0
    for index in range(existing_count + 1, PRODUCT_TARGET_COUNT + 1):
        category = next(category_cycle)
        color = next(colors)
        fur_type = next(fur_types)
        length = next(lengths)
        season = next(seasons)
        audience = next(audiences)
        style_tags = next(style_sets)
        features = next(feature_sets)
        brand = next(brands)
        price = Decimal("89000.00") + Decimal(index * 1250)

        product = Product(
            name=f"{brand} {fur_type.title()} Coat #{index}",
            description=(
                f"Premium {color} {fur_type} outerwear with {length} silhouette, designed for {season} use."
            ),
            old_description=f"Archive description for product #{index}",
            brand=brand,
            fur_type=fur_type,
            color=color,
            length=length,
            size_range="42-52",
            features=features,
            material_composition=f"Outer: {fur_type}; lining: viscose",
            target_audience=audience,
            season=season,
            style_tags=style_tags,
            price=price,
            category_id=category.id,
            image_url=IMAGE_URL_TEMPLATE.format(index=index),
        )
        session.add(product)
        created += 1

    session.commit()
    return created


def main() -> None:
    with SessionLocal() as session:
        statuses = ensure_order_statuses(session)
        categories = ensure_categories(session)
        admin = ensure_superuser(session)
        created_products = ensure_products(session, categories)
        total_products = session.scalar(select(func.count(Product.id))) or 0
        print(
            f"Seed complete: admin={admin.email} is_staff={admin.is_staff}, created_products={created_products}, total_products={total_products}"
            f"Seed complete: admin={admin.email} is_staff={admin.is_staff}, order_statuses={len(statuses)}, created_products={created_products}, total_products={total_products}"
        )


if __name__ == "__main__":
    main()
