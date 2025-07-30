from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.config import security

router = APIRouter()

@router.get("/credentials/")
async def list_processes():
    data = security.security.load_config()
    if data.get("status", True) == False:
        return JSONResponse(content={"message": "Error"}, status_code=500)
    return JSONResponse(data)

@router.get("/fetch-credential")
async def fetch_credentials():
    data = await security.security.init_fetch()
    return JSONResponse(data)