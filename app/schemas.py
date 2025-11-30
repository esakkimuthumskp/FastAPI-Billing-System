from pydantic import BaseModel
from typing import List, Optional


class ItemCreate(BaseModel):
    product_id: str
    quantity: int


class PurchaseCreate(BaseModel):
    customer_email: str
    items: List[ItemCreate]
    paid_amount: float
