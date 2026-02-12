from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PayRequest(BaseModel):
    """Request model for initiating a payment."""
    cart_id: str
    amount: float

class PaymentNotification(BaseModel):
    """Model for payment webhook notifications."""
    transaction_id: str
    amount: float
    timestamp: datetime
    status: str

# You might want to add Product models here later if needed
class Product(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None

class ManualCartItemRequest(BaseModel):
    """Request model for manually adding an item via API."""
    cart_id: str
    product_id: int
    name: str
    price: float
    quantity: int = 1
