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
    ChallanUpdate,
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
            """INSERT INTO buyers(name, address, state, gst, alias) VALUES ($1, $2, $3, $4, $5) RETURNING id;""",
            buyer.name,
            buyer.address,
            buyer.state,
            buyer.gst,
            buyer.alias
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Buyer already exists")
    buyer_details = dict(buyer)
    buyer_details["id"] = buyer_id
    new_buyer = BuyerDB(**buyer_details)
    request.app.state.cache.buyers[buyer.name] = new_buyer
    return new_buyer


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
        """UPDATE buyers SET name = $1, address = $2, state = $3, gst = $4, alias = $5 WHERE id = $6;""",
        input_buyer.name,
        input_buyer.address,
        input_buyer.state,
        input_buyer.gst,
        input_buyer.alias,
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

    challan_number = (
        await request.app.state.db.fetchval("SELECT MAX(number) FROM challans WHERE session = $1;", session)
    ) or 0
    challan_number += 1
    return NewChallanInfo(
        session=session,
        number=challan_number,
    )


@router.post(
    "/challans",
    status_code=201,
    response_model=ChallanCache,
)
async def create_challan(request: Request, challan: ChallanIn):
    """Create a new challan"""

    buyer = [buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == challan.buyer_id]
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    buyer = buyer[0]
    try:
        inserted_challan = await request.app.state.db.fetchrow(
            """INSERT INTO challans(number, session, buyer_id, delivered_by, vehicle_number, digitally_signed, product_value, notes) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *;""",
            challan.number,
            challan.session,
            challan.buyer_id,
            challan.delivered_by,
            challan.vehicle_number,
            challan.digitally_signed,
            challan.product_value,
            challan.notes
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="A challan of same number and session exists.")
    await request.app.state.db.executemany(
        """
        INSERT INTO products(challan_id, description, quantity, comments, serial_number)
        VALUES ($1, $2, $3, $4, $5);
    """,
        [
            (
                inserted_challan["id"],
                product.description,
                product.quantity,
                product.comments,
                product.serial_number,
            )
            for product in challan.products
        ],
    )
    challan_details = dict(inserted_challan)
    challan_details["buyer"] = buyer
    challan_details["products"] = [
        ProductDB(challan_id=inserted_challan["id"], **dict(product)) for product in challan.products
    ]
    new_challan = ChallanCache(**challan_details)
    request.app.state.cache.challans.insert(0, new_challan)
    return new_challan


@router.patch(
    "/challans/{id}",
    responses={
        200: {"model": ChallanCache},
        404: {"detail": "Challan not found"},
        400: {"detail": "Bad request"},
    },
    status_code=200,
    response_model=ChallanCache,
)
async def update_challan(request: Request, id: int, new_challan: ChallanUpdate):
    """Update a challan by its id. Products will be replaced"""
    challans: List[ChallanCache] = [challan for challan in request.app.state.cache.challans if challan.id == id]
    if not challans:
        raise HTTPException(status_code=404, detail="Challan not found")
    challan: ChallanCache = challans[0]

    new_data = new_challan.dict(exclude_unset=True)
    if not new_data:
        raise HTTPException(status_code=400, detail="No data to update")

    if "products" in new_data:
        new_data["products"] = [{**product, "challan_id": id} for product in new_data["products"]]

    async with request.app.state.db.acquire() as connection:
        async with connection.transaction():
            products = new_data.pop("products", None)
            if products is not None:
                if products == []:
                    raise HTTPException(status_code=400, detail="Must have at least one product")

                await connection.execute("""DELETE FROM products WHERE challan_id=$1;""", id)
                await connection.executemany(
                    """
                    INSERT INTO products(description, quantity, comments, serial_number, challan_id) 
                    VALUES ($1, $2, $3, $4, $5);
                """,
                    [
                        (
                            product["description"],
                            product["quantity"],
                            product.get("comments", None),
                            product.get("serial_number", None),
                            id,
                        )
                        for product in products
                    ],
                )

            if new_data:
                try:
                    await connection.execute(
                        """UPDATE challans SET {} WHERE id = $1;""".format(
                            ", ".join(f"{key} = ${idx + 2}" for idx, key in enumerate(new_data.keys()))
                        ),
                        id,
                        *new_data.values(),
                    )
                except asyncpg.ForeignKeyViolationError:
                    raise HTTPException(status_code=400, detail="Buyer doesn't exist")
            
            if products:
                new_data['products'] = [ProductDB(**product) for product in products]

    if "buyer_id" in new_data:
        new_data["buyer"] = [
            buyer for buyer in request.app.state.cache.buyers.values() if buyer.id == new_data["buyer_id"]
        ][0]

    updated_challan = challan.copy(update=new_data)

    for index, challan in enumerate(request.app.state.cache.challans):
        if challan.id == id:
            request.app.state.cache.challans[index] = updated_challan
            break

    return updated_challan
