import io
import os
import cv2
from minio import Minio
from dotenv import load_dotenv
import asyncio

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# 📦 MinIO Client Singleton Class
class MinIOClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = Minio(
                MINIO_ENDPOINT,
                access_key=ACCESS_KEY,
                secret_key=SECRET_KEY,
                secure=False  # Set to True if using HTTPS
            )
        return cls._instance

    def get_client(self):
        return self.client
    
class MinioManager:
    async def initialize_minio():
        minio_client = MinIOClient().get_client()
        
        # Ensure the bucket exists
        found = await asyncio.to_thread(minio_client.bucket_exists, BUCKET_NAME)
        if not found:
            await asyncio.to_thread(minio_client.make_bucket, BUCKET_NAME)
            print(f"🪣 Bucket '{BUCKET_NAME}' created.")
        else:
            print(f"✅ Bucket '{BUCKET_NAME}' already exists.")
    
    async def save_frame_to_minio(frame, frame_id):
        """
        Saves a video frame to MinIO as WEBP format.
        """
        _, buffer = cv2.imencode('.webp', frame, [cv2.IMWRITE_WEBP_QUALITY, 90])  # Convert frame to WEBP
        image_bytes = io.BytesIO(buffer.tobytes())  # Convert to bytes
        object_name = f"{frame_id}.webp"  # Unique file name

        minio_client = MinIOClient().get_client()  # Get MinIO client instance

        # Upload to MinIO asynchronously
        await asyncio.to_thread(
            minio_client.put_object,
            BUCKET_NAME,
            object_name,
            image_bytes,
            length=image_bytes.getbuffer().nbytes,
            content_type="image/webp"
        )

        print(f"✅ Frame {object_name} saved to MinIO.")