
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
    users = relationship("User", back_populates="plan")


# --- User Model ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    plan = relationship("Plan", back_populates="users")
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
