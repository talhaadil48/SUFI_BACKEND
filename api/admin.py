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


class KalamResponse(BaseModel):
    title: str
    language: str | None
    theme: str | None
    sufi_influence: str | None
    musical_preference: str | None
    id : int

class KalamByUserResponse(BaseModel):
    title: str
    language: str | None
    theme: str | None
    sufi_influence: str | None
    musical_preference: str | None
    id : int

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    country: str | None
    city: str | None

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



@router.get("/kalams")
def get_all_kalams(
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view kalams")

    query = """
    SELECT title, language, theme, sufi_influence, musical_preference,id
    FROM kalams
    """
    with conn.cursor() as cur:
        cur.execute(query)
        kalams = cur.fetchall()
    
    return {
        "kalams": [
            KalamResponse(
                title=kalam[0],
                language=kalam[1],
                theme=kalam[2],
                sufi_influence=kalam[3],
                musical_preference=kalam[4],
                id=kalam[5]
            ).dict() for kalam in kalams
        ]
    }

@router.get("/kalams/writer/{user_id}")
def get_kalams_by_writer(
    user_id: int,
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view writer kalams")

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "writer":
        raise HTTPException(status_code=404, detail="Writer not found")

    query = """
    SELECT title,language, theme, sufi_influence, musical_preference,id
    FROM kalams
    WHERE writer_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (user_id,))
        kalams = cur.fetchall()
    
    return {
        "kalams": [
            KalamByUserResponse(
                title = kalam[0],
                language=kalam[1],
                theme=kalam[2],
                sufi_influence=kalam[3],
                musical_preference=kalam[4],
                id=kalam[5]
            ).dict() for kalam in kalams
        ]
    }

@router.get("/vocalists")
def get_all_vocalists(
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view vocalists")

    query = """
    SELECT id, email, name, role, country, city
    FROM users
    WHERE role = 'vocalist'
    """
    with conn.cursor() as cur:
        cur.execute(query)
        users = cur.fetchall()
    
    return {
        "vocalists": [
            UserResponse(
                id=user[0],
                email=user[1],
                name=user[2],
                role=user[3],
                country=user[4],
                city=user[5]
            ).dict() for user in users
        ]
    }

@router.get("/writers")
def get_all_writers(
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    current_user = db.get_user_by_id(current_user_id)

    if not current_user or current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view writers")

    query = """
    SELECT id, email, name, role, country, city
    FROM users
    WHERE role = 'writer'
    """
    with conn.cursor() as cur:
        cur.execute(query)
        users = cur.fetchall()
    
    return {
        "writers": [
            UserResponse(
                id=user[0],
                email=user[1],
                name=user[2],
                role=user[3],
                country=user[4],
                city=user[5]
            ).dict() for user in users
        ]
    }