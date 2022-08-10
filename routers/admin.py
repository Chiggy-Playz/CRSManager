from fastapi import APIRouter, Request, HTTPException

from utils.models import GeneralResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/sql")
async def run_sql(request: Request):
    query = ";"
    method = request.app.state.db.fetch
    values = await method(query)
    return GeneralResponse(message="SQL executed")