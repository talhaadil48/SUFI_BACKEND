from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from db.connection import DBConnection
from datetime import datetime
from sql.combinedQueries import Queries

router = APIRouter(prefix="/public", tags=["Public"])

class PartnershipProposalCreate(BaseModel):
    full_name: str
    email: str
    organization_name: str
    role_title: str
    organization_type: Optional[str]
    partnership_type: Optional[str]
    website: Optional[str]
    proposal_text: str
    proposed_timeline: Optional[str]
    resources: Optional[str]
    goals: Optional[str]
    sacred_alignment: Optional[bool] = True

class PartnershipProposalResponse(BaseModel):
    id: int
    full_name: str
    email: str
    organization_name: str
    role_title: str
    organization_type: Optional[str]
    partnership_type: Optional[str]
    website: Optional[str]
    proposal_text: str
    proposed_timeline: Optional[str]
    resources: Optional[str]
    goals: Optional[str]
    sacred_alignment: bool
    created_at: str

@router.post("/", response_model=PartnershipProposalResponse)
def create_partnership_proposal(
    data: PartnershipProposalCreate,
    
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
   
    query = """
    INSERT INTO partnership_proposals (
        full_name, email, organization_name, role_title, organization_type,
        partnership_type, website, proposal_text, proposed_timeline,
        resources, goals, sacred_alignment
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING *
    """
    with conn.cursor() as cur:
        cur.execute(query, (
            data.full_name,
            data.email,
            data.organization_name,
            data.role_title,
            data.organization_type,
            data.partnership_type,
            data.website,
            data.proposal_text,
            data.proposed_timeline,
            data.resources,
            data.goals,
            data.sacred_alignment
        ))
        proposal = cur.fetchone()
        conn.commit()

    return PartnershipProposalResponse(
        id=proposal[0],
        full_name=proposal[1],
        email=proposal[2],
        organization_name=proposal[3],
        role_title=proposal[4],
        organization_type=proposal[5],
        partnership_type=proposal[6],
        website=proposal[7],
        proposal_text=proposal[8],
        proposed_timeline=proposal[9],
        resources=proposal[10],
        goals=proposal[11],
        sacred_alignment=proposal[12],
        created_at=str(proposal[13])
    )





@router.get("/postedkalams", response_model=List[dict])
def get_posted_kalams(
    skip: int = Query(0, ge=0),  # how many to skip
    limit: int = Query(4, ge=1),  # how many to fetch
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
   
    return db.fetch_posted_kalams(skip, limit)




@router.get("/vocalists", response_model=List[dict])
def get_vocalists(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    return db.fetch_vocalists(skip, limit)





@router.get("/posts", response_model=List[dict])
def get_guest_posts_paginated(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    
    try:
        return db.fetch_paginated_guest_posts(skip, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))







@router.get("/writers", response_model=List[dict])
def get_writers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
):
    conn = DBConnection.get_connection()
    db = Queries(conn)
    return db.fetch_writers(skip, limit)





@router.get("/special-recognitions/all", response_model=List[dict])
def get_all_special_recognitions():
    conn = DBConnection.get_connection()
    db = Queries(conn)
    
    try:
        return db.fetch_all_special_recognitions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))