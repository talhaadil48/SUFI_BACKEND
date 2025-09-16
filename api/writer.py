from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from psycopg2.extras import RealDictCursor
from db import DBConnection  # adjust your import
from utils.jwt_handler import get_current_user
from sql.combinedQueries import Queries
from typing import Optional

router = APIRouter(prefix="/writers", tags=["writers"])

class SubmitWriterProfile(BaseModel):
    writing_styles: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    sample_title: Optional[str] = None
    experience_background: Optional[str] = None
    portfolio: Optional[str] = None
    availability: Optional[str] = None

class WriterApprovalRequest(BaseModel):
    status: str  # 'approved' or 'rejected'
    comments: str = None


# ---------------- Routes ---------------- #

@router.post("/submit")
def submit_writer_profile(data: SubmitWriterProfile, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    existing = db.get_writer_by_user_id(user_id)
    if existing:
        db.update_writer_profile(
            user_id=user_id,
            writing_styles=data.writing_styles,
            languages=data.languages,
            sample_title=data.sample_title,
            experience_background=data.experience_background,
            portfolio=data.portfolio,
            availability=data.availability
        )
        return {"message": "Writer profile updated successfully"}
    else:
        db.create_writer_profile(
            user_id=user_id,
            writing_styles=data.writing_styles,
            languages=data.languages,
            sample_title=data.sample_title,
            experience_background=data.experience_background,
            portfolio=data.portfolio,
            availability=data.availability
        )
        return {"message": "Writer profile submitted successfully"}


@router.get("/get/{writer_id}")
def get_writer_profile(
    writer_id: int,
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] == "writer":
        profile = db.get_writer_by_user_id(user["id"])
    elif user["role"] not in ['sub-admin','admin']:
        profile = db.get_writer_by_user_id(writer_id)
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view writer profiles")

    if not profile:
        raise HTTPException(status_code=404, detail="Writer profile not found")

    profile.pop("id", None)
    return profile


@router.get("/is-registered")
def check_writer_registration(user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    writer = db.is_writer_registered(user_id)

    if not writer:
        return {"is_registered": False}
    return {"is_registered": True}



