import asyncio
import uuid
from fastapi import APIRouter, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from app.controllers.video_controller import video_processor
from app.controllers.video_session import videoSessionsController
from app.helpers.websocket_manager import websocket_manager
from app.helpers.session_manager import session_manager

router = APIRouter()

# -------------------------------
# 🌐 FastAPI Controller Endpoints
# -------------------------------

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    session = session_manager.sessions.get(session_id)
    if not session:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return
    session.websocket = websocket

    try:
        while True:
            await websocket.receive_text()
            # await asyncio.sleep(0)
    except WebSocketDisconnect:
        session.websocket = None
        print(f"WebSocket disconnected for session {session_id}")
    finally:
        await websocket.close()

@router.websocket("/socket/{session}")
async def sockets_endpoint(websocket: WebSocket, session: str):
    await websocket_manager.connect(websocket, session)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(session)
    finally:
        await websocket.close()

@router.get("/test-socket/{session}")
async def test_socket(session: str):
    await websocket_manager.send_personal_message("Hello", session)
    return JSONResponse({"message": "Sent"})

@router.post("/list-video-session/")
async def list_video_session():
    response = await videoSessionsController.list_video_sessions()
    return JSONResponse(response)

# @router.post("/init-video-session/")
# async def init_video_session(stream_url: str):
#     """Memulai proses baru."""
#     responses = await videoSessionsController.init(stream_url)
#     return JSONResponse(responses)

@router.post("/start-video-session/")
async def start_video_session(request: Request):
    payload = await request.json()
    session_id = payload.get("session_id")
    responses = await session_manager.start_session(session_id)
    return responses

@router.post("/stop-video-session/")
async def stop_video_session(request: Request):
    payload = await request.json()
    session_id = payload.get("session_id")
    responses = await session_manager.stop_session(session_id)
    return JSONResponse(responses)

@router.get("/feed-video-session/{session_id}")
async def feed_video_session(session_id: str):
    responses = await session_manager.video_feed(session_id)
    return StreamingResponse(responses,media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/single-feed-video-session/{session_id}")
async def feed_video_session(session_id: str):
    responses = await session_manager.single_video_feed(session_id)
    return StreamingResponse(responses,media_type="image/webp")

@router.post("/start/")
async def start_video(process_id: str = Form(...), video_path: str = Form(...)):
    """Memulai proses baru."""
    response = video_processor.start(process_id, video_path)
    return JSONResponse(response)

@router.post("/stop/")
async def stop_video(process_id: str = Form(...)):
    """Menghentikan proses berdasarkan process_id."""
    response = video_processor.stop(process_id)
    return JSONResponse(response)

@router.get("/processes/")
async def list_processes():
    """List semua proses aktif."""
    return JSONResponse(video_processor.list_processes())

@router.get("/logs/")
async def get_logs(process_id: str):
    """Mengambil log untuk proses tertentu."""
    logs = video_processor.get_logs(process_id)
    return JSONResponse({"logs": logs})
