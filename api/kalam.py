from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from psycopg2.extras import RealDictCursor
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.jwt_handler import get_current_user

router = APIRouter(
    prefix="/kalams",
    tags=["Kalams"],
    dependencies=[Depends(get_current_user)]
)

# Pydantic Models
class CreateKalam(BaseModel):
    title: str
    language: str
    theme: str
    kalam_text: str
    description: str
    sufi_influence: str
    musical_preference: str
    writer_comments: Optional[str] = None

class UpdateKalam(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    kalam_text: Optional[str] = None
    description: Optional[str] = None
    sufi_influence: Optional[str] = None
    musical_preference: Optional[str] = None

class AssignVocalist(BaseModel):
    vocalist_id: int

class UpdateYouTubeLink(BaseModel):
    youtube_link: str

class SubmitKalam(BaseModel):
    writer_comments: Optional[str] = None

class UpdateSubmissionStatus(BaseModel):
    new_status: str
    comments: Optional[str] = None

class WriterResponse(BaseModel):
    user_approval_status: str
    writer_comments: Optional[str] = None

class VocalistResponse(BaseModel):
    vocalist_approval_status: str
    vocalist_comments: Optional[str] = None

@router.post("/")
def create_kalam(data: CreateKalam, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "writer":
        raise HTTPException(status_code=403, detail="Only writers can create kalams")

    kalam = db.create_kalam(
        title=data.title,
        language=data.language,
        theme=data.theme,
        kalam_text=data.kalam_text,
        description=data.description,
        sufi_influence=data.sufi_influence,
        musical_preference=data.musical_preference,
        writer_id=user_id
    )
    if not kalam:
        raise HTTPException(status_code=500, detail="Failed to create kalam")

    # Automatically submit the kalam
    submission = db.submit_kalam(kalam["id"], data.writer_comments)
    if not submission:
        raise HTTPException(status_code=500, detail="Failed to submit kalam")

    return {
        "message": "Kalam created and submitted successfully",
        "kalam": kalam,
        "submission": submission
    }

@router.get("/{id}")
def get_kalam(id: int, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    # Fetch the submission for this kalam
    submission = db.get_kalam_submission_by_kalam_id(id)

    return {
        "kalam": kalam,
        "submission": submission
    }

@router.put("/{id}")
def update_kalam(id: int, data: UpdateKalam, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    if user["role"] == "writer" and kalam["writer_id"] != int(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this kalam")

    updated_kalam = db.update_kalam(
        kalam_id=id,
        title=data.title,
        language=data.language,
        theme=data.theme,
        kalam_text=data.kalam_text,
        description=data.description,
        sufi_influence=data.sufi_influence,
        musical_preference=data.musical_preference
    )
    if not updated_kalam:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    return {"message": "Kalam updated successfully", "kalam": updated_kalam}

@router.post("/{id}/assign-vocalist")
def assign_vocalist(id: int, data: AssignVocalist, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign vocalists")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    submission = db.get_kalam_submission_by_kalam_id(id)
    if not submission or submission["status"] != "final_approved":
        raise HTTPException(status_code=400, detail="Kalam must be in final_approved status to assign vocalist")

    vocalist = db.get_vocalist_by_user_id(data.vocalist_id)
    if not vocalist:
        raise HTTPException(status_code=404, detail="Vocalist not found")

    kalam, submission = db.assign_vocalist(id, data.vocalist_id)
    if not kalam or not submission:
        raise HTTPException(status_code=500, detail="Failed to assign vocalist")

    return {
        "message": "Vocalist assigned successfully",
        "kalam": kalam,
        "submission": submission
    }

@router.post("/{id}/post-youtube-link")
def update_youtube_link(id: int, data: UpdateYouTubeLink, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update YouTube links")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    submission = db.get_kalam_submission_by_kalam_id(id)
    if not submission or submission["status"] != "complete_approved":
        raise HTTPException(status_code=400, detail="Kalam must be in complete_approved status to add YouTube link")

    kalam, submission = db.update_youtube_link(id, data.youtube_link)
    if not kalam or not submission:
        raise HTTPException(status_code=500, detail="Failed to update YouTube link")

    return {
        "message": "YouTube link updated successfully",
        "kalam": kalam,
        "submission": submission
    }

@router.get("/{id}/submissions/{sub_id}")
def get_kalam_submission(id: int, sub_id: int, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    submission = db.get_kalam_submission_by_id(sub_id)
    if not submission or submission["kalam_id"] != int(id):
        raise HTTPException(status_code=404, detail="Submission not found")

    return submission

@router.post("/{id}/submissions/{sub_id}/update-status")
def update_submission_status(id: int, sub_id: int, data: UpdateSubmissionStatus, 
                            user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update submission status")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    submission = db.get_kalam_submission_by_id(sub_id)
    if not submission or submission["kalam_id"] != int(id):
        raise HTTPException(status_code=404, detail="Submission not found")

    if data.new_status not in ["admin_approved", "admin_rejected", "changes_requested","final_approved","complete_approved"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    updated_submission = db.update_submission_status(sub_id, data.new_status, data.comments)
    if not updated_submission:
        raise HTTPException(status_code=500, detail="Failed to update submission status")

    return {"message": "Submission status updated successfully", "submission": updated_submission}

@router.post("/{id}/submissions/{sub_id}/writer-response")
def writer_response(id: int, sub_id: int, data: WriterResponse, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "writer":
        raise HTTPException(status_code=403, detail="Only writers can respond to submissions")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    if kalam["writer_id"] != int(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to respond to this submission")

    submission = db.get_kalam_submission_by_id(sub_id)
    if not submission or submission["kalam_id"] != int(id):
        raise HTTPException(status_code=404, detail="Submission not found")

    if data.user_approval_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid user approval status")

    updated_submission = db.writer_response(sub_id, data.user_approval_status, data.writer_comments)
    if not updated_submission:
        raise HTTPException(status_code=500, detail="Failed to process writer response")

    if data.user_approval_status == "approved":
        updated_submission = db.update_submission_status(sub_id, "final_approved", submission["admin_comments"])
        if not updated_submission:
            raise HTTPException(status_code=500, detail="Failed to finalize submission")

    return {"message": "Writer response processed successfully", "submission": updated_submission}

@router.post("/{id}/submissions/{sub_id}/vocalist-response")
def vocalist_response(id: int, sub_id: int, data: VocalistResponse, user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user or user["role"] != "vocalist":
        raise HTTPException(status_code=403, detail="Only vocalists can respond to submissions")

    kalam = db.get_kalam_by_id(id)
    if not kalam:
        raise HTTPException(status_code=404, detail="Kalam not found")

    if kalam["vocalist_id"] != int(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to respond to this submission")

    submission = db.get_kalam_submission_by_id(sub_id)
    if not submission or submission["kalam_id"] != int(id):
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission["status"] != "final_approved":
        raise HTTPException(status_code=400, detail="Submission must be in final_approved status")

    if data.vocalist_approval_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid vocalist approval status")

    kalam, submission = db.vocalist_response(id, data.vocalist_approval_status, data.vocalist_comments)
    if not kalam or not submission:
        raise HTTPException(status_code=500, detail="Failed to process vocalist response")

    return {
        "message": "Vocalist response processed successfully",
        "kalam": kalam,
        "submission": submission
    }
    
    
    
@router.get("/writer/my-kalams")
def get_my_kalams(user_id: int = Depends(get_current_user)):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(user["role"])
    if user["role"] != "writer":
        raise HTTPException(status_code=403, detail="Only writers can view their own kalams")

    kalams = db.get_kalams_by_writer_id(user_id)
    if not kalams:
        return {"message": "No kalams found for this writer", "kalams": []}

    # Fetch submissions for each kalam
    kalam_list = []
    for kalam in kalams:
      
        kalam_list.append({
            "kalam": kalam,
           
        })

    return {
        "message": "Kalams retrieved successfully",
        "kalams": kalam_list
    }
