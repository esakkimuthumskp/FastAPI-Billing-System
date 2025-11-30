from sqlmodel import Session, select
from .models import Product, Denomination
from .database import engine

def seed():
    with Session(engine) as session:
        p = session.exec(select(Product)).first()
        if p:
            return

        products = [
            Product(product_id="P1001", name="Pen", available_stocks=100, price_per_unit=10.0, tax_percentage=5.0),
            Product(product_id="P1002", name="Notebook", available_stocks=50, price_per_unit=45.0, tax_percentage=12.0),
            Product(product_id="P1003", name="Eraser", available_stocks=200, price_per_unit=5.0, tax_percentage=0.0),
        ]
        denominations = [
            Denomination(value=2000),
            Denomination(value=500),
            Denomination(value=200),
            Denomination(value=100),
            Denomination(value=50),
            Denomination(value=20),
            Denomination(value=10),
            Denomination(value=5),
            Denomination(value=1),
        ]
        for pr in products:
            session.add(pr)
        for d in denominations:
            session.add(d)
        session.commit()
