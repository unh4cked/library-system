"""Pydantic schemas for request/response validation in the library system."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc


# ========================= Category Schemas =========================


class CategoryBase(BaseModel):
    """Base schema for category with shared fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str | None = Field(None, max_length=255, description="Category description")


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category. All fields are optional."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)


class CategoryRead(CategoryBase):
    """Schema for reading a category from the database."""

    id: int
    model_config = ConfigDict(from_attributes=True)


# ========================= Book Schemas =========================


class BookBase(BaseModel):
    """Base schema for book with shared fields."""

    name: str = Field(..., min_length=1, max_length=150, description="Book title")
    category_id: int | None = Field(None, description="Optional category ID")


class BookCreate(BookBase):
    """Schema for creating a new book."""

    pass


class BookUpdate(BaseModel):
    """Schema for updating an existing book. All fields are optional."""

    name: str | None = Field(None, min_length=1, max_length=150)
    category_id: int | None = None


class BookRead(BookBase):
    """Schema for reading a book from the database."""

    id: int
    category: CategoryRead | None = None
    model_config = ConfigDict(from_attributes=True)


# ========================= Student Schemas =========================


class StudentBase(BaseModel):
    """Base schema for student with shared fields."""

    first_name: str = Field(..., min_length=1, max_length=60, description="First name")
    last_name: str = Field(..., min_length=1, max_length=60, description="Last name")
    grade: str | None = Field(None, max_length=30, description="Student grade level")
    major: str | None = Field(None, max_length=60, description="Student major/field")
    national_id: str | None = Field(None, max_length=20, description="National ID or identifier (optional)")
    phone_number: str | None = Field(None, max_length=15, description="Contact phone number (optional)")
    
class StudentCreate(StudentBase):
    """Schema for creating a new student."""

    pass


class StudentUpdate(BaseModel):
    """Schema for updating an existing student. All fields are optional."""

    first_name: str | None = Field(None, min_length=1, max_length=60)
    last_name: str | None = Field(None, min_length=1, max_length=60)
    grade: str | None = Field(None, max_length=30)
    major: str | None = Field(None, max_length=60)
    national_id: str | None = Field(None, max_length=20)
    phone_number: str | None = Field(None, max_length=15)
    

class StudentRead(BaseModel):
    """Schema for reading a student from the database."""

    id: int
    first_name: str
    last_name: str
    full_name: str
    grade: str | None
    major: str | None
    national_id: str | None
    phone_number: str | None
    registered_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ========================= Loan Schemas =========================


class LoanBase(BaseModel):
    """Base schema for loan with shared fields."""

    book_id: int = Field(..., description="ID of the book being loaned")
    student_id: int = Field(..., description="ID of the student borrowing the book")
    due_date: datetime | None = Field(None, description="Due date for returning the book")


class LoanCreate(LoanBase):
    """Schema for creating a new loan."""

    pass


class LoanReturnRequest(BaseModel):
    """Schema for marking a loan as returned."""

    return_date: datetime | None = Field(None, description="Date when book was returned")


class LoanRead(BaseModel):
    """Schema for reading a loan from the database with relationships."""

    id: int
    book_id: int
    student_id: int
    loan_date: datetime
    due_date: datetime | None
    return_date: datetime | None
    returned: bool
    book: BookRead | None = None
    student: StudentRead | None = None
    model_config = ConfigDict(from_attributes=True)
