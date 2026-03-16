from infrastructure.db.models import Category
from infrastructure.db.repositories import CategoryRepository


def test_get_tree_returns_nested_categories(db_session):
    root = Category(name="Outerwear")
    db_session.add(root)
    db_session.flush()

    child = Category(name="Fur Coats", parent_id=root.id)
    db_session.add(child)
    db_session.flush()

    grandchild = Category(name="Mink", parent_id=child.id)
    db_session.add(grandchild)
    db_session.commit()

    repo = CategoryRepository(session=db_session)
    tree = repo.get_tree()

    assert len(tree) == 1
    assert tree[0]["name"] == "Outerwear"
    assert tree[0]["children"][0]["name"] == "Fur Coats"
    assert tree[0]["children"][0]["children"][0]["name"] == "Mink"