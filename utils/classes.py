from typing import List, Dict

from utils.models import BuyerDB, ChallanDB, ProductDB


class Cache:

    buyers: Dict[str, BuyerDB]
    challans: List[ChallanDB]

    async def load_cache(self, db):
        self.buyers = {row["name"]: BuyerDB(**row) for row in await db.fetch("SELECT * FROM buyers")}