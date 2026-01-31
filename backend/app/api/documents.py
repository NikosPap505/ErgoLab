from datetime import datetime
from typing import List, Optional
import logging

import boto3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document, DocumentType
from app.services.image_optimizer import optimizer

logger = logging.getLogger(__name__)

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
    elif file_extension in ["jpg", "jpeg", "png", "gif", "webp"]:
        doc_type = DocumentType.IMAGE
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    s3_key = f"projects/{project_id}/documents/{timestamp}_{file.filename}"
    thumbnail_key = None

    try:
        file_content = await file.read()
        original_size = len(file_content)
        
        # Optimize images
        if doc_type == DocumentType.IMAGE and optimizer.is_supported_image(file.content_type or ""):
            logger.info(f"Optimizing image: {file.filename} ({original_size / 1024:.2f} KB)")
            
            # Optimize main image
            optimized_content, metadata = optimizer.optimize_image(file_content)
            file_content = optimized_content
            
            logger.info(
                f"✓ Image optimized: {metadata.get('original_size_kb', 0):.2f}KB → "
                f"{metadata.get('optimized_size_kb', 0):.2f}KB "
                f"({metadata.get('compression_ratio', 0)}% reduction)"
            )
            
            # Create and upload thumbnail
            thumbnail_content = optimizer.create_thumbnail(file_content)
            if thumbnail_content:
                thumbnail_key = f"projects/{project_id}/thumbnails/{timestamp}_{file.filename}"
                s3_client.put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=thumbnail_key,
                    Body=thumbnail_content,
                    ContentType="image/jpeg",
                )
                logger.info(f"✓ Thumbnail uploaded: {thumbnail_key}")
        
        # Upload main file
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
        )
        logger.info(f"✓ Document uploaded: {s3_key}")
        
    except Exception as exc:
        logger.error(f"Upload failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    document = Document(
        project_id=project_id,
        title=title or file.filename,
        description=description,
        file_type=doc_type,
        file_path=s3_key,
        thumbnail_path=thumbnail_key,
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
        "thumbnail_path": thumbnail_key,
        "file_size": len(file_content),
        "original_size": original_size,
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
            "thumbnail_path": doc.thumbnail_path,
            "uploaded_at": doc.uploaded_at,
        }
        for doc in documents
    ]


@router.get("/{document_id}/thumbnail")
def get_document_thumbnail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get presigned URL for document thumbnail"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    thumbnail_path: str | None = document.thumbnail_path  # type: ignore[assignment]
    if not thumbnail_path:
        raise HTTPException(status_code=404, detail="No thumbnail available")
    
    try:
        url = s3_public_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": document.thumbnail_path},
            ExpiresIn=3600,
        )
        return {"thumbnail_url": url}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get thumbnail: {exc}")


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
        "thumbnail_path": document.thumbnail_path,
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

    # Delete main file from S3
    try:
        s3_client.delete_object(
            Bucket=settings.S3_BUCKET,
            Key=document.file_path,
        )
        logger.info(f"✓ Deleted S3 file: {document.file_path}")
    except Exception as exc:
        logger.warning(f"Could not delete S3 file: {exc}")

    # Delete thumbnail from S3 if exists
    doc_thumbnail: str | None = document.thumbnail_path  # type: ignore[assignment]
    if doc_thumbnail:
        try:
            s3_client.delete_object(
                Bucket=settings.S3_BUCKET,
                Key=doc_thumbnail,
            )
            logger.info(f"✓ Deleted thumbnail: {document.thumbnail_path}")
        except Exception as exc:
            logger.warning(f"Could not delete thumbnail: {exc}")

    # Delete related annotations
    from app.models.document import Annotation
    db.query(Annotation).filter(Annotation.document_id == document_id).delete()

    # Delete document record
    db.delete(document)
    db.commit()
    return None
