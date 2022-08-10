from fastapi import APIRouter, Request, HTTPException

from utils.models import GeneralResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/sql")
async def run_sql(request: Request):
    query = ";"
    method = request.app.state.db.fetch
    values = await method(query)
    return GeneralResponse(message="SQL executed")

@router.get("/reload_cache")
async def reload_cache(request: Request):
    await request.app.state.cache.load(request.app.state.db)
    return GeneralResponse(message="Cache reloaded")