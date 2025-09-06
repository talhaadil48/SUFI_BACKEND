from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.jwt_handler import get_current_user

router = APIRouter(
    prefix="/vocalists",
    tags=["Vocalists"],
    dependencies=[Depends(get_current_user)]
)

class SubmitVocalistProfile(BaseModel):
    vocal_range: str
    languages: List[str]
    sample_title: str
    audio_sample_url: str
    sample_description: str
    experience_background: str
    portfolio: str
    availability: str
    

class KalamApprovalRequest(BaseModel):
    status: str  # 'approved' or 'rejected'
    comments: str = None


@router.post("/submit")
def submit_vocalist_profile(data: SubmitVocalistProfile, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    existing = db.get_vocalist_by_user_id(user_id)
    if existing:
        db.update_vocalist_profile(
            user_id=user_id,
            vocal_range=data.vocal_range,
            languages=data.languages,
            sample_title=data.sample_title,
            audio_sample_url=data.audio_sample_url,
            sample_description=data.sample_description,
            experience_background=data.experience_background,
            portfolio=data.portfolio,
            availability=data.availability
        )
        return {"message": "Vocalist profile updated successfully"}
    else:
        db.create_vocalist_profile(
            user_id=user_id,
            vocal_range=data.vocal_range,
            languages=data.languages,
            sample_title=data.sample_title,
            audio_sample_url=data.audio_sample_url,
            sample_description=data.sample_description,
            experience_background=data.experience_background,
            portfolio=data.portfolio,
            availability=data.availability
        )
        return {"message": "Vocalist profile submitted successfully"}

@router.get("/get/{vocalist_id}")
def get_vocalist_profile(
    vocalist_id: int,
    current_user_id: int = Depends(get_current_user)  # Only returns user ID
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    
    
    # Fetch full user info (id + role) from DB
    user = db.get_user_by_id(current_user_id)  # Make sure this returns a dict with 'id' and 'role'
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["role"] == "vocalist":
        profile = db.get_vocalist_by_user_id(user["id"])
    elif user["role"] == "admin":
        profile = db.get_vocalist_by_user_id(vocalist_id)
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view vocalist profiles")
    
    if not profile:
        raise HTTPException(status_code=404, detail="Vocalist profile not found")
    profile.pop("id", None)  # Remove internal ID before returning
    return profile


@router.get("/is-registered")
def check_vocalist_registration(user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    vocalist = db.is_vocalist_registered(user_id)

    if not vocalist:
        return {"is_registered": False}
    return {"is_registered": True}


@router.get("/kalams")
def get_kalams_by_vocalist(current_user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] not in ["admin", "vocalist"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    

    kalams = db.get_kalams_by_vocalist_id(current_user_id)
    return {"vocalist_id": current_user_id, "kalams": kalams}


@router.post("/kalam/{kalam_id}/approval")
def approve_or_reject_kalam(
    kalam_id: int,
    data: KalamApprovalRequest,
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] not in ["admin", "vocalist"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = db.approve_or_reject_kalam(
        kalam_id=kalam_id,
        status=data.status,
        comments=data.comments,
        by_admin=(user["role"] == "admin")
    )

    if not result:
        raise HTTPException(status_code=404, detail="Kalam submission not found")

    return {"message": f"Kalam {data.status} successfully", "kalam_submission": result}