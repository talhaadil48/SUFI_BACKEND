from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.jwt_handler import get_current_user
from utils.hashing import hash_password

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


class SubAdminCreateRequest(BaseModel):
    email: str
    name: str
    password: str
    permissions: dict

class SubAdminUpdateRequest(BaseModel):
    id: int
    name: str | None = None
    password: str | None = None
    permissions: dict | None = None

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


@router.post("/register")
def register_subadmin(
    data: SubAdminCreateRequest,
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can register sub-admins")

    if db.get_user_by_email(data.email):
        raise HTTPException(status_code=400, detail="Sub-admin already exists")

    hashed = hash_password(data.password)

    user = db.create_subadmin(
        email=data.email,
        name=data.name,
        password_hash=hashed,
        permissions=data.permissions
    )

    return {"message": "Sub-admin created successfully", "user": user}


@router.put("/update")
def update_subadmin(
    data: SubAdminUpdateRequest,
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update sub-admins")

    user = db.get_user_by_id(data.id)
    if not user or user["role"] != "sub-admin":
        raise HTTPException(status_code=404, detail="Sub-admin not found")

    hashed = hash_password(data.password) if data.password else user["password_hash"]

    updated_user = db.update_subadmin(
        id=data.id,
        name=data.name or user["name"],
        password_hash=hashed,
        permissions=data.permissions or user["permissions"]
    )

    return {"message": "Sub-admin updated successfully", "user": updated_user}


@router.delete("/delete/{user_id}")
def delete_subadmin(
    user_id: int,
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete sub-admins")

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "sub-admin":
        raise HTTPException(status_code=404, detail="Sub-admin not found")

    db.delete_user_by_id(user_id)
    return {"message": "Sub-admin deleted successfully"}


@router.get("/all")
def get_all_subadmins(
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view sub-admins")

    subadmins = db.get_all_subadmins()
    return {"subadmins": subadmins}
