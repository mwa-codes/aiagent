import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def summarize_text(text: str, model: str = "gpt-4.1") -> str:
    """
    Summarize the input text using OpenAI ChatCompletion API.
    Uses a system message to instruct the assistant to summarize the data.
    """
    if not openai.api_key:
        raise RuntimeError("OpenAI API key not configured.")
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that summarizes data."},
                {"role": "user", "content": text}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        raise RuntimeError(f"OpenAI summarization error: {str(e)}")
