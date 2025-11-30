from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: str = Field(index=True, unique=True)
    name: str
    available_stocks: int
    price_per_unit: float
    tax_percentage: float


class Denomination(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    value: int = Field(index=True, unique=True)


class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_email: str
    subtotal: float
    tax: float
    total: float
    paid_amount: float
    change_amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_id: Optional[int] = Field(default=None, foreign_key="purchase.id")
    product_id: str
    product_name: str
    unit_price: float
    quantity: int
    tax_percentage: float
    line_subtotal: float
    line_tax: float
    line_total: float



class PurchaseChange(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_id: Optional[int] = Field(default=None, foreign_key="purchase.id")
    denomination_value: int
    count: int


class PurchasePaidDenomination(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_id: Optional[int] = Field(default=None, foreign_key="purchase.id")
    denomination_value: int
    count: int
