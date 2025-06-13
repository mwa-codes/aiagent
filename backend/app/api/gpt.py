
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from .auth import get_current_user
from ..utils.openai_client import summarize_text

router = APIRouter(prefix="/gpt", tags=["gpt"])


def chunk_text(text: str, max_tokens: int = 1500) -> list[str]:
    """
    Split text into chunks of approximately max_tokens (by word count for simplicity).
    Adjust max_tokens as needed for your model/context window.
    """
    words = text.split()
    chunk_size = max_tokens * 0.75  # rough estimate: 1 token ≈ 0.75 words
    chunk_size = int(chunk_size)
    return [
        ' '.join(words[i:i+chunk_size])
        for i in range(0, len(words), chunk_size)
    ]


class SummarizeRequest(BaseModel):
    text: str
    model: Optional[str] = "gpt-4.1"


class SummarizeResponse(BaseModel):
    summary: str


# --- Summarization Endpoint ---

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text_api(
    request: SummarizeRequest,
    current_user=Depends(get_current_user)
):
    """Summarize the given text using OpenAI GPT-4.1 (or specified model)."""
    try:
        text = request.text.strip()
        model = request.model or "gpt-4.1"
        summary = summarize_text(text, model=model)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"OpenAI summarization error: {str(e)}")


try:
    from sqlalchemy.orm import Session
    from ..db import get_db
    from ..models import Result, FileUpload, User
except ImportError:
    pass


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
