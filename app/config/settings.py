import os

class Settings:
    LOG_FOLDER = "logs"
    INSTANCE_FOLDER = "instances"

    os.makedirs(LOG_FOLDER, exist_ok=True)
    os.makedirs(INSTANCE_FOLDER, exist_ok=True)

settings = Settings()
