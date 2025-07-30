# -------------------------------------
# 🛠️ SessionManager for All Sessions
# -------------------------------------

import json
from fastapi.responses import JSONResponse
from app.helpers.video_sessions import VideoSession

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.recent_captured = {}

    def initialize_socket_recentCapturedData(self):
        return set()
    
    async def initialize_sessions(self, sources):
        # vertical_line_points = ((640, 0), (640, 720))  # Define vertical line points
        # horizontal_line_points = ((0, 360), (1280, 360))  # Define horizontal line points
        for source in sources:
            data_horizontal_line_points = json.loads(source['horizontal_line_points'])
            data_vertical_line_points = json.loads(source['vertical_line_points'])
            result_vertical = tuple((item["x"], item["y"]) for item in data_vertical_line_points)
            result_horizontal = tuple((item["x"], item["y"]) for item in data_horizontal_line_points)
            if self.get_session_by_device_id(source["device_id"]):
                """already initialized. Skipping."""
                continue
            session = VideoSession(source["source"],source["device_id"],source["device_name"],result_horizontal,result_vertical)
            self.sessions[session.session_id] = session
        print(f"Initialized {len(self.sessions)} sessions.")

    def get_session_by_device_id(self, device_id):
        for session in self.sessions.values():
            if session.device_id == device_id:
                return session
        return None
    
    def list_sessions(self):
        return [
            {
                "session_id": session.session_id,
                "device_id": session.device_id,
                "device_name": session.device_name,
                "stream_url": session.stream_url,
                "frame_count": session.frame_count,
                "status": session.is_running
            }
            for session in self.sessions.values()
        ]

    async def video_feed(self, session_id):
        """
        Start a specific session by session_id.
        """
        session = self.sessions.get(session_id)

        if not session:
            return "Session not found"
        return VideoSession.video_feed(session)
    
    async def single_video_feed(self, session_id):
        """
        Start a specific session by session_id.
        """
        session = self.sessions.get(session_id)

        if not session:
            return "Session not found"
        return await VideoSession.get_single_frame(session)
    
    async def start_session(self, session_id):
        """
        Start a specific session by session_id.
        """
        session = self.sessions.get(session_id)
        
        if not session.horizontal_line_points:
            return JSONResponse({"error": "horizontal_line_points is invalid, please fill it in first in the settings menu"},status_code=400)
        
        if not session.vertical_line_points:
            return JSONResponse({"error": "vertical_line_points is invalid, please fill it in first in the settings menu"},status_code=400)
        
        if not session:
            return JSONResponse({"error": "Session not found"},status_code=404)
        
        if session.is_running:
            return JSONResponse({"error": "Session is already running"},status_code=302)
        
        if session and not session.is_running:
            await session.start()
            return JSONResponse({"session_id": session_id, "status": "Started", "messages":"Started"},status_code=200)
        
        return JSONResponse({"error": "Session not found or already running"},status_code=302)

    async def stop_session(self, session_id):
        session = self.sessions.get(session_id)
        
        if not session:
            return {"error": "Session not found"}
        
        if not session.is_running:
            return {"error": "Session is already Stopped"}
        
        if session and session.is_running:
            await session.stop()
            return {"session_id": session_id, "status": "Stopped"}
        
        return {"error": "Session not found or already running"}

    async def clear_sesions(self):
        for session in self.sessions.values():
            if session.is_running:
                await session.stop()
                
# Initialize SessionManager
session_manager = SessionManager()