import uvicorn
import sys
import os

# Menambahkan path proyek ke sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
