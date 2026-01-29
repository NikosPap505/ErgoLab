from datetime import datetime
from typing import List, Optional

import boto3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document, DocumentType

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Internal S3 client for uploads (uses Docker internal network)
s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
)

# Public S3 client for presigned URLs (uses localhost for browser access)
s3_public_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_PUBLIC_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
)


@router.post("/upload/{project_id}", status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.project import Project

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    file_extension = file.filename.split(".")[-1].lower() if file.filename else ""
    if file_extension == "pdf":
        doc_type = DocumentType.PDF
    elif file_extension in ["jpg", "jpeg", "png", "gif"]:
        doc_type = DocumentType.IMAGE
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    s3_key = f"projects/{project_id}/documents/{timestamp}_{file.filename}"

    try:
        file_content = await file.read()
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    document = Document(
        project_id=project_id,
        title=title or file.filename,
        description=description,
        file_type=doc_type,
        file_path=s3_key,
        file_size=len(file_content),
        uploaded_by_id=current_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "document_id": document.id,
        "title": document.title,
        "file_path": s3_key,
        "download_url": f"/api/documents/{document.id}/download",
    }


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Use public client for browser-accessible URLs
        url = s3_public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": document.file_path},
            ExpiresIn=3600,
        )
        return {"url": url, "download_url": url}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Download failed: {exc}")


@router.get("/project/{project_id}", response_model=List[dict])
def get_project_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "file_type": doc.file_type.value,
            "file_size": doc.file_size,
            "uploaded_at": doc.uploaded_at,
        }
        for doc in documents
    ]


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get single document metadata"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": document.id,
        "title": document.title,
        "description": document.description,
        "file_type": document.file_type.value,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "project_id": document.project_id,
        "uploaded_at": document.uploaded_at,
        "uploaded_by_id": document.uploaded_by_id,
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a document and its S3 file"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from S3
    try:
        s3_client.delete_object(
            Bucket=settings.S3_BUCKET,
            Key=document.file_path,
        )
    except Exception as exc:
        # Log but don't fail if S3 delete fails
        print(f"Warning: Could not delete S3 file: {exc}")

    # Delete related annotations
    from app.models.document import Annotation
    db.query(Annotation).filter(Annotation.document_id == document_id).delete()

    # Delete document record
    db.delete(document)
    db.commit()
    return None
