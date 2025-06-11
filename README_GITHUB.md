# How to Upload This Project to GitHub

## 1. What to Include in Your Repo
- All source code: `backend/app/`, `frontend/`, `dashboards/`
- All config and manifest files: `docker-compose.yml`, `pyproject.toml`, `poetry.lock`, `requirements.txt`, `alembic.ini`, `PROJECT_COMMANDS.md`, `README.md`, `.env.example`
- Alembic migrations (except `__pycache__`): `backend/migrations/` (but not `__pycache__`)
- Dockerfiles: `backend/Dockerfile`, `frontend/Dockerfile`, `dashboards/Dockerfile`
- `.gitignore`

## 2. What to Exclude (already in .gitignore)
- `node_modules/`, `.next/`, `__pycache__/`, `*.pyc`, `.venv/`, `.env`, `.streamlit/`, `.vscode/`, `pgdata/`
- Any local secrets or environment files: `.env` (but you can include `.env.example`)

## 3. Steps to Upload to GitHub

1. **Initialize git (if not already):**
   ```zsh
   git init
   ```
2. **Add all files (except those in .gitignore):**
   ```zsh
   git add .
   ```
3. **Commit:**
   ```zsh
   git commit -m "Initial project commit"
   ```
4. **Create a new repo on GitHub** (via the website).
5. **Add the remote and push:**
   ```zsh
   git remote add origin https://github.com/yourusername/your-repo.git
   git branch -M main
   git push -u origin main
   ```

---

**Tip:**
- Never commit `.env` or secrets. Use `.env.example` for sharing config structure.
- Your `.gitignore` is already set up for best practices.

---

_Last updated: 2025-06-11_
