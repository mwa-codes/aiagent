# Full-Stack AI Web App

This project is a full-stack web application with:
- **Frontend**: Next.js (TypeScript)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Dashboards**: Streamlit (optional)
- **Orchestration**: Docker Compose

## Structure
- `frontend/` — Next.js app
- `backend/` — FastAPI app
- `dashboards/` — Streamlit dashboards

## Features
- User authentication
- File upload API
- GPT integration
- PostgreSQL storage
- Optional Streamlit dashboards

## Getting Started
1. Copy `.env.example` to `.env` and fill in secrets.
2. Run `docker-compose up --build` to start all services.
3. Access the frontend at `http://localhost:3000`, backend at `http://localhost:8000`, and dashboards at `http://localhost:8501` (if enabled).

## Development
- Frontend: `cd frontend && npm run dev`
- Backend: `cd backend && uvicorn app.main:app --reload`
- Dashboards: `cd dashboards && streamlit run app.py`

---
See each folder for more details.
