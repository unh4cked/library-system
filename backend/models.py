"""SQLAlchemy ORM models for the library system."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import null

from .database import Base

# Pre-defined book categories
DEFAULT_CATEGORIES = [
    {"name": "ادبیات و داستان", "description": "رمان، داستان کوتاه، شعر و ادبیات کلاسیک"},
    {"name": "علمی و فنی", "description": "کتاب‌های علوم پایه، ریاضی، فیزیک، شیمی و مهندسی"},
    {"name": "تاریخ و جغرافیا", "description": "تاریخ ایران و جهان، جغرافیا و مطالعات اجتماعی"},
    {"name": "هنر و موسیقی", "description": "هنرهای تجسمی، موسیقی، سینما و نقاشی"},
    {"name": "علوم انسانی", "description": "روانشناسی، فلسفه، جامعه‌شناسی و علوم اجتماعی"},
]

# Tehran timezone (UTC+3:30)
TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))

class Category(Base):
    """Represents a book category."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    books: Mapped[list[Book]] = relationship(
        "Book",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r})"


class Book(Base):
    """Represents a book stored in the library."""

    __tablename__ = "books"
    __table_args__ = (
        {"comment": "Books available in the library"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)  # Added index for search
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,  # Added index for filtering
    )

    category: Mapped[Category | None] = relationship("Category", back_populates="books")
    loans: Mapped[list[Loan]] = relationship("Loan", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Book(id={self.id!r}, name={self.name!r})"


class Student(Base):
    """Represents a student who can borrow books."""

    __tablename__ = "students"
    __table_args__ = (
        {"comment": "Students who can borrow books from the library"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    grade: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    major: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    national_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    phone_number = Mapped[str | None] = mapped_column(String(15), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(TEHRAN_TZ),
        index=True,
    )

    loans: Mapped[list[Loan]] = relationship("Loan", back_populates="student", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        """Return full name combining first and last name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"Student(id={self.id!r}, name={self.full_name!r})"


class Loan(Base):
    """Represents a loan relationship between a student and a book."""

    __tablename__ = "loans"
    __table_args__ = (
        {"comment": "Loan records tracking book borrowing by students"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Added index for querying loans by book
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # Added index for querying loans by student
    )
    loan_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(TEHRAN_TZ),
        index=True,  # Added index for sorting by date
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # Added index for finding overdue loans
    )
    return_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,  # Added index for filtering active/returned loans
    )

    book: Mapped[Book] = relationship("Book", back_populates="loans")
    student: Mapped[Student] = relationship("Student", back_populates="loans")

    def __repr__(self) -> str:
        return (
            f"Loan(id={self.id!r}, book_id={self.book_id!r}, "
            f"student_id={self.student_id!r}, returned={self.returned!r})"
        )
