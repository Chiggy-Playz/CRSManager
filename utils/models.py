import datetime
from turtle import st
from typing import List, Optional

from pydantic import BaseModel


class GeneralResponse(BaseModel):

    message: str

class BuyerIn(BaseModel):
    name: str
    address: str
    state: str
    gst: Optional[str] = None


class BuyerDB(BaseModel):
    id: int
    name: str
    address: str
    state: str
    gst: Optional[str] = None


class ProductDB(BaseModel):
    challan_id: int
    name: str
    description: str
    quantity: int
    serial_number: str


class ChallanDB(BaseModel):
    id: int
    challan_number: int
    session: str
    buyer_id: int
    received: bool
    delivered_by: str
    vehicle_number: str
    created_at: datetime.datetime
    cancelled: bool
    digitally_signed: bool

class ChallanCache(ChallanDB):
    buyer: BuyerDB
    products: List[ProductDB]
