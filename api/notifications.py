from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.jwt_handler import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    dependencies=[Depends(get_current_user)]  # all routes require a valid token
)

class NotificationCreate(BaseModel):
    title: str
    message: str
    target_type: str  # all, writers, vocalists, specific
    target_user_ids: Optional[List[int]] = None

@router.post("/")
def create_notification(
    data: NotificationCreate,
    user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)

    user = db.get_user_by_id(user_id)
    if not user or user["role"] not in ("admin", "sub-admin"):
        raise HTTPException(status_code=403, detail="Only admins can create notifications")


    if data.target_type not in ("all", "writers", "vocalists", "specific"):
        raise HTTPException(status_code=400, detail="Invalid target_type")
    
    if data.target_type == "specific" and not data.target_user_ids:
        raise HTTPException(status_code=400, detail="target_user_ids required for specific notifications")

    notification = db.create_notification(data.title, data.message, data.target_type, data.target_user_ids)
    return notification

@router.get("/user/")
def get_user_notifications(
    current_user_id: int = Depends(get_current_user)
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    raw_notifications = db.get_user_notifications(current_user_id)

    notifications = []
    for notif in raw_notifications:
        notifications.append({
            "id": notif[0],
            "title": notif[1],
            "message": notif[2],
            "target_type": notif[3],
            "specific_users": notif[4],
            "created_at": notif[5],
            "read": notif[6]
        })

    return {"notifications": notifications}

@router.post("/{notification_id}/read/{user_id}")
def mark_notification_as_read(
    notification_id: int,
    current_user_id: int = Depends(get_current_user)
):
  
    conn = DBConnection.get_connection()
    db = Queries(conn)
    read_entry = db.mark_as_read(notification_id, current_user_id)
    if not read_entry:
        raise HTTPException(status_code=404, detail="Notification already marked as read or not found")
    
    return {"message": "Notification marked as read"}
