from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.document import Annotation, Document
from app.models.user import User

router = APIRouter(prefix="/api/annotations", tags=["Annotations"])


class AnnotationCreate(BaseModel):
    document_id: int
    page_number: Optional[int] = 1
    annotation_type: Optional[str] = "canvas"
    content: Optional[str] = None
    annotation_data: Optional[str] = None  # Legacy support


class AnnotationResponse(BaseModel):
    id: int
    document_id: int
    page_number: int
    annotation_type: Optional[str] = "canvas"
    content: Optional[str] = None
    annotation_data: Optional[str] = None
    created_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)
def create_annotation(
    data: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == data.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    annotation = Annotation(
        document_id=data.document_id,
        page_number=data.page_number or 1,
        annotation_type=data.annotation_type or "canvas",
        content=data.content,
        annotation_data=data.annotation_data,
        created_by_id=current_user.id,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return annotation


@router.get("/document/{document_id}", response_model=List[AnnotationResponse])
def get_document_annotations(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Annotation).filter(Annotation.document_id == document_id).all()


@router.put("/{annotation_id}", response_model=AnnotationResponse)
def update_annotation(
    annotation_id: int,
    annotation_data: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    if annotation.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    annotation.annotation_data = annotation_data
    db.commit()
    db.refresh(annotation)
    return annotation


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    if annotation.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(annotation)
    db.commit()
    return None
