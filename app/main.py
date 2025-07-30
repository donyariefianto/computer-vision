import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.helpers.minio_manager import MinioManager
from app.helpers.mongodb_manager import MongoDBClient
from app.routers import video,settings
from app.config import security
from app.helpers.session_manager import session_manager
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
import httpx


# if getattr(sys, 'frozen', False):
#     BASE_DIR = sys._MEIPASS  # PyInstaller menyimpan file sementara di _MEIPASS
# else:
#     # BASE_DIR = os.path.abspath(os.path.dirname(__file__))
#     BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) 
#     # BASE_DIR = Path(__file__).parent.parent.absolute()
    
video_sessions_object = {}
server_url = os.getenv("URL_SERVER")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Fetching configuration...")
    await MinioManager.initialize_minio()
    MongoDBClient().get_database()
    print("✅ MongoDB connection established.")
    security.security.init()
    credentials = security.security.load_config()
    web_token = security.security.load_access_token()
    print(credentials.get('devices',[]))
    await session_manager.initialize_sessions(credentials.get('devices',[]))
    yield
    print("Application shutdown.")
    await session_manager.clear_sesions()

app = FastAPI(lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.parent.absolute() / "static"),
    name="static",
)
templates = Jinja2Templates(directory="templates")

# app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
# templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Registrasi router
app.include_router(video.router)
app.include_router(settings.router)

@app.get("/monitoring")
async def home(request: Request):
    """Menampilkan UI untuk monitoring FFMPEG."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("/login.html", {"request": request})


@app.post("/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        url = server_url+"/v2/authentication/login/"
        auth = await client.post(url, json={"email": email, "password": password})
        if auth.status_code == 200:
            data = auth.json()
            token = data["token"]
            security.security.store_access_token(token)
            
            content = {"message": "Login successful", "success": True}
            response = JSONResponse(content=content)
            response.set_cookie(key="access_token", value=token)
            return response
        else:
            return JSONResponse(content={"message": "Invalid email or password", "success": False})

@app.get("/dashboard")
async def dashboard(request: Request):
    token = request.cookies.get("access_token")
    async with httpx.AsyncClient() as client:
        url = server_url+"/v2/enygma-computer-vision/credentials/"
        check_token = await client.get(url, headers={'Authorization': f'Bearer {token}'})
        if check_token.status_code == 200:
            return templates.TemplateResponse("/dashboard_terbaru.html", {"request": request, "base_url":server_url})
        else:
            response = RedirectResponse(url="/", status_code=303)
            print(response.delete_cookie("access_token"))
            return response
        
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)