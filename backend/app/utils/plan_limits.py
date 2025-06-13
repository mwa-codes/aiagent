"""
Subscription plan limit enforcement utilities.
Provides functions to check and enforce user subscription limits.
"""

from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from ..models import User, Plan, FileUpload, Result


class PlanLimitExceeded(HTTPException):
    """Custom exception for when subscription plan limits are exceeded."""

    def __init__(self, limit_type: str, current_usage: int, limit: int, plan_name: str):
        self.limit_type = limit_type
        self.current_usage = current_usage
        self.limit = limit
        self.plan_name = plan_name

        detail = (
            f"{limit_type} limit exceeded for {plan_name} plan. "
            f"Usage: {current_usage}/{limit}. "
            f"Please upgrade your plan to continue."
        )

        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail
        )


def get_monthly_usage_count(user: User, db: Session, model_class, date_field: str) -> int:
    """
    Get the count of records for a user in the current month.

    Args:
        user: The user to check usage for
        db: Database session
        model_class: The SQLAlchemy model to count (FileUpload, Result, etc.)
        date_field: The name of the date field to filter on

    Returns:
        int: Number of records in the current month
    """
    # Calculate the start of the current month
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    # Query for records in the current month
    date_column = getattr(model_class, date_field)

    if model_class == FileUpload:
        count = db.query(func.count(model_class.id)).filter(
            model_class.user_id == user.id,
            date_column >= start_of_month
        ).scalar()
    elif model_class == Result:
        # For Results, we need to join with FileUpload to get user_id
        count = db.query(func.count(model_class.id)).join(
            FileUpload, model_class.file_id == FileUpload.id
        ).filter(
            FileUpload.user_id == user.id,
            date_column >= start_of_month
        ).scalar()
    else:
        raise ValueError(f"Unsupported model class: {model_class}")

    return count or 0


def get_user_plan_limits(user: User) -> dict:
    """
    Get the plan limits for a user.

    Args:
        user: The user to get limits for

    Returns:
        dict: Dictionary containing plan limits
    """
    if not user.plan:
        # Default limits for users without a plan
        return {
            "max_files": 5,
            "max_uploads_per_month": 10,
            "max_summaries_per_month": 5,
            "max_file_size_mb": 5,
            "plan_name": "Free (No Plan)"
        }

    return {
        "max_files": user.plan.max_files,
        "max_uploads_per_month": user.plan.max_uploads_per_month,
        "max_summaries_per_month": user.plan.max_summaries_per_month,
        "max_file_size_mb": user.plan.max_file_size_mb,
        "plan_name": user.plan.name
    }


def check_upload_limit(user: User, db: Session, file_size_mb: float = 0) -> None:
    """
    Check if user can upload a new file based on their plan limits.

    Args:
        user: The user attempting to upload
        db: Database session
        file_size_mb: Size of the file in MB (optional)

    Raises:
        PlanLimitExceeded: If any limit would be exceeded
    """
    limits = get_user_plan_limits(user)

    # Check total files limit
    total_files = db.query(func.count(FileUpload.id)).filter(
        FileUpload.user_id == user.id
    ).scalar() or 0

    if total_files >= limits["max_files"]:
        raise PlanLimitExceeded(
            "Total files", total_files, limits["max_files"], limits["plan_name"]
        )

    # Check monthly uploads limit
    monthly_uploads = get_monthly_usage_count(
        user, db, FileUpload, "upload_date")

    if monthly_uploads >= limits["max_uploads_per_month"]:
        raise PlanLimitExceeded(
            "Monthly uploads", monthly_uploads, limits["max_uploads_per_month"], limits["plan_name"]
        )

    # Check file size limit
    if file_size_mb > limits["max_file_size_mb"]:
        raise PlanLimitExceeded(
            "File size", int(
                file_size_mb), limits["max_file_size_mb"], limits["plan_name"]
        )


def check_summary_limit(user: User, db: Session) -> None:
    """
    Check if user can create a new summary based on their plan limits.

    Args:
        user: The user attempting to create a summary
        db: Database session

    Raises:
        PlanLimitExceeded: If summary limit would be exceeded
    """
    limits = get_user_plan_limits(user)

    # Check monthly summaries limit
    monthly_summaries = get_monthly_usage_count(user, db, Result, "created_at")

    if monthly_summaries >= limits["max_summaries_per_month"]:
        raise PlanLimitExceeded(
            "Monthly summaries", monthly_summaries, limits["max_summaries_per_month"], limits["plan_name"]
        )


def check_plan_limit(user: User, db: Session, limit_type: str, **kwargs) -> None:
    """
    Universal plan limit checker function.

    Args:
        user: The user to check limits for
        db: Database session
        limit_type: Type of limit to check ("upload", "summary")
        **kwargs: Additional arguments specific to the limit type

    Raises:
        PlanLimitExceeded: If the specified limit would be exceeded
        ValueError: If an unsupported limit_type is provided
    """
    if limit_type == "upload":
        file_size_mb = kwargs.get("file_size_mb", 0)
        check_upload_limit(user, db, file_size_mb)
    elif limit_type == "summary":
        check_summary_limit(user, db)
    else:
        raise ValueError(f"Unsupported limit type: {limit_type}")


def get_usage_summary(user: User, db: Session) -> dict:
    """
    Get a comprehensive usage summary for a user.

    Args:
        user: The user to get usage for
        db: Database session

    Returns:
        dict: Usage summary with current usage and limits
    """
    limits = get_user_plan_limits(user)

    # Get current usage
    total_files = db.query(func.count(FileUpload.id)).filter(
        FileUpload.user_id == user.id
    ).scalar() or 0

    monthly_uploads = get_monthly_usage_count(
        user, db, FileUpload, "upload_date")
    monthly_summaries = get_monthly_usage_count(user, db, Result, "created_at")

    return {
        "plan_name": limits["plan_name"],
        "total_files": {
            "current": total_files,
            "limit": limits["max_files"],
            "percentage": round((total_files / limits["max_files"]) * 100, 1) if limits["max_files"] > 0 else 0
        },
        "monthly_uploads": {
            "current": monthly_uploads,
            "limit": limits["max_uploads_per_month"],
            "percentage": round((monthly_uploads / limits["max_uploads_per_month"]) * 100, 1) if limits["max_uploads_per_month"] > 0 else 0
        },
        "monthly_summaries": {
            "current": monthly_summaries,
            "limit": limits["max_summaries_per_month"],
            "percentage": round((monthly_summaries / limits["max_summaries_per_month"]) * 100, 1) if limits["max_summaries_per_month"] > 0 else 0
        },
        "max_file_size_mb": limits["max_file_size_mb"]
    }
