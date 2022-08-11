from fastapi import APIRouter, Request, HTTPException
import asyncpg
from typing import List

from utils.models import BuyerDB, BuyerIn, GeneralResponse

router = APIRouter(prefix="/delivery_challan", tags=["Delivery Challan"])


@router.get(
    "/buyers",
    status_code=200,
    response_model=List[BuyerDB],
)
async def get_buyers(request: Request, search_term: str = ""):

    buyers = []
    for name in request.app.state.cache.buyers:
        if search_term.lower() in name.lower():
            buyers.append(request.app.state.cache.buyers[name])
    return buyers


@router.get(
    "/buyers/{id}",
    status_code=200,
    response_model=BuyerDB,
)
async def get_buyer(request: Request, id: int):
    buyer = [buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == id]
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer[0]


@router.post(
    "/buyers",
    status_code=201,
    response_model=GeneralResponse,
)
async def create_buyer(request: Request, buyer: BuyerIn):
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
    status_code=200,
    response_model=GeneralResponse,
)
async def delete_buyer(request: Request, id: int):
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
    status_code=200,
    response_model=GeneralResponse,
)
async def update_buyer(request: Request, id: int, input_buyer: BuyerIn):
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
