import av
import cv2
import asyncio
import os
from datetime import datetime
from ultralytics import YOLO
from app.config.settings import settings
# from app.helpers.video_sessions import VideoSession

class VideoProcess:
    """Class untuk merepresentasikan satu proses PyAV."""
    def __init__(self, process_id, video_path, model):
        self.process_id = process_id
        self.video_path = video_path
        self.model = model
        self.running = False
        self.start_time = datetime.now()
        self.frame_count = 0
        self.log_file = os.path.join(settings.LOG_FOLDER, f"{process_id}.log")
        self.task = None  # Untuk menyimpan coroutine task

    async def run(self):
        """Memproses video dan menulis log deteksi."""
        try:
            container = av.open(self.video_path)
            self.running = True

            with open(self.log_file, "a") as log:
                log.write(f"\n[{datetime.now()}] Start processing {self.video_path}\n")

            for frame in container.decode(video=0):
                if not self.running:
                    break

                self.frame_count += 1
                img = frame.to_ndarray(format="bgr24")
                results = self.model(img)

                detected_objects = []
                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        label = self.model.names[int(box.cls[0])]
                        detected_objects.append(label)

                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(img, label, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Simpan hasil deteksi ke log
                with open(self.log_file, "a") as log:
                    log.write(f"[{datetime.now()}] Detected: {', '.join(detected_objects)}\n")

                # Preview
                cv2.imshow(f"Process {self.process_id}", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                await asyncio.sleep(0)  # Untuk memastikan event loop tetap berjalan

        except Exception as e:
            with open(self.log_file, "a") as log:
                log.write(f"[{datetime.now()}] ERROR: {str(e)}\n")

        finally:
            self.running = False
            cv2.destroyWindow(f"Process {self.process_id}")

    def stop(self):
        """Menghentikan proses berjalan."""
        self.running = False


class VideoProcessor:
    """Manajemen banyak proses PyAV."""
    def __init__(self):
        self.processes = {}
        self.model = YOLO("yolo11n.pt")

    def start(self, process_id: str, video_path: str):
        """Memulai proses baru."""
        if process_id in self.processes:
            return {"status": "error", "message": "Process ID already running."}

        process = VideoProcess(process_id, video_path, self.model)
        task = asyncio.create_task(process.run())
        process.task = task
        self.processes[process_id] = process

        return {"status": "started", "process_id": process_id}

    def stop(self, process_id: str):
        """Menghentikan proses tertentu."""
        if process_id in self.processes:
            self.processes[process_id].stop()
            return {"status": "stopped", "process_id": process_id}
        return {"status": "error", "message": "Process ID not found."}

    def list_processes(self):
        """Daftar semua proses aktif."""
        return [
            {
                "process_id": proc.process_id,
                "status": "running" if proc.running else "stopped",
                "start_time": proc.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "frame_count": proc.frame_count
            }
            for proc in self.processes.values()
        ]

    def get_logs(self, process_id: str):
        """Mengambil log proses."""
        log_file = os.path.join(settings.LOG_FOLDER, f"{process_id}.log")
        try:
            with open(log_file, "r") as log:
                return log.readlines()[-10:]  # Last 10 log lines
        except FileNotFoundError:
            return []

video_processor = VideoProcessor()
