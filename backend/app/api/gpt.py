from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/gpt", tags=["gpt"])


class GPTRequest(BaseModel):
    prompt: str


@router.post("/ask")
async def ask_gpt(request: GPTRequest):
    # Placeholder: Integrate with OpenAI or local LLM
    return {"response": f"Echo: {request.prompt}"}
