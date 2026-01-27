from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Address, Order, OrderItem, Product, User
from schemas import (
    AddressSchema,
    OrderItemSchema,
    OrderResponse,
    OrderSchema,
    UserSchema,
)


async def fetch_order_by_id(
    session: AsyncSession, order_id: int
) -> OrderResponse | None:
    stmt = (
        select(Order, User, Address, OrderItem, Product)
        .join(User, Order.user_id == User.id)
        .join(Address, Order.address_id == Address.id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, OrderItem.product_id == Product.id)
        .where(Order.id == order_id)
    )

    result = await session.execute(stmt)
    rows = result.all()
    if not rows:
        return None

    order, user, address, _, _ = rows[0]

    order_data = OrderSchema(
        id=order.id,
        user_id=order.user_id,
        address_id=order.address_id,
        quantity=order.quantity,
        status=order.status,
        total=order.total,
        created_at=order.created_at,
    )

    user_data = UserSchema(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
    )

    address_data = AddressSchema(
        id=address.id,
        user_id=address.user_id,
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        created_at=address.created_at,
    )

    products: list[OrderItemSchema] = []
    for _, _, _, item, product in rows:
        products.append(
            OrderItemSchema(
                order_item_id=item.id,
                product_id=product.id,
                name=product.name,
                sku=product.sku,
                price=product.price,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        )

    return OrderResponse(
        order=order_data,
        user=user_data,
        address=address_data,
        products=products,
    )


async def fetch_order_lite(
    session: AsyncSession, order_id: int
) -> OrderSchema | None:
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()
    if order is None:
        return None

    return OrderSchema(
        id=order.id,
        user_id=order.user_id,
        address_id=order.address_id,
        quantity=order.quantity,
        status=order.status,
        total=order.total,
        created_at=order.created_at,
    )
