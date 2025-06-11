from typing import List
import os
import shutil
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel

try:
    from sqlalchemy.orm import Session
    from ..db import get_db
    from ..models import FileUpload, User
    from .auth import get_current_user
except ImportError:
    pass

router = APIRouter(prefix="/files", tags=["files"])

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".md", ".csv", ".json"}


class FileResponse(BaseModel):
    id: int
    filename: str
    summary: str | None
    upload_date: datetime

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int


def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    """Save uploaded file to destination."""
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check file size (if possible)
    if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size {file_size} exceeds maximum allowed size {MAX_FILE_SIZE}"
            )


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Upload a file for the authenticated user."""
    # Validate file
    validate_file(file)

    # Check user's plan limits
    user_files_count = db.query(FileUpload).filter(
        FileUpload.user_id == current_user.id).count()
    if current_user.plan and user_files_count >= current_user.plan.max_files:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Upload limit reached. Your plan allows {current_user.plan.max_files} files."
        )

    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save file
    save_upload_file(file, file_path)

    # Create database record
    db_file = FileUpload(
        filename=filename,
        user_id=current_user.id,
        summary=None  # Will be generated later
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file


@router.get("/", response_model=FileListResponse)
async def list_files(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """List files for the authenticated user."""
    files = db.query(FileUpload).filter(
        FileUpload.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    total = db.query(FileUpload).filter(
        FileUpload.user_id == current_user.id).count()

    return FileListResponse(files=files, total=total)


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get file details by ID."""
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return file


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Delete a file by ID."""
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Delete physical file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete database record
    db.delete(file)
    db.commit()

    return {"message": "File deleted successfully"}
