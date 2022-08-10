from typing import List, Dict
from itertools import groupby

from utils.models import BuyerDB, ChallanDB, ProductDB, ChallanCache


class Cache:

    buyers: Dict[str, BuyerDB]
    challans: List[ChallanCache]

    async def load_cache(self, db):
        self.buyers = {row["name"]: BuyerDB(**row) for row in await db.fetch("SELECT * FROM buyers")}
        self.challans = []
        
        query = """
            SELECT {} FROM challans c JOIN products p ON c.id = p.challan_id JOIN buyers b ON c.buyer_id = b.id;
        """.format(
            ", ".join(
                [f'b.{buyer_field} AS "b.{buyer_field}"' for buyer_field in BuyerDB.__fields__] + 
                [f'c.{challan_field} AS "c.{challan_field}"' for challan_field in ChallanDB.__fields__] +
                [f'p.{product_field} AS "p.{product_field}"' for product_field in ProductDB.__fields__]
            )
        ).strip()

        raw_challans = await db.fetch(query)

        for challan_id, challans in groupby(raw_challans, lambda challan: challan["c.id"]):
            products = []
            challan = None

            for challan in challans:
                products.append(ProductDB(**{product_field: challan["p." + product_field] for product_field in ProductDB.__fields__}))
            
            # There will always be at least one challan in challans, since
            # every challan will have at least one product
            assert challan

            buyer = BuyerDB(**{buyer_field: challan["b." + buyer_field] for buyer_field in BuyerDB.__fields__})
            challan_values = {challan_field: challan["c." + challan_field] for challan_field in ChallanDB.__fields__}
            challan_values.update({"buyer": buyer, "products": products})
            challan = ChallanCache(**challan_values)
            self.challans.append(challan)
        
        print("Cache loaded")