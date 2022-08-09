import datetime
from turtle import st
from typing import List, Optional

from pydantic import BaseModel


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
    description: str
    quantity: int
    serial_number: str


class ChallanDB(BaseModel):
    id: int
    number: int
    session: str
    buyer_id: int
    products: List[ProductDB]
    received: bool
    delivered_by: str
    vehicle_number: str
    created_at: datetime.datetime
    deleted: bool
