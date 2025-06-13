"""Database initialization script."""

from .db import sync_engine, SessionLocal
from .models import Base, Plan, User
from .api.auth import get_password_hash


def init_database():
    """Initialize the database with tables and default data."""

    # Create all tables
    Base.metadata.create_all(bind=sync_engine)

    # Create default plans
    db = SessionLocal()
    try:
        # Check if plans exist
        if not db.query(Plan).first():
            # Create default plans
            free_plan = Plan(name="Free", max_files=5)
            premium_plan = Plan(name="Premium", max_files=100)

            db.add(free_plan)
            db.add(premium_plan)
            db.commit()
            print("✅ Created default plans")

        # Create default admin user (optional)
        admin_email = "admin@example.com"
        if not db.query(User).filter(User.email == admin_email).first():
            free_plan = db.query(Plan).filter(Plan.name == "Free").first()
            admin_user = User(
                email=admin_email,
                password_hash=get_password_hash("admin123!"),
                plan_id=free_plan.id if free_plan else None
            )
            db.add(admin_user)
            db.commit()
            print("✅ Created default admin user (admin@example.com / admin123!)")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
