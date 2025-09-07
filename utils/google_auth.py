from google.oauth2 import id_token
from google.auth.transport import requests
from utils.jwt_handler import create_access_token, create_refresh_token
from utils.conv_to_json import user_to_dict
from sql.combinedQueries import Queries
from db.connection import DBConnection
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

def verify_google_token(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "google_id": idinfo.get("sub"),
        }
    except Exception:
        return None

def google_login_or_signup(token: str, role: str):
    user_info = verify_google_token(token)
    if not user_info:
        return None, "Invalid Google token"

    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_email(user_info["email"])
    if not user:
        user = db.create_user(
            email=user_info["email"],
            name=user_info["name"],
            password_hash="",  # No password for Google users
            role=role,
            country="",
            city="",
        )

    access_token = create_access_token({"sub": str(user["id"])})
    refresh_token = create_refresh_token({"sub": str(user["id"])})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            k: v for k, v in user.items() if k not in ("password_hash", "email")
        }
    }, None
