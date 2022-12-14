from fastapi import FastAPI
import asyncpg
import toml

from utils.classes import Cache

from routers import delivery_challan, admin
from utils.models import GeneralResponse

with open("config.toml", "r") as f:
    config = toml.load(f)

app = FastAPI(
    title="CRSManager",
    version="0.1.0",
    description="CRS Manager's backend server",
    redoc_url="/docs",
    docs_url=None,
    servers=[{"url": "http://localhost:3330", "description": "Local"}],
)


@app.on_event("startup")
async def app_startup():

    app.state.db = await asyncpg.create_pool(**config["DB Info"])
    app.state.cache = Cache()
    await app.state.cache.load(app.state.db)


@app.get("/", response_model=GeneralResponse)
async def ping():
    return GeneralResponse(message="Pong!")


app.include_router(delivery_challan.router)
app.include_router(admin.router)
