from fastapi import APIRouter, Request, HTTPException

from utils.models import BuyerIn

router = APIRouter(prefix="/delivery_challan")


@router.get("/buyers")
async def get_buyers(request: Request, q: str = ""):

    buyers = []
    for name in request.app.state.cache.buyers:
        if q.lower() in name.lower():
            buyers.append(request.app.state.cache.buyers[name])
    return buyers


@router.get("/buyers/{id}")
async def get_buyer(request: Request, id: int):
    buyer = [buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == id] or None
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer[0]
