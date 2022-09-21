import datetime
from typing import List, Optional

from pydantic import BaseModel


class GeneralResponse(BaseModel):

    message: str


class BuyerIn(BaseModel):
    name: str
    address: str
    state: str
    gst: Optional[str] = None
    alias: str = ""

class BuyerDB(BaseModel):
    id: int
    name: str
    address: str
    state: str
    alias: str
    gst: Optional[str] = None

class ProductIn(BaseModel):
    description: str
    quantity: int
    comments: Optional[str] = None
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
    product_value: int
    notes: str

class ChallanCache(ChallanDB):
    buyer: BuyerDB
    products: List[ProductDB]

# Cancelled and received not taken since the challan is just created
class ChallanIn(BaseModel):
    number: int
    session: str
    buyer_id: int
    delivered_by: str
    vehicle_number: str
    digitally_signed: bool
    products: List[ProductIn]
    product_value: int
    notes: str = ''

class ChallanUpdate(BaseModel):
    number: Optional[int] = None
    session: Optional[str] = None
    buyer_id: Optional[int] = None
    received: Optional[bool] = None
    delivered_by: Optional[str] = None
    vehicle_number: Optional[str] = None
    digitally_signed: Optional[bool] = None
    cancelled: Optional[bool] = None
    products: Optional[List[ProductIn]] = None
    product_value: str
    notes: str

class NewChallanInfo(BaseModel):
    number: int
    session: str