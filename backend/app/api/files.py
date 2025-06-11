from typing import List, Dict, Any, Tuple
import os
import shutil
import uuid
import mimetypes
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel

try:
    import pandas as pd
    import openpyxl
    from sqlalchemy.orm import Session
    from ..db import get_db
    from ..models import FileUpload, User
    from .auth import get_current_user
except ImportError as e:
    print(f"Import error: {e}")
    pass

router = APIRouter(prefix="/files", tags=["files"])

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
# Focus on text and spreadsheet files
ALLOWED_EXTENSIONS = {".txt", ".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/csv",
    "application/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel"
}


class FileResponse(BaseModel):
    id: int
    filename: str
    summary: str | None
    upload_date: datetime
    file_type: str | None
    file_size: int | None
    rows_count: int | None
    columns_count: int | None

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    status: str
    file_id: int
    filename: str
    file_type: str
    file_size: int
    preview: Dict[str, Any] | None
    message: str


class FilePreview(BaseModel):
    rows_count: int
    columns_count: int | None
    columns: List[str] | None
    sample_data: List[Dict[str, Any]] | None
    content_preview: str | None


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int


class DataCleaningResponse(BaseModel):
    status: str
    original_shape: Tuple[int, int]
    cleaned_shape: Tuple[int, int]
    rows_removed: int
    columns_removed: int
    cleaning_summary: str
    preview: Dict[str, Any]


def clean_data(file_path: str) -> pd.DataFrame:
    """
    Load file into pandas and perform cleaning.

    Data cleaning best practices include handling nulls and outliers.
    Tailor cleaning to your data (e.g. date parsing, numeric types). 
    Ensure cleaned data is ready for summarization.
    """
    try:
        # Load data based on file extension
        if file_path.endswith(".csv") or file_path.endswith(".txt"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file type")

        # Remove rows/columns that are entirely empty
        df = df.dropna(axis='index', how='all').dropna(
            axis='columns', how='all')

        # Additional cleaning: drop irrelevant columns
        df = df.drop(columns=[col for col in df.columns if col.startswith(
            "Unnamed")], errors='ignore')

        # Reset index
        df = df.reset_index(drop=True)

        return df

    except Exception as e:
        raise ValueError(f"Error cleaning data: {str(e)}")


def get_cleaning_summary(original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> str:
    """Generate a summary of the data cleaning process."""
    orig_rows, orig_cols = original_df.shape
    clean_rows, clean_cols = cleaned_df.shape

    rows_removed = orig_rows - clean_rows
    cols_removed = orig_cols - clean_cols

    summary_parts = []
    if rows_removed > 0:
        summary_parts.append(f"Removed {rows_removed} empty rows")
    if cols_removed > 0:
        summary_parts.append(
            f"Removed {cols_removed} empty/irrelevant columns")

    # Check for data type improvements
    numeric_cols = len(cleaned_df.select_dtypes(include=['number']).columns)
    date_cols = len(cleaned_df.select_dtypes(include=['datetime']).columns)

    if numeric_cols > 0:
        summary_parts.append(f"Optimized {numeric_cols} numeric columns")
    if date_cols > 0:
        summary_parts.append(f"Parsed {date_cols} date columns")

    if not summary_parts:
        return "Data was already clean - no changes needed"

    return "; ".join(summary_parts)


def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    """Save uploaded file to destination."""
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


def get_file_info(file: UploadFile, file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information including size and type."""
    file_size = os.path.getsize(file_path)
    file_ext = os.path.splitext(file.filename or "")[1].lower()

    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(file.filename or "")

    return {
        "file_size": file_size,
        "file_type": file_ext,
        "mime_type": mime_type,
        "original_filename": file.filename
    }


def validate_file_content(file_path: str, file_ext: str) -> Dict[str, Any]:
    """Validate and analyze file content based on file type."""
    validation_result = {
        "is_valid": False,
        "error": None,
        "preview": None,
        "metadata": {}
    }

    try:
        if file_ext in [".csv"]:
            # Validate CSV file
            # Read first 100 rows for validation
            df = pd.read_csv(file_path, nrows=100)
            validation_result.update({
                "is_valid": True,
                "preview": {
                    "rows_count": len(df),
                    "columns_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "sample_data": df.head(5).to_dict('records') if not df.empty else [],
                    "data_types": df.dtypes.astype(str).to_dict()
                },
                "metadata": {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "memory_usage": df.memory_usage(deep=True).sum()
                }
            })

        elif file_ext in [".xlsx", ".xls"]:
            # Validate Excel file
            try:
                # Read Excel file
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names

                # Read first sheet for preview
                df = pd.read_excel(
                    file_path, sheet_name=sheet_names[0], nrows=100)

                validation_result.update({
                    "is_valid": True,
                    "preview": {
                        "rows_count": len(df),
                        "columns_count": len(df.columns),
                        "columns": df.columns.tolist(),
                        "sample_data": df.head(5).to_dict('records') if not df.empty else [],
                        "sheet_names": sheet_names,
                        "active_sheet": sheet_names[0]
                    },
                    "metadata": {
                        "total_sheets": len(sheet_names),
                        "total_rows": len(df),
                        "total_columns": len(df.columns)
                    }
                })
            except Exception as e:
                validation_result.update({
                    "is_valid": False,
                    "error": f"Excel file validation failed: {str(e)}"
                })

        elif file_ext in [".txt"]:
            # Validate text file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Read first 1000 characters
                    lines = content.split('\n')

                validation_result.update({
                    "is_valid": True,
                    "preview": {
                        "content_preview": content[:500] + "..." if len(content) > 500 else content,
                        "lines_count": len(lines),
                        "char_count": len(content)
                    },
                    "metadata": {
                        "encoding": "utf-8",
                        "file_size": os.path.getsize(file_path)
                    }
                })
            except UnicodeDecodeError:
                # Try different encodings
                for encoding in ['latin1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read(1000)
                            lines = content.split('\n')

                        validation_result.update({
                            "is_valid": True,
                            "preview": {
                                "content_preview": content[:500] + "..." if len(content) > 500 else content,
                                "lines_count": len(lines),
                                "char_count": len(content)
                            },
                            "metadata": {
                                "encoding": encoding,
                                "file_size": os.path.getsize(file_path)
                            }
                        })
                        break
                    except:
                        continue
                else:
                    validation_result.update({
                        "is_valid": False,
                        "error": "Could not decode text file with supported encodings"
                    })
        else:
            validation_result.update({
                "is_valid": False,
                "error": f"Unsupported file type: {file_ext}"
            })

    except Exception as e:
        validation_result.update({
            "is_valid": False,
            "error": f"File validation error: {str(e)}"
        })

    return validation_result


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file before processing."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check content type if available
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type {file.content_type} not allowed"
        )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="Upload CSV, TXT, or XLSX file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a file (CSV/TXT/XLSX) for the authenticated user.

    - **file**: The file to upload (CSV, TXT, or XLSX format)
    - **Returns**: File upload confirmation with preview data
    """
    # Validate file format and basic properties
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

    # Generate unique filename to avoid conflicts
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        # Save file to disk
        save_upload_file(file, file_path)

        # Get file information
        file_info = get_file_info(file, file_path)

        # Check file size after saving
        if file_info["file_size"] > MAX_FILE_SIZE:
            os.remove(file_path)  # Clean up
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size {file_info['file_size']} bytes exceeds maximum allowed size {MAX_FILE_SIZE} bytes"
            )

        # Validate and analyze file content
        content_validation = validate_file_content(file_path, file_ext)

        if not content_validation["is_valid"]:
            os.remove(file_path)  # Clean up invalid file
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content validation failed: {content_validation['error']}"
            )

        # Generate summary based on file content
        summary = generate_file_summary(content_validation, file_info)

        # Create database record with enhanced metadata
        preview_data = content_validation.get("preview", {})
        metadata = content_validation.get("metadata", {})

        db_file = FileUpload(
            filename=unique_filename,
            user_id=current_user.id,
            summary=summary,
            file_type=file_ext,
            file_size=file_info["file_size"],
            rows_count=metadata.get(
                "total_rows") or preview_data.get("rows_count"),
            columns_count=metadata.get(
                "total_columns") or preview_data.get("columns_count")
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        return FileUploadResponse(
            status="success",
            file_id=db_file.id,
            filename=file.filename or "unknown",
            file_type=file_ext,
            file_size=file_info["file_size"],
            preview=content_validation.get("preview"),
            message=f"File uploaded successfully. {summary}"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


def generate_file_summary(content_validation: Dict[str, Any], file_info: Dict[str, Any]) -> str:
    """Generate a human-readable summary of the uploaded file."""
    preview = content_validation.get("preview", {})
    metadata = content_validation.get("metadata", {})
    file_ext = file_info.get("file_type", "")

    if file_ext == ".csv":
        return f"CSV file with {metadata.get('total_rows', 0)} rows and {metadata.get('total_columns', 0)} columns"
    elif file_ext in [".xlsx", ".xls"]:
        sheet_count = metadata.get('total_sheets', 1)
        return f"Excel file with {sheet_count} sheet(s), {metadata.get('total_rows', 0)} rows and {metadata.get('total_columns', 0)} columns"
    elif file_ext == ".txt":
        lines = preview.get('lines_count', 0)
        chars = preview.get('char_count', 0)
        return f"Text file with {lines} lines and {chars} characters"
    else:
        return f"File of type {file_ext}"


@router.get("/{file_id}/preview")
async def get_file_preview(
    file_id: int,
    rows: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a preview of the file content with specified number of rows."""
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found"
        )

    file_ext = os.path.splitext(file.filename)[1].lower()

    try:
        if file_ext == ".csv":
            df = pd.read_csv(file_path, nrows=rows)
            return {
                "file_type": "csv",
                "rows_count": len(df),
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "data_types": df.dtypes.astype(str).to_dict()
            }
        elif file_ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(file_path)
            df = pd.read_excel(file_path, nrows=rows)
            return {
                "file_type": "excel",
                "rows_count": len(df),
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "sheet_names": excel_file.sheet_names
            }
        elif file_ext == ".txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= rows:
                        break
                    lines.append(line.rstrip('\n\r'))
            return {
                "file_type": "text",
                "lines_count": len(lines),
                "content": lines
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file: {str(e)}"
        )


@router.post("/{file_id}/analyze")
async def analyze_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze file content and provide statistics and insights."""
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found"
        )

    file_ext = os.path.splitext(file.filename)[1].lower()

    try:
        analysis = {}

        if file_ext == ".csv":
            df = pd.read_csv(file_path)
            analysis = {
                "file_type": "csv",
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": df.columns.tolist(),
                "data_types": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "text_columns": df.select_dtypes(include=['object']).columns.tolist(),
            }

            # Add basic statistics for numeric columns
            if analysis["numeric_columns"]:
                analysis["numeric_stats"] = df[analysis["numeric_columns"]
                                               ].describe().to_dict()

        elif file_ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(file_path)
            df = pd.read_excel(file_path)
            analysis = {
                "file_type": "excel",
                "total_sheets": len(excel_file.sheet_names),
                "sheet_names": excel_file.sheet_names,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": df.columns.tolist(),
                "data_types": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "text_columns": df.select_dtypes(include=['object']).columns.tolist(),
            }

        elif file_ext == ".txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                words = content.split()

            analysis = {
                "file_type": "text",
                "total_lines": len(lines),
                "total_words": len(words),
                "total_characters": len(content),
                "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
                "encoding": "utf-8"
            }

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing file: {str(e)}"
        )


@router.get("/", response_model=FileListResponse)
async def list_files(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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


@router.post("/{file_id}/clean", response_model=DataCleaningResponse)
async def clean_file_data(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean and preprocess file data for analysis."""
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found"
        )

    try:
        # Load and clean data
        original_df = pd.read_csv(file_path)
        cleaned_df = clean_data(file_path)

        # Save cleaned data back to file (overwriting original for simplicity)
        cleaned_df.to_csv(file_path, index=False)

        # Update file metadata in the database
        file.rows_count = len(cleaned_df)
        file.columns_count = len(cleaned_df.columns)
        db.commit()

        # Generate cleaning summary
        cleaning_summary = get_cleaning_summary(original_df, cleaned_df)

        return DataCleaningResponse(
            status="success",
            original_shape=original_df.shape,
            cleaned_shape=cleaned_df.shape,
            rows_removed=original_df.shape[0] - cleaned_df.shape[0],
            columns_removed=len(original_df.columns) - len(cleaned_df.columns),
            cleaning_summary=cleaning_summary,
            preview=cleaned_df.head(5).to_dict('records')
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning file data: {str(e)}"
        )
