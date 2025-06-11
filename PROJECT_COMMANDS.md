# Project Commands & Guide


## Start All Services (Docker Compose)
```
docker compose up -d
```
- Starts backend (FastAPI), frontend (Next.js), dashboards (Streamlit), and PostgreSQL database using existing images (fastest, use this for normal runs).

## Rebuild All Services (if you changed Dockerfile or dependencies)
```
docker compose up -d --build
```
- Use this only after changing Dockerfiles, `package.json`, `requirements.txt`, or `pyproject.toml`.

## Stop All Services
```
docker compose down
```

## View Running Containers
```
docker compose ps
```

## View Logs for All Services
```
docker compose logs -f
```

## Run Alembic Migrations (from backend/)
```
poetry run alembic upgrade head
```

## Start Only the Backend (Dev Mode)
```
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Start Only the Frontend (Dev Mode)
```
cd frontend
npm run dev
```

## Start Only the Dashboards (Dev Mode)
```
cd dashboards
streamlit run app.py
```

## Check Database Connection (psql)
```
psql -h localhost -p 55432 -U postgres -d postgres
```
Password: `postgres`

## Useful Docker Compose Commands
- Restart a service:  
  `docker compose restart backend`
- View logs for a service:  
  `docker compose logs -f backend`

## Environment Setup

### Copy Environment File
```bash
cp .env.example .env
```
Then edit `.env` with your actual values (especially JWT_SECRET_KEY and OPENAI_API_KEY).

### Test Authentication System
```bash
cd backend
python test_auth.py
```

### Initialize Database (if needed)
```bash
cd backend
python -c "from app.init_db import init_database; init_database()"
```

## API Documentation

### Access API Docs
- FastAPI Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

### Authentication Endpoints
- POST `/auth/register` - Register new user
- POST `/auth/login` - Login user
- GET `/auth/me` - Get user profile (requires auth)
- POST `/auth/refresh` - Refresh JWT token
- POST `/auth/logout` - Logout user

### File Upload Endpoints (Requires Authentication)
- POST `/files/upload` - Upload file
- GET `/files/` - List user files
- GET `/files/{file_id}` - Get file details
- DELETE `/files/{file_id}` - Delete file

### GPT Endpoints (Requires Authentication)
- POST `/gpt/ask` - Ask GPT question
- GET `/gpt/results/{file_id}` - Get GPT results for file

### Default Admin User
- Email: admin@example.com
- Password: admin123!

---

**Tip:**
- All services use `.env` or environment variables as configured in `docker-compose.yml`.
- If you change ports, update them in this file and in your configs.

---

_Last updated: 2025-06-11_
