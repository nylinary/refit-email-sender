from typing import Optional

from pydantic import BaseModel, EmailStr


class WebflowOrderPayload(BaseModel):
    customer_name: Optional[str] = None
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    delivery_method: Optional[str] = None
    customer_comment: Optional[str] = None
    order_total: Optional[str] = None
    order_total_card: Optional[str] = None
    order_total_sbp: Optional[str] = None
    order_items_json: Optional[str] = None
    order_items_text: Optional[str] = None
    order_items_count: Optional[str] = None
    order_source_page: Optional[str] = None
    order_created_at: Optional[str] = None

    class Config:
        extra = "allow"
