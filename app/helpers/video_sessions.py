from collections import defaultdict
from datetime import datetime, timezone
import io
import av
import asyncio
import uuid
import cv2
from app.helpers.minio_manager import MinioManager
from concurrent.futures import ProcessPoolExecutor
from ultralytics import YOLO
from app.helpers.boxmot_tracking import BoxmotTracking

process_pool = ProcessPoolExecutor()

class VideoSession:
    def __init__(self, stream_url: str, device_id: str, device_name: str, horizontal_line_points: any,vertical_line_points:any):
        self.session_id = str(uuid.uuid4())
        self.device_id = device_id
        self.device_name = device_name
        self.stream_url = stream_url
        self.frame_count = 0
        self.websocket = None
        self.task = None
        self.video_feeds = None
        self.is_running = False
        self.model = None
        self.tracker = None
        self.track_histories = defaultdict(list)
        self.crossed_ids = set()
        self.horizontal_line_points = horizontal_line_points
        self.vertical_line_points = vertical_line_points

    async def get_single_frame(self):
        """Ambil satu frame dari kamera"""
        container = await asyncio.to_thread(av.open, self.stream_url)
        video_stream = next(s for s in container.streams if s.type == 'video')

        frame = next(await asyncio.to_thread(lambda: container.decode(video_stream)))
        img = await asyncio.to_thread(frame.to_ndarray, format="bgr24")

        _, buffer = await asyncio.to_thread(cv2.imencode, '.webp', img, [cv2.IMWRITE_WEBP_QUALITY, 80])

        container.close()

        return io.BytesIO(buffer.tobytes())
    
    async def video_feed(self):
        """
        Process the video stream using asyncio task.
        """
        # input_container = av.open(self.stream_url)
        input_container = await asyncio.to_thread(av.open, self.stream_url)
        video_stream = next(s for s in input_container.streams if s.type == 'video')
        try:
            for frame in await asyncio.to_thread(lambda: input_container.decode(video_stream)):
                img = await asyncio.to_thread(frame.to_ndarray, format="bgr24")
                # Encode frame as WEBP
                _, buffer = await asyncio.to_thread(cv2.imencode, '.webp', img, [cv2.IMWRITE_WEBP_QUALITY, 80])

                yield (b'--frame\r\n'
                    b'Content-Type: image/webp\r\n\r\n' +
                    buffer.tobytes() + b'\r\n')

                await asyncio.sleep(0)  # ~80 FPS
        finally:
            print("✅ PyAV container closed.")
            await asyncio.to_thread(input_container.close)  # Tutup PyAV dengan aman

    async def process_stream(self):
        """
        Process the video stream using asyncio task.
        """
        input_container = await asyncio.to_thread(av.open, self.stream_url)
        video_stream = next(s for s in input_container.streams if s.type == 'video')
        try:
            for frame in await asyncio.to_thread(lambda: input_container.decode(video_stream)):
            # for frame in await asyncio.to_thread(lambda: list(input_container.decode(video=0))):
                if not self.is_running:
                    break

                self.frame_count += 1
                img = await asyncio.to_thread(frame.to_ndarray, format="bgr24")
                frame_id = datetime.now(timezone.utc).strftime("%Y-%m-%d")+"/"+str(uuid.uuid4()) 
                await MinioManager.save_frame_to_minio(img, frame_id)
                # detect = BoxmotTracking.process_detections(img,self.model,0.5)
                detect = await asyncio.to_thread(BoxmotTracking.process_detections, img, self.model, 0.5)
                tracks = await asyncio.to_thread(self.tracker.update, detect, img)
                # tracks = self.tracker.update(detect,img) # (x1, y1, x2, y2, obj_conf, class_conf, class_pred)
                for track in tracks:
                    x1=track[0]
                    y1=track[1]
                    x2=track[2]
                    y2=track[3]
                    track_id=track[4] 
                    confidence=track[5]
                    class_id=track[6]
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Calculate center of the bounding box
                    await BoxmotTracking.update_track_crossing(confidence, class_id, track_id, x1, y1, x2, y2, cx, cy, self.vertical_line_points, self.horizontal_line_points, self.track_histories, frame_id, self.crossed_ids, self.model, self.device_name, self.device_id)

                # Send update to websocket if connected
                if self.websocket:
                    await self.websocket.send_json({
                        "session_id": self.session_id,
                        "frame_number": self.frame_count,
                        "status": "Running"
                    })
                
                # print(session_manager.web_session_id[self.web_token])
                await asyncio.sleep(0)

            # input_container.close()
            await asyncio.to_thread(input_container.close)
        finally:
        # Tutup input_container jika masih terbuka
            if input_container:
                print("✅ Video stream closed.")
                await asyncio.to_thread(input_container.close)
            await VideoSession.stop(self)

    async def start(self):
        """
        Start video stream processing.
        """
        
        self.is_running = True
        self.tracker = BoxmotTracking.initial_tracker()
        self.model = YOLO("yolo11n.pt")
        self.frame_count = 0

        loop = asyncio.get_running_loop()
        self.task = loop.create_task(self.process_stream())

    async def stop(self):
        """
        Stop video stream processing.
        """
        self.is_running = False
        self.tracker = None
        self.model = None
        
        # Cancel any active asyncio task
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                print(f"Session {self.session_id} cancelled gracefully.")

    async def delete(self):
        """
        Delete session and clean up.
        """
        await self.stop()

    async def restart(self):
        """
        Restart the video stream.
        """
        await self.stop()
        await self.start()