import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

try:
    import openai
    from sqlalchemy.orm import Session
    from ..db import get_db
    from ..models import Result, FileUpload, User
    from .auth import get_current_user
except ImportError:
    pass

router = APIRouter(prefix="/gpt", tags=["gpt"])

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")


class GPTRequest(BaseModel):
    prompt: str
    file_id: Optional[int] = None


class GPTResponse(BaseModel):
    response: str
    result_id: Optional[int] = None


@router.post("/ask", response_model=GPTResponse)
async def ask_gpt(
    request: GPTRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Ask GPT a question, optionally based on a file."""

    # Check if file_id is provided and belongs to the user
    file_context = ""
    if request.file_id:
        file = db.query(FileUpload).filter(
            FileUpload.id == request.file_id,
            FileUpload.user_id == current_user.id
        ).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        # Add file context (you might want to read the actual file content here)
        file_context = f"Based on the file '{file.filename}': "
        if file.summary:
            file_context += f"File summary: {file.summary}\n"

    try:
        # Prepare the prompt
        full_prompt = file_context + request.prompt

        # Check if OpenAI API key is configured
        if not openai.api_key:
            # Fallback response for development
            response_text = f"GPT Response (Demo Mode): {full_prompt}"
        else:
            # Make OpenAI API call
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes documents and answers questions."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            response_text = response.choices[0].message.content

        # Save the result to database if file_id is provided
        result_id = None
        if request.file_id:
            result = Result(
                file_id=request.file_id,
                result_text=response_text
            )
            db.add(result)
            db.commit()
            db.refresh(result)
            result_id = result.id

        return GPTResponse(response=response_text, result_id=result_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing GPT request: {str(e)}"
        )


@router.get("/results/{file_id}")
async def get_file_results(
    file_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get all GPT results for a specific file."""

    # Verify file belongs to user
    file = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.user_id == current_user.id
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Get all results for the file
    results = db.query(Result).filter(Result.file_id == file_id).all()

    return {
        "file_id": file_id,
        "filename": file.filename,
        "results": [
            {
                "id": result.id,
                "result_text": result.result_text,
                "created_at": result.created_at
            }
            for result in results
        ]
    }
