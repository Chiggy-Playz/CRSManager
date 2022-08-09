from fastapi import FastAPI
import asyncio
import asyncpg
from typing import Optional
import toml

from utils.classes import Cache

from routers import delivery_challan

with open("config.toml", "r") as f:
    config = toml.load(f)

app = FastAPI()

app = FastAPI(
    title="CRSManager",
    version="0.1.0",
    description="CRS Manager's backend server",
    redoc_url="/docs",
    docs_url=None,
)


@app.on_event("startup")
async def app_startup():

    app.state.db = await asyncpg.create_pool(**config["DB Info"])
    app.state.cache = Cache()
    await app.state.cache.load_cache(app.state.db)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(delivery_challan.router)