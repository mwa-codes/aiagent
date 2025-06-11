#!/bin/bash
# filepath: /Users/MWA/Desktop/aiagent/backend/startup.sh

echo "🚀 Starting FastAPI backend..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h db -p 5432 -U postgres; do
    echo "Database is unavailable - sleeping"
    sleep 1
done
echo "✅ Database is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Initialize database with default data
echo "🗃️ Initializing database..."
python -c "from app.init_db import init_database; init_database()"

# Start the application
echo "🎯 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
