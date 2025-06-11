# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY app ./app

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
