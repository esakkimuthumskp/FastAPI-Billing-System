from typing import List
from sqlmodel import Session, select
from . import models


def get_product_by_product_id(session: Session, product_id: str):
    return session.exec(select(models.Product).where(models.Product.product_id == product_id)).first()


def list_products(session: Session) -> List[models.Product]:
    return session.exec(select(models.Product)).all()


def list_denominations(session: Session):
    return session.exec(select(models.Denomination).order_by(models.Denomination.value.desc())).all()


def decrease_stock(session: Session, product: models.Product, qty: int):
    product.available_stocks = max(0, product.available_stocks - qty)
    session.add(product)


def create_purchase(session: Session, purchase: models.Purchase, items: List[models.PurchaseItem], changes: List[models.PurchaseChange]):
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    for it in items:
        it.purchase_id = purchase.id
        session.add(it)
    for ch in changes:
        ch.purchase_id = purchase.id
        session.add(ch)
    session.commit()
    return purchase
