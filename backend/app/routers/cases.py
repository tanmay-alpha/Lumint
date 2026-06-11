from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.models import Case
from app.schemas.cases import CaseCreate, CaseUpdate, CaseResponse
from ai.client import ask_groq

router = APIRouter(prefix="/api/cases", tags=["cases"], dependencies=[Depends(get_current_user)])

@router.post("", response_model=CaseResponse)
def create_case(body: CaseCreate, db: Session = Depends(get_db)):
    db_case = Case(
        title=body.title,
        description=body.description,
        status=body.status,
        severity=body.severity,
        assigned_analyst=body.assigned_analyst,
        saved_evidence=[],
        analyst_notes=""
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("", response_model=List[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    return db.query(Case).all()

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return db_case

@router.put("/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, body: CaseUpdate, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found.")
    
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_case, key, value)
        
    db.commit()
    db.refresh(db_case)
    return db_case

@router.post("/{case_id}/evidence", response_model=CaseResponse)
def add_evidence(case_id: int, evidence_item: dict, db: Session = Depends(get_db)):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found.")
    
    current_evidence = list(db_case.saved_evidence or [])
    current_evidence.append(evidence_item)
    db_case.saved_evidence = current_evidence
    
    db.commit()
    db.refresh(db_case)
    return db_case

@router.post("/{case_id}/ai-brief", response_model=CaseResponse)
async def generate_case_ai_brief(case_id: int, db: Session = Depends(get_db)):
    """
    Synthesize all attached threat indicators, logs, and analyst notes into an AI executive investigation brief.
    """
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found.")
        
    system_prompt = """
    You are Lumint's Lead Principal Security Investigator.
    Generate a concise executive summary brief for a corporate security team.
    Highlight:
    1. Incident Summary & Severity Assessment.
    2. Modus Operandi & Entities involved.
    3. Actionable remediation steps (mitigation plan).
    Format your response in neat, professional Markdown.
    Respond with a JSON object containing a single key "brief".
    """
    
    user_prompt = f"""
    Case Title: {db_case.title}
    Description: {db_case.description}
    Severity: {db_case.severity}
    Status: {db_case.status}
    Analyst Notes: {db_case.analyst_notes}
    Evidence: {db_case.saved_evidence}
    """
    
    response = await ask_groq(system=system_prompt, user=user_prompt, json_mode=True)
    brief = response.get("brief", "Error synthesizing intelligence briefing via Groq. Please check API credentials.")
    
    db_case.ai_summary_brief = brief
    db.commit()
    db.refresh(db_case)
    return db_case
