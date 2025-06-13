from ..utils.data_cleaning import clean_uploaded_file
from .auth import get_current_user
from ..models import FileUpload, User
from ..db import get_db
from sqlalchemy.orm import Session
import openpyxl
import pandas as pd
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from io import BytesIO
from datetime import datetime
import mimetypes
import uuid
import shutil
import os
from typing import List, Dict, Any, Tuple
from ..models import FileUpload, User, Result
from ..utils.openai_client import summarize_text
# Summarize a file's data and save the summary
from fastapi import Body

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
    "application/octet-stream",  # Sometimes CSV files are detected as this
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel"
}


@router.post("/summarize/{file_id}")
async def summarize_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Summarize the cleaned data of a file for the current user using OpenAI.
    """
    # Retrieve the file for the user
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")

    # Clean and load the data
    cleaned_df, _ = clean_uploaded_file(file_path)
    # Use only the first 20 rows for summarization to avoid token limits
    preview_df = cleaned_df.head(20)
    # Convert to CSV string for prompt
    data_str = preview_df.to_csv(index=False)
    prompt = f"Summarize this dataset:\n{data_str}"

    # Call OpenAI to summarize
    try:
        summary = summarize_text(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    # Save summary to the database (Result table)
    result = Result(file_id=file.id, result_text=summary)
    db.add(result)
    db.commit()
    db.refresh(result)

    # Optionally, update the file's summary field
    file.summary = summary
    db.commit()

    return {"file_id": file.id, "summary": summary}
ALLOWED_EXTENSIONS = {".txt", ".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/csv",
    "application/csv",
    "application/octet-stream",  # Sometimes CSV files are detected as this
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


class FileHistoryItem(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    file_type: str | None
    file_size: int | None
    has_summary: bool

    class Config:
        from_attributes = True


class FileHistoryResponse(BaseModel):
    files: List[FileHistoryItem]
    total: int


class FileSummaryResult(BaseModel):
    id: int
    result_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class FileResultsResponse(BaseModel):
    file_id: int
    filename: str
    upload_date: datetime
    file_type: str | None
    file_size: int | None
    rows_count: int | None
    columns_count: int | None
    summaries: List[FileSummaryResult]

    class Config:
        from_attributes = True


def clean_data(file_path: str) -> pd.DataFrame:
    """
    Comprehensive data parsing and cleaning function for uploaded files.

    Performs the following cleaning steps:
    1. Load file into pandas DataFrame
    2. Drop empty rows and columns
    3. Standardize column headers
    4. Convert data types appropriately
    5. Remove duplicates
    6. Handle missing values

    Args:
        file_path (str): Path to the uploaded file

    Returns:
        pd.DataFrame: Cleaned DataFrame ready for analysis and summarization

    Raises:
        ValueError: If file type is unsupported or cleaning fails
    """
    try:
        # Step 1: Load data based on file extension
        file_ext = file_path.lower()
        if file_ext.endswith((".csv", ".txt")):
            # Try different encodings for robust CSV/TXT loading
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                raise ValueError(
                    "Could not decode file with supported encodings")

        elif file_ext.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Store original shape for reporting
        original_shape = df.shape

        # Step 2: Drop entirely empty rows and columns
        df = df.dropna(axis='index', how='all')  # Remove empty rows
        df = df.dropna(axis='columns', how='all')  # Remove empty columns

        # Step 3: Clean and standardize column headers
        # Remove unnamed columns (often from Excel files)
        df = df.drop(columns=[col for col in df.columns if str(
            col).startswith("Unnamed")], errors='ignore')

        # Standardize column names
        if not df.empty:
            # Clean column names: strip whitespace, replace spaces with underscores, lowercase
            df.columns = [
                str(col).strip()
                .replace(' ', '_')
                .replace('-', '_')
                .replace('.', '_')
                .lower()
                .replace('__', '_')  # Replace double underscores
                for col in df.columns
            ]

            # Remove special characters from column names
            import re
            df.columns = [re.sub(r'[^\w_]', '', col) for col in df.columns]

            # Ensure column names are not empty
            df.columns = [
                col if col else f'column_{i}' for i, col in enumerate(df.columns)]

        # Step 4: Convert data types appropriately
        if not df.empty:
            for column in df.columns:
                # Skip if column is already properly typed
                if df[column].dtype in ['int64', 'float64', 'bool']:
                    continue

                # Try to convert to numeric (integers or floats)
                numeric_converted = pd.to_numeric(df[column], errors='coerce')
                if not numeric_converted.isna().all():
                    # If more than 50% of values are numeric, convert the column
                    if (numeric_converted.notna().sum() / len(df)) > 0.5:
                        df[column] = numeric_converted
                        continue

                # Try to convert to datetime
                if df[column].dtype == 'object':
                    try:
                        # Sample a few values to check if they might be dates
                        sample_values = df[column].dropna().head(10)
                        if len(sample_values) > 0:
                            # Try to parse dates with multiple formats
                            date_formats = ['%Y-%m-%d', '%m/%d/%Y',
                                            '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                            for date_format in date_formats:
                                try:
                                    pd.to_datetime(
                                        sample_values.iloc[0], format=date_format)
                                    df[column] = pd.to_datetime(
                                        df[column], format=date_format, errors='coerce')
                                    break
                                except:
                                    continue
                            else:
                                # Try general datetime parsing
                                datetime_converted = pd.to_datetime(
                                    df[column], errors='coerce')
                                if (datetime_converted.notna().sum() / len(df)) > 0.5:
                                    df[column] = datetime_converted
                    except:
                        pass  # Keep as object type if datetime conversion fails

        # Step 5: Remove duplicate rows
        if not df.empty:
            initial_rows = len(df)
            df = df.drop_duplicates()
            df = df.reset_index(drop=True)
            duplicates_removed = initial_rows - len(df)
        else:
            duplicates_removed = 0

        # Step 6: Handle missing values intelligently
        if not df.empty:
            for column in df.columns:
                if df[column].dtype in ['int64', 'float64']:
                    # For numeric columns, fill missing values with median
                    if df[column].isna().any():
                        median_value = df[column].median()
                        if pd.notna(median_value):
                            df[column] = df[column].fillna(median_value)
                elif df[column].dtype == 'object':
                    # For text columns, fill with 'Unknown' or most frequent value
                    if df[column].isna().any():
                        mode_value = df[column].mode()
                        if len(mode_value) > 0:
                            df[column] = df[column].fillna(mode_value.iloc[0])
                        else:
                            df[column] = df[column].fillna('Unknown')

        # Final cleanup: Reset index
        df = df.reset_index(drop=True)

        # Log cleaning summary
        final_shape = df.shape
        print(f"Data cleaning completed: {original_shape} -> {final_shape}")
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate rows")

        return df

    except Exception as e:
        raise ValueError(f"Error cleaning data: {str(e)}")


def get_cleaning_summary(original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> str:
    """
    Generate a comprehensive summary of the data cleaning process.

    Args:
        original_df (pd.DataFrame): Original DataFrame before cleaning
        cleaned_df (pd.DataFrame): DataFrame after cleaning

    Returns:
        str: Human-readable summary of cleaning operations performed
    """
    orig_rows, orig_cols = original_df.shape
    clean_rows, clean_cols = cleaned_df.shape

    rows_removed = orig_rows - clean_rows
    cols_removed = orig_cols - clean_cols

    summary_parts = []

    # Report structural changes
    if rows_removed > 0:
        summary_parts.append(f"Removed {rows_removed} empty/duplicate rows")
    if cols_removed > 0:
        summary_parts.append(
            f"Removed {cols_removed} empty/irrelevant columns")

    # Report data type improvements
    if not cleaned_df.empty:
        numeric_cols = len(cleaned_df.select_dtypes(
            include=['int64', 'float64']).columns)
        datetime_cols = len(cleaned_df.select_dtypes(
            include=['datetime64']).columns)
        text_cols = len(cleaned_df.select_dtypes(include=['object']).columns)

        type_summary = []
        if numeric_cols > 0:
            type_summary.append(f"{numeric_cols} numeric")
        if datetime_cols > 0:
            type_summary.append(f"{datetime_cols} datetime")
        if text_cols > 0:
            type_summary.append(f"{text_cols} text")

        if type_summary:
            summary_parts.append(
                f"Optimized data types: {', '.join(type_summary)} columns")

    # Report missing value handling
    if not cleaned_df.empty:
        missing_values = cleaned_df.isnull().sum().sum()
        if missing_values == 0:
            summary_parts.append("Handled all missing values")
        elif missing_values < original_df.isnull().sum().sum():
            summary_parts.append(f"Reduced missing values to {missing_values}")

    # Report column name standardization
    if not original_df.empty and not cleaned_df.empty:
        original_cols_with_spaces = sum(
            1 for col in original_df.columns if ' ' in str(col))
        if original_cols_with_spaces > 0:
            summary_parts.append("Standardized column names")

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


# --- History Endpoints ---
@router.get("/history/files", response_model=FileHistoryResponse)
async def get_user_file_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all files uploaded by the current user with basic metadata.
    """
    files = db.query(FileUpload).filter(
        FileUpload.user_id == current_user.id
    ).order_by(FileUpload.upload_date.desc()).all()

    file_items = []
    for file in files:
        file_items.append(FileHistoryItem(
            id=file.id,
            filename=file.filename,
            upload_date=file.upload_date,
            file_type=file.file_type,
            file_size=file.file_size,
            has_summary=file.summary is not None
        ))

    return FileHistoryResponse(
        files=file_items,
        total=len(file_items)
    )


@router.get("/history/results/{file_id}", response_model=FileResultsResponse)
async def get_file_results_history(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all summaries and results for a specific file owned by the current user.
    """
    # Verify file ownership and existence
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(
            status_code=404,
            detail="File not found or you don't have permission to access it"
        )

    # Get all results/summaries for this file
    results = db.query(Result).filter(
        Result.file_id == file_id
    ).order_by(Result.created_at.desc()).all()

    summary_results = []
    for result in results:
        summary_results.append(FileSummaryResult(
            id=result.id,
            result_text=result.result_text,
            created_at=result.created_at
        ))

    return FileResultsResponse(
        file_id=file.id,
        filename=file.filename,
        upload_date=file.upload_date,
        file_type=file.file_type,
        file_size=file.file_size,
        rows_count=file.rows_count,
        columns_count=file.columns_count,
        summaries=summary_results
    )


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


@router.post("/{file_id}/advanced-clean")
async def advanced_clean_file_data(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform advanced data cleaning using the comprehensive DataCleaner utility.

    This endpoint provides more sophisticated cleaning than the basic clean endpoint,
    including:
    - Intelligent data type conversion
    - Advanced missing value handling
    - Column name standardization
    - Duplicate removal
    - Comprehensive reporting
    """
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
        # Use the advanced data cleaning utility
        cleaned_df, cleaning_stats = clean_uploaded_file(file_path)

        if not cleaning_stats.get('success', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Advanced cleaning failed: {cleaning_stats.get('error', 'Unknown error')}"
            )

        # Save cleaned data back to file
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == ".csv":
            cleaned_df.to_csv(file_path, index=False)
        elif file_ext in [".xlsx", ".xls"]:
            cleaned_df.to_excel(file_path, index=False)
        else:
            # For TXT files, save as CSV
            csv_path = file_path.replace(file_ext, ".csv")
            cleaned_df.to_csv(csv_path, index=False)
            # Update filename in database to reflect format change
            file.filename = file.filename.replace(file_ext, ".csv")

        # Update file metadata in the database
        file.rows_count = cleaned_df.shape[0]
        file.columns_count = cleaned_df.shape[1]
        file.file_type = ".csv" if file_ext == ".txt" else file_ext
        db.commit()

        # Prepare response
        response_data = {
            "status": "success",
            "file_id": file_id,
            "cleaning_summary": cleaning_stats,
            "preview": cleaned_df.head(10).to_dict('records') if not cleaned_df.empty else [],
            "message": cleaning_stats.get('message', 'Advanced data cleaning completed successfully')
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during advanced cleaning: {str(e)}"
        )


@router.get("/{file_id}/data-quality")
async def get_data_quality_report(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive data quality report for the uploaded file.

    This endpoint analyzes the file and provides detailed insights about:
    - Data types and distribution
    - Missing values patterns
    - Potential data quality issues
    - Cleaning recommendations
    """
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
        # Load the file and analyze data quality
        file_ext = file_path.lower()
        df = None

        # Load file based on extension
        if file_ext.endswith((".csv", ".txt")):
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
        elif file_ext.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)

        if df is None:
            raise ValueError("Could not load file")

        # Generate comprehensive data quality report
        quality_report = {
            "file_info": {
                "filename": file.filename,
                "file_type": file.file_type,
                "file_size_mb": file.file_size / 1024 / 1024 if file.file_size else 0,
                "shape": df.shape
            },
            "data_overview": {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'missing_values': df.isnull().sum().to_dict(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            },
            "quality_issues": [],
            "recommendations": []
        }

        # Analyze data quality issues
        if df.empty:
            quality_report["quality_issues"].append("Dataset is empty")
            quality_report["recommendations"].append("Upload a file with data")
        else:
            # Check for missing values
            missing_values = df.isnull().sum()
            high_missing_cols = missing_values[missing_values > len(
                df) * 0.5].index.tolist()
            if high_missing_cols:
                quality_report["quality_issues"].append(
                    f"High missing values in columns: {high_missing_cols}")
                quality_report["recommendations"].append(
                    "Consider removing or imputing high-missing columns")

            # Check for duplicate rows
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                quality_report["quality_issues"].append(
                    f"Found {duplicates} duplicate rows")
                quality_report["recommendations"].append(
                    "Remove duplicate rows for better analysis")

            # Check for unnamed columns
            unnamed_cols = [col for col in df.columns if str(
                col).startswith("Unnamed")]
            if unnamed_cols:
                quality_report["quality_issues"].append(
                    f"Found {len(unnamed_cols)} unnamed columns")
                quality_report["recommendations"].append(
                    "Remove or rename unnamed columns")

            # Check for inconsistent data types
            object_cols = df.select_dtypes(include=['object']).columns
            for col in object_cols:
                # Check if column might be numeric
                numeric_convertible = pd.to_numeric(
                    df[col], errors='coerce').notna().sum()
                if numeric_convertible > len(df) * 0.5:
                    quality_report["quality_issues"].append(
                        f"Column '{col}' appears numeric but stored as text")
                    quality_report["recommendations"].append(
                        f"Convert column '{col}' to numeric type")

            # Check for empty rows/columns
            empty_rows = df.isnull().all(axis=1).sum()
            empty_cols = df.isnull().all(axis=0).sum()
            if empty_rows > 0:
                quality_report["quality_issues"].append(
                    f"Found {empty_rows} completely empty rows")
                quality_report["recommendations"].append("Remove empty rows")
            if empty_cols > 0:
                quality_report["quality_issues"].append(
                    f"Found {empty_cols} completely empty columns")
                quality_report["recommendations"].append(
                    "Remove empty columns")

        # Add cleaning readiness score
        total_issues = len(quality_report["quality_issues"])
        if total_issues == 0:
            quality_report["readiness_score"] = 100
            quality_report["readiness_level"] = "Excellent"
        elif total_issues <= 2:
            quality_report["readiness_score"] = 80
            quality_report["readiness_level"] = "Good"
        elif total_issues <= 4:
            quality_report["readiness_score"] = 60
            quality_report["readiness_level"] = "Fair"
        else:
            quality_report["readiness_score"] = 40
            quality_report["readiness_level"] = "Needs Improvement"

        return quality_report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating data quality report: {str(e)}"
        )
