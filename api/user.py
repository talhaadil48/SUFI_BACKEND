from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from utils.hashing import hash_password, verify_password
from utils.jwt_handler import verify_token,get_current_user
from sql.combinedQueries import Queries
from db.connection import DBConnection
from typing import List, Optional



router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_current_user)]
)


class GuestPostCreate(BaseModel):
    title: str
    role: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    user_id: str = Depends(get_current_user)  # optional if you need user_id
):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(data.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    hashed_new = hash_password(data.new_password)
    db.update_password(user["email"], hashed_new)

    return {"message": "Password changed successfully"}








@router.post("/create-blog")
def create_guest_post(
    data: GuestPostCreate,
    user_id: str = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    
    try:
        post_id = db.create_guest_post(
            user_id=user_id,
            title=data.title,
            role=data.role,
            city=data.city,
            country=data.country,
            date=data.date,
            category=data.category,
            excerpt=data.excerpt,
            content=data.content,
            tags=data.tags
        )
        return {"message": "Guest post created successfully", "post_id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/guest-blogs", response_model=List[dict])
def get_user_guest_posts(
    user_id: str = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    
    try:
        return db.fetch_user_guest_posts(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))