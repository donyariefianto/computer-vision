from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.helpers.session_manager import session_manager
from app.helpers.video_sessions import VideoSession
from app.config import security

video_sessions = {}

class VideoSessionsController:
    async def list_video_sessions(self):
        id_key = "device_id"
        data_credentials = (security.security.load_config())
        data_credentials = data_credentials.get('devices',[])
        merged_dict = {item[id_key]: item for item in data_credentials}
        data_session = session_manager.list_sessions()
        for item in data_session:
            if item[id_key] in merged_dict:
                merged_dict[item[id_key]].update(item)
        return list(merged_dict.values())
    
    async def init(self,stream_url):
        await session_manager.initialize_sessions([
            {
                "device_id": 1,
                "device_name": "Perbatasan Batu",
                "device_type": "vehicle",
                "source": "https://103.135.14.146/enygma/cam105.stream/playlist.m3u8"
            }
        ])
        return {"session_id": "", "status": "Initialized"}
    
    async def start(self,stream_url):
        session = VideoSession(stream_url)
        video_sessions[session.session_id] = session
        
        await session.start()
        return {"session_id": str(session.session_id), "status": "Started"}
    
    async def stop_stream(self,session_id: str):
        session = video_sessions.get(session_id)
        if session:
            await session.stop()
            return JSONResponse({"session_id": session_id, "status": "Stopped"})
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    
    async def delete_stream(self,session_id: str):
        session = video_sessions.pop(session_id, None)
        if session:
            await session.delete()
            return JSONResponse({"session_id": session_id, "status": "Deleted"})
        else:
            raise HTTPException(status_code=404, detail="Session not found")
        
    async def restart_stream(self,session_id: str):
        session = video_sessions.get(session_id)
        if session:
            await session.restart()
            return JSONResponse({"session_id": session_id, "status": "Restarted"})
        else:
            raise HTTPException(status_code=404, detail="Session not found")    
        
    async def check_session(self, session_id: str):
        session = video_sessions.get(session_id)
        if session:
            status = await session.check_status()
            return JSONResponse(status)
        else:
            raise HTTPException(status_code=404, detail="Session not found")

videoSessionsController = VideoSessionsController()