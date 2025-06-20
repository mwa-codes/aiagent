from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# --- Plan Model ---
class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    max_files = Column(Integer, nullable=False, default=10)
    max_uploads_per_month = Column(Integer, nullable=False, default=50)
    max_summaries_per_month = Column(Integer, nullable=False, default=20)
    max_file_size_mb = Column(Integer, nullable=False, default=10)
    users = relationship("User", back_populates="plan")


# --- User Model ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    plan = relationship("Plan", back_populates="users")
    stripe_customer_id = Column(String, unique=True, nullable=True, index=True)
    files = relationship("FileUpload", back_populates="user",
                         cascade="all, delete-orphan")


# --- FileUpload Model ---
class FileUpload(Base):
    __tablename__ = "file_uploads"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    # File extension (.csv, .xlsx, .txt)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)  # File size in bytes
    # Number of rows (for CSV/Excel)
    rows_count = Column(Integer, nullable=True)
    # Number of columns (for CSV/Excel)
    columns_count = Column(Integer, nullable=True)
    user = relationship("User", back_populates="files")
    results = relationship("Result", back_populates="file",
                           cascade="all, delete-orphan")


# --- Result Model ---
class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey(
        "file_uploads.id", ondelete="CASCADE"), nullable=False)
    result_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    file = relationship("FileUpload", back_populates="results")
