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


class ProductIn(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int
    serial_number: Optional[str] = None

class ProductDB(ProductIn):
    challan_id: int

class ChallanDB(BaseModel):
    id: int
    number: int
    session: str
    buyer_id: int
    received: bool = False
    delivered_by: str
    vehicle_number: str
    created_at: datetime.datetime
    cancelled: bool = False
    digitally_signed: bool

class ChallanCache(ChallanDB):
    buyer: BuyerDB
    products: List[ProductDB]

class ChallanIn(BaseModel):
    number: int
    session: str
    buyer_id: int
    delivered_by: str
    vehicle_number: str
    digitally_signed: bool
    products: List[ProductIn]

class NewChallanInfo(BaseModel):
    number: int
    session: str