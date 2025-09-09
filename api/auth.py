from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from utils.hashing import hash_password,verify_password
from utils.jwt_handler import create_access_token, create_refresh_token,verify_token
from utils.otp import generate_otp, send_otp_email, get_otp_expiry
from utils.conv_to_json import user_to_dict
from utils.google_auth import google_login_or_signup
from sql.combinedQueries import Queries
from db.connection import DBConnection
from typing import Optional


router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleAuthRequest(BaseModel):
    token: str
    role: Optional[str] = None  # Optional if user exists, required for signup

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str

class SignUpRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str
    country: str
    city: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class ResendOTPRequest(BaseModel):
    email: str
    
    
class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str
    
@router.post("/signup")
def signup(data: SignUpRequest):
    if data.role == "admin":
        raise HTTPException(status_code=403, detail="Cannot sign up as admin")

    conn = DBConnection.get_connection()
    db = Queries(conn)

    if db.get_user_by_email(data.email):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(data.password)
    otp = generate_otp()
    otp_expiry = get_otp_expiry()

    db.create_user_with_otp(
        email=data.email,
        name=data.name,
        password_hash=hashed,
        role=data.role,
        country=data.country,
        city=data.city,
        otp=otp,
        otp_expiry=otp_expiry
    )

    send_otp_email(data.email, otp)
    return {"message": "User created. OTP sent to your email."}


@router.post("/verify-otp")
def verify_otp(data: OTPVerifyRequest):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user, msg = db.verify_otp_and_register(data.email, data.otp)
    
    if not user:
        raise HTTPException(status_code=400, detail=msg)

    access_token = create_access_token({"sub": str(user["id"])})
    refresh_token = create_refresh_token({"sub": str(user["id"])})
   
    

    user_data = {k: v for k, v in user.items() if k not in ("email", "password_hash")}
    return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data
        }



   

@router.post("/resend-otp")
def resend_otp(data: ResendOTPRequest):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if user["is_registered"]:
        raise HTTPException(status_code=400, detail="User already verified")

    otp = generate_otp()
    otp_expiry = get_otp_expiry()
    db.resend_otp(data.email, otp, otp_expiry)
    send_otp_email(data.email, otp)
    return {"message": "OTP resent successfully."}




@router.post("/login")
def login(data: LoginRequest):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    if not user["is_registered"]:
        raise HTTPException(status_code=400, detail="User not verified. Please verify your email first.")
    
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user["id"])})
    refresh_token = create_refresh_token({"sub": str(user["id"])})
   
    

    user_data = {k: v for k, v in user.items() if k not in ("email", "password_hash")}

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_data
    }

# ---------- Forgot Password ----------

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    otp = generate_otp()
    otp_expiry = get_otp_expiry()
    db.resend_otp(data.email, otp, otp_expiry)  # Reuse resend_otp for storing OTP
    send_otp_email(data.email, otp)
    
    return {"message": "OTP sent to your email for password reset"}

# ---------- Reset Password ----------

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    verified_user, msg = db.verify_otp_and_register(data.email, data.otp)
    if not verified_user:
        raise HTTPException(status_code=400, detail=msg)

    hashed = hash_password(data.new_password)
    db.update_password(data.email, hashed)  # You need to implement update_password in UserQueries

    return {"message": "Password reset successfully"}

@router.post("/refresh-token")
def refresh_token(data: RefreshTokenRequest):
    payload = verify_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    conn = DBConnection.get_connection()
    db = Queries(conn)
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access_token = create_access_token({"sub": str(user_id)})

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
    
    
@router.post("/change-password")
def change_password(data: ChangePasswordRequest):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(data.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    hashed_new = hash_password(data.new_password)
    db.update_password(data.email, hashed_new)

    return {"message": "Password changed successfully"}



@router.post("/google-auth")
def google_auth(data: GoogleAuthRequest):
    result, error = google_login_or_signup(data.token, data.role)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result