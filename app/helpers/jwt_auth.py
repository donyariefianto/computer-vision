import datetime
import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Security
import jwt

JWT_SECRET = os.getenv("JWT_SECRET")
TOKEN_EXPIRY_MINUTES = 60
security = HTTPBearer()

# 🔐 JWT Authentication Class
class JWTAuth:
    @staticmethod
    def create_jwt(user_id: str) -> str:
        """
        Generates JWT token for a user.
        """
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRY_MINUTES),
            "iat": datetime.datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    @staticmethod
    def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
        """
        Verifies JWT token and extracts user_id.
        """
        try:
            token = credentials.credentials
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return payload["user_id"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
