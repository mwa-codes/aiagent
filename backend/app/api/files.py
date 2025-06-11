from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Placeholder: Save file logic
    return {"filename": file.filename}
