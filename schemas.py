from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class ModelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", check_fields=False)
    def _serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class UserSchema(ModelBase):
    id: int
    email: str
    full_name: str
    created_at: datetime


class AddressSchema(ModelBase):
    id: int
    user_id: int
    line1: str
    line2: str | None
    city: str
    state: str
    postal_code: str
    created_at: datetime


class OrderSchema(ModelBase):
    id: int
    user_id: int
    address_id: int
    quantity: int
    status: str
    total: Decimal
    created_at: datetime

    @field_serializer("total")
    def _serialize_total(self, value: Decimal) -> float:
        return float(value)


class OrderItemSchema(ModelBase):
    order_item_id: int
    product_id: int
    name: str
    sku: str
    price: Decimal
    quantity: int
    unit_price: Decimal

    @field_serializer("price", "unit_price")
    def _serialize_money(self, value: Decimal) -> float:
        return float(value)


class OrderResponse(ModelBase):
    order: OrderSchema
    user: UserSchema
    address: AddressSchema
    products: list[OrderItemSchema]
