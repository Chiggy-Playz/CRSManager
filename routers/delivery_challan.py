from fastapi import APIRouter, Request, HTTPException
import asyncpg
from typing import List
from datetime import datetime

from utils.models import (
    BuyerDB,
    BuyerIn,
    ProductDB,
    ChallanCache,
    ChallanIn,
    NewChallanInfo,
    GeneralResponse,
)

router = APIRouter(prefix="/delivery_challan", tags=["Delivery Challan"])


@router.get(
    "/buyers",
    status_code=200,
    response_model=List[BuyerDB],
)
async def get_buyers(request: Request, search_term: str = ""):
    """Get all buyers"""
    buyers = []
    for name in request.app.state.cache.buyers:
        if search_term.lower() in name.lower():
            buyers.append(request.app.state.cache.buyers[name])
    return buyers


@router.get(
    "/buyers/{id}",
    responses={
        200: {"model": BuyerDB},
        404: {"detail": "Buyer not found"},
    },
    status_code=200,
    response_model=BuyerDB,
)
async def get_buyer(request: Request, id: int):
    """Get a buyer by its id"""
    buyer = [buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == id]
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer[0]


@router.post(
    "/buyers",
    responses={
        201: {"model": GeneralResponse},
        400: {"detail": "Buyer already exists"},
    },
    status_code=201,
    response_model=GeneralResponse,
)
async def create_buyer(request: Request, buyer: BuyerIn):
    """Create a new buyer"""
    try:
        buyer_id = await request.app.state.db.fetchval(
            """INSERT INTO buyers(name, address, state, gst) VALUES ($1, $2, $3, $4) RETURNING id;""",
            buyer.name,
            buyer.address,
            buyer.state,
            buyer.gst,
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Buyer already exists")
    buyer_details = dict(buyer)
    buyer_details["id"] = buyer_id
    request.app.state.cache.buyers[buyer.name] = BuyerDB(**buyer_details)
    return GeneralResponse(message="Buyer created")


@router.delete(
    "/buyers/{id}",
    responses={
        200: {"model": GeneralResponse},
        404: {"detail": "Buyer not found"},
    },
    status_code=200,
    response_model=GeneralResponse,
)
async def delete_buyer(request: Request, id: int):
    """Delete a buyer"""
    buyer = [buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == id]
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    buyer = buyer[0]
    await request.app.state.db.execute(
        """DELETE FROM buyers WHERE id = $1;""",
        buyer.id,
    )
    del request.app.state.cache.buyers[buyer.name]
    return GeneralResponse(message="Buyer deleted")


@router.put(
    "/buyers/{id}",
    responses={
        200: {"model": GeneralResponse},
        404: {"detail": "Buyer not found"},
    },
    status_code=200,
    response_model=GeneralResponse,
)
async def update_buyer(request: Request, id: int, input_buyer: BuyerIn):
    """Update a buyer"""
    buyer = [buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == id]
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    buyer = buyer[0]
    await request.app.state.db.execute(
        """UPDATE buyers SET name = $1, address = $2, state = $3, gst = $4 WHERE id = $5;""",
        input_buyer.name,
        input_buyer.address,
        input_buyer.state,
        input_buyer.gst,
        id,
    )
    new_buyer_info = dict(input_buyer)
    new_buyer_info["id"] = id
    del request.app.state.cache.buyers[buyer.name]
    request.app.state.cache.buyers[input_buyer.name] = BuyerDB(**new_buyer_info)

    return GeneralResponse(message="Buyer updated")


@router.get(
    "/challans",
    status_code=200,
    response_model=List[ChallanCache],
)
async def get_challans(request: Request):
    """Get all challans"""
    return request.app.state.cache.challans


@router.get(
    "/challans/{id}",
    responses={
        200: {"model": ChallanCache},
        404: {"detail": "Challan not found"},
    },
    status_code=200,
    response_model=ChallanCache,
)
async def get_challan(request: Request, id: int):
    """Get a challan by its id"""
    challan = [challan for challan in request.app.state.cache.challans if challan.id == id]
    if not challan:
        raise HTTPException(status_code=404, detail="Challan not found")
    return challan[0]


@router.get(
    "/new_challan_info",
    status_code=200,
    response_model=NewChallanInfo,
)
async def get_new_challan_info(request: Request):
    """Get new challan info"""
    now = datetime.now()
    end_of_fiscal_year = datetime(second=59, minute=59, hour=23, day=31, month=3, year=now.year)
    # If after 31st march
    if now > end_of_fiscal_year:
        session = f"{now.year}-{now.year + 1}"
    else:
        session = f"{now.year - 1}-{now.year}"

    challan_number = await request.app.state.db.fetchval("SELECT COUNT(*) FROM challans WHERE session = $1;", session)
    challan_number += 1
    return NewChallanInfo(
        session=session,
        number=challan_number,
    )


@router.post(
    "/challans",
    status_code=201,
    response_model=GeneralResponse,
)
async def create_challan(request: Request, challan: ChallanIn):
    """Create a new challan"""

    buyer = [buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == challan.buyer_id]
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    buyer = buyer[0]
    inserted_challan = await request.app.state.db.fetchrow(
        """INSERT INTO challans(number, session, buyer_id, delivered_by, vehicle_number, digitally_signed) 
        VALUES ($1, $2, $3, $4, $5, $6) RETURNING *;""",
        challan.number,
        challan.session,
        challan.buyer_id,
        challan.delivered_by,
        challan.vehicle_number,
        challan.digitally_signed,
    )
    await request.app.state.db.executemany(
        """
        INSERT INTO products(challan_id, name, description, quantity, serial_number)
        VALUES ($1, $2, $3, $4, $5);
    """,
        [
            (inserted_challan["id"], product.name, product.description, product.quantity, product.serial_number,)
            for product in challan.products
        ],
    )
    challan_details = dict(inserted_challan)
    challan_details["buyer"] = buyer
    challan_details["products"] = [
        ProductDB(challan_id=inserted_challan["id"], **dict(product)) for product in challan.products
    ]
    request.app.state.cache.challans.append(ChallanCache(**challan_details))
    return GeneralResponse(message="Challan created")
