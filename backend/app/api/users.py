from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db import get_db
from ..models import User, Plan, FileUpload
from ..schemas import UserOut, UserProfile, UserUpdate, PasswordChange, EmailUpdate, AccountDeactivation
from .auth import get_current_user, verify_password, get_password_hash, get_user_by_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return current authenticated user's basic data."""
    return current_user


@router.get("/me/profile", response_model=UserProfile)
def get_detailed_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return current user's detailed profile with plan information."""
    # Get user's file count
    files_count = db.query(func.count(FileUpload.id)).filter(
        FileUpload.user_id == current_user.id
    ).scalar()

    # Get plan information
    plan_name = None
    max_files = None
    if current_user.plan:
        plan_name = current_user.plan.name
        max_files = current_user.plan.max_files

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        plan_id=current_user.plan_id,
        plan_name=plan_name,
        max_files=max_files,
        current_files_count=files_count
    )


@router.put("/me", response_model=UserOut)
def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile data."""

    # Track if any changes were made
    changes_made = False

    # Handle email update
    if update_data.email and update_data.email != current_user.email:
        # Check if email is already taken by another user
        existing_user = get_user_by_email(db, update_data.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user"
            )

        current_user.email = update_data.email
        changes_made = True

    # Handle password update
    if update_data.new_password:
        if not update_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to set a new password"
            )

        # Verify current password
        if not verify_password(update_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Update password
        current_user.password_hash = get_password_hash(
            update_data.new_password)
        changes_made = True

    if not changes_made:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid updates provided"
        )

    # Save changes
    db.commit()
    db.refresh(current_user)

    return current_user


@router.put("/me/password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user's password."""

    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Check if new password is different
    if verify_password(password_data.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.put("/me/email")
def change_email(
    email_data: EmailUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user's email address."""

    # Verify password
    if not verify_password(email_data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )

    # Check if email is already taken
    existing_user = get_user_by_email(db, email_data.new_email)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered by another user"
        )

    # Check if new email is different
    if email_data.new_email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New email must be different from current email"
        )

    # Update email
    old_email = current_user.email
    current_user.email = email_data.new_email
    db.commit()

    return {
        "message": "Email updated successfully",
        "old_email": old_email,
        "new_email": email_data.new_email
    }


@router.get("/me/usage")
def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's usage statistics."""

    # Get file count
    files_count = db.query(func.count(FileUpload.id)).filter(
        FileUpload.user_id == current_user.id
    ).scalar()

    # Get plan limits
    max_files = current_user.plan.max_files if current_user.plan else 0

    # Calculate usage percentage
    usage_percentage = (files_count / max_files * 100) if max_files > 0 else 0

    return {
        "current_files": files_count,
        "max_files": max_files,
        "usage_percentage": round(usage_percentage, 2),
        "plan_name": current_user.plan.name if current_user.plan else "No Plan",
        "can_upload": files_count < max_files if max_files > 0 else False
    }


@router.delete("/me/deactivate")
def deactivate_account(
    deactivation_data: AccountDeactivation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account (soft delete - removes all data but keeps user record)."""

    # Verify password
    if not verify_password(deactivation_data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )

    # Delete all user files
    db.query(FileUpload).filter(FileUpload.user_id == current_user.id).delete()

    # Mark user as deactivated (you might want to add a deactivated field to User model)
    # For now, we'll change email to indicate deactivation
    current_user.email = f"deactivated_{current_user.id}@deleted.com"
    current_user.password_hash = "DEACTIVATED"

    db.commit()

    return {
        "message": "Account deactivated successfully",
        "warning": "All user data has been removed"
    }


@router.get("/me/activity")
def get_account_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's recent account activity."""

    # Get recent files
    recent_files = db.query(FileUpload).filter(
        FileUpload.user_id == current_user.id
    ).order_by(FileUpload.upload_date.desc()).limit(5).all()

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "plan": current_user.plan.name if current_user.plan else "No Plan",
        "recent_files": [
            {
                "id": file.id,
                "filename": file.filename,
                "upload_date": file.upload_date,
                "summary": file.summary
            }
            for file in recent_files
        ]
    }
