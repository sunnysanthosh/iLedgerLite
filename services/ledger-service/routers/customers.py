import uuid

from db import get_db
from fastapi import APIRouter, Depends, Query
from models.org import OrgMembership
from schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
    CustomerWithBalance,
)
from services.customer_service import create_customer, get_customer, list_customers, update_customer
from services.security import get_org_member, get_write_member
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["customers"])


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer_endpoint(
    data: CustomerCreate,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    return await create_customer(membership.user_id, membership.org_id, data, db)


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers_endpoint(
    search: str | None = Query(None, description="Search by name, phone, or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    customers_with_balance, total = await list_customers(membership.org_id, db, search=search, skip=skip, limit=limit)
    items = [
        CustomerWithBalance(
            id=c.id,
            user_id=c.user_id,
            name=c.name,
            phone=c.phone,
            email=c.email,
            address=c.address,
            created_at=c.created_at,
            updated_at=c.updated_at,
            outstanding_balance=str(balance),
        )
        for c, balance in customers_with_balance
    ]
    return CustomerListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/customers/{customer_id}", response_model=CustomerWithBalance)
async def get_customer_endpoint(
    customer_id: uuid.UUID,
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    from services.customer_service import _calculate_outstanding_balance

    customer = await get_customer(customer_id, membership.org_id, db)
    balance = await _calculate_outstanding_balance(customer.id, db)
    return CustomerWithBalance(
        id=customer.id,
        user_id=customer.user_id,
        name=customer.name,
        phone=customer.phone,
        email=customer.email,
        address=customer.address,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        outstanding_balance=str(balance),
    )


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer_endpoint(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    return await update_customer(customer_id, membership.org_id, data, db)
