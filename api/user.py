from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from utils.hashing import hash_password, verify_password
from utils.jwt_handler import verify_token,get_current_user
from sql.queries import AuthQueries
from db.connection import DBConnection

router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_current_user)]
)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    user_id: str = Depends(get_current_user)  # optional if you need user_id
):
    conn = DBConnection.get_connection()
    db = AuthQueries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(data.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    hashed_new = hash_password(data.new_password)
    db.update_password(user["email"], hashed_new)

    return {"message": "Password changed successfully"}