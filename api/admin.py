from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.jwt_handler import get_current_user

router = APIRouter(
    prefix="/admin/vocalists",
    tags=["Admin"]
)

class VocalistStatusUpdate(BaseModel):
    status: str  # must be "approved" or "rejected"

@router.patch("/{vocalist_id}/status")
def admin_update_vocalist_status(
    vocalist_id: int,
    data: VocalistStatusUpdate,
    current_user_id: int = Depends(get_current_user)  # Only ID
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
   
    # Fetch full user info
    user = db.get_user_by_id(current_user_id)  # must return dict with 'id' and 'role'
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] != "admin" and user["role"] != "sub-admin":
        raise HTTPException(status_code=403, detail="Only admins can update vocalist status")

    if data.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    profile = db.get_vocalist_by_user_id(vocalist_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vocalist profile not found")

    db.update_vocalist_profile(vocalist_id, data.status)
    return {"message": f"Vocalist profile {data.status} successfully"}
