from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from db.connection import DBConnection
from utils.jwt_handler import get_current_user
from sql.combinedQueries import Queries

# Studio Visit Request Models
class StudioVisitRequestCreate(BaseModel):
    vocalist_id: int
    kalam_id: int
    name: str
    email: str
    organization: Optional[str] = None
    contact_number: Optional[str] = None
    preferred_date: Optional[date] = None
    preferred_time: Optional[str] = None
    purpose: Optional[str] = None
    number_of_visitors: Optional[str] = None
    additional_details: Optional[str] = None
    special_requests: Optional[str] = None

class StudioVisitRequestResponse(BaseModel):
    id: int
    vocalist_id: int
    kalam_id: int
    name: str
    email: str
    organization: Optional[str]
    contact_number: Optional[str]
    preferred_date: Optional[date]
    preferred_time: Optional[str]
    purpose: Optional[str]
    number_of_visitors: Optional[str]
    additional_details: Optional[str]
    special_requests: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

# Remote Recording Request Models
class RemoteRecordingRequestCreate(BaseModel):
    vocalist_id: int
    kalam_id: int
    name: str
    email: str
    city: Optional[str] = None
    country: Optional[str] = None
    time_zone: Optional[str] = None
    role: Optional[str] = None
    project_type: Optional[str] = None
    recording_equipment: Optional[str] = None
    internet_speed: Optional[str] = None
    preferred_software: Optional[str] = None
    availability: Optional[str] = None
    recording_experience: Optional[str] = None
    technical_setup: Optional[str] = None
    additional_details: Optional[str] = None

class RemoteRecordingRequestResponse(BaseModel):
    id: int
    vocalist_id: int
    kalam_id: int
    name: str
    email: str
    city: Optional[str]
    country: Optional[str]
    time_zone: Optional[str]
    role: Optional[str]
    project_type: Optional[str]
    recording_equipment: Optional[str]
    internet_speed: Optional[str]
    preferred_software: Optional[str]
    availability: Optional[str]
    recording_experience: Optional[str]
    technical_setup: Optional[str]
    additional_details: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

router = APIRouter(
    prefix="/requests",
    tags=["Requests"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/studio-visit-request", response_model=StudioVisitRequestResponse)
def create_studio_visit_request(
    data: StudioVisitRequestCreate,
    user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "vocalist":
        raise HTTPException(status_code=403, detail="Only vocalists can create studio visit requests")

    if data.vocalist_id != int(user.get("id")):
        raise HTTPException(status_code=403, detail="Vocalist ID must match authenticated user")

    result = db.create_studio_visit_request(data.dict())
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create studio visit request")

    return StudioVisitRequestResponse(**result)

@router.get("/studio-visit-requests", response_model=list[StudioVisitRequestResponse])
def get_all_studio_visit_requests(user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view all studio visit requests")

    requests = db.get_all_studio_visit_requests()
    return [StudioVisitRequestResponse(**req) for req in requests]

@router.get("/studio-visit-requests/vocalist", response_model=list[StudioVisitRequestResponse])
def get_studio_visit_requests_by_vocalist(user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "vocalist":
        raise HTTPException(status_code=403, detail="Only vocalists can view their studio visit requests")

    requests = db.get_studio_visit_requests_by_vocalist(int(user.get("id")))
    return [StudioVisitRequestResponse(**req) for req in requests]

@router.post("/remote-recording-request", response_model=RemoteRecordingRequestResponse)
def create_remote_recording_request(
    data: RemoteRecordingRequestCreate,
    user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "vocalist":
        raise HTTPException(status_code=403, detail="Only vocalists can create remote recording requests")

    if data.vocalist_id != int(user.get("id")):
        raise HTTPException(status_code=403, detail="Vocalist ID must match authenticated user")

    result = db.create_remote_recording_request(data.dict())
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create remote recording request")

    return RemoteRecordingRequestResponse(**result)

@router.get("/remote-recording-requests", response_model=list[RemoteRecordingRequestResponse])
def get_all_remote_recording_requests(user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view all remote recording requests")

    requests = db.get_all_remote_recording_requests()
    return [RemoteRecordingRequestResponse(**req) for req in requests]

@router.get("/remote-recording-requests/vocalist", response_model=list[RemoteRecordingRequestResponse])
def get_remote_recording_requests_by_vocalist(user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") != "vocalist":
        raise HTTPException(status_code=403, detail="Only vocalists can view their remote recording requests")

    requests = db.get_remote_recording_requests_by_vocalist(int(user.get("id")))
    return [RemoteRecordingRequestResponse(**req) for req in requests]




@router.get("/check-request-exists/{vocalist_id}/{kalam_id}", response_model=bool)
def check_request_exists(vocalist_id: int, kalam_id: int, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Allow only vocalists or admins to check requests
    if user.get("role") not in ["vocalist", "admin"]:
        raise HTTPException(status_code=403, detail="Only vocalists or admins can check request existence")

    # If vocalist, ensure they can only check their own requests
    if user.get("role") == "vocalist" and vocalist_id != int(user.get("id")):
        raise HTTPException(status_code=403, detail="Vocalists can only check their own requests")

    # Check for studio visit request
    studio_conflict = db.check_studio_visit_conflict(vocalist_id, kalam_id, None, None)
    # Check for remote recording request
    remote_conflict = db.check_remote_recording_conflict(vocalist_id, kalam_id, None, None)

    return {
        "is_booked": studio_conflict or remote_conflict
    }