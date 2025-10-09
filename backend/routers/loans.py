"""Loan management endpoints for the library system backend."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Book, Loan, Student
from ..schemas import LoanCreate, LoanRead, LoanReturnRequest

# Tehran timezone (UTC+3:30)
TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db)) -> LoanRead:
    """Register a new loan for a student and a book."""
    book = db.get(Book, payload.book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    active_loan_statement = select(Loan).where(
        and_(Loan.book_id == payload.book_id, Loan.returned.is_(False))
    )
    active_loan = db.execute(active_loan_statement).scalar_one_or_none()
    if active_loan is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book already on loan")

    loan = Loan(**payload.model_dump())
    db.add(loan)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loan could not be created") from exc

    db.refresh(loan)
    loan = _load_loan_with_relations(loan.id, db)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Loan refresh failed")
    return LoanRead.model_validate(loan, from_attributes=True)


@router.get("/", response_model=list[LoanRead])
def list_loans(
    returned: bool | None = None,
    student_id: int | None = None,
    book_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[LoanRead]:
    """List loans with optional filters."""
    statement = (
        select(Loan)
        .options(
            selectinload(Loan.book).selectinload(Book.category),
            selectinload(Loan.student),
        )
        .order_by(Loan.loan_date.desc())
    )

    if returned is not None:
        statement = statement.where(Loan.returned.is_(returned))
    if student_id is not None:
        statement = statement.where(Loan.student_id == student_id)
    if book_id is not None:
        statement = statement.where(Loan.book_id == book_id)

    loans = db.execute(statement).scalars().all()
    return [LoanRead.model_validate(loan, from_attributes=True) for loan in loans]


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: Session = Depends(get_db)) -> LoanRead:
    """Retrieve a loan by identifier."""
    loan = _load_loan_with_relations(loan_id, db)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return LoanRead.model_validate(loan, from_attributes=True)


@router.post("/{loan_id}/return", response_model=LoanRead)
def return_book(loan_id: int, payload: LoanReturnRequest, db: Session = Depends(get_db)) -> LoanRead:
    """Mark a loan as returned."""
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    if loan.returned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loan already returned")

    loan.returned = True
    loan.return_date = payload.return_date or datetime.now(TEHRAN_TZ)

    db.add(loan)
    db.commit()
    db.refresh(loan)

    loaded = _load_loan_with_relations(loan_id, db)
    if loaded is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Loan refresh failed")
    return LoanRead.model_validate(loaded, from_attributes=True)


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a loan record."""
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    
    db.delete(loan)
    db.commit()


def _load_loan_with_relations(loan_id: int, db: Session) -> Loan | None:
    """Load a loan with eagerly loaded book and student relationships."""
    statement = (
        select(Loan)
        .options(
            selectinload(Loan.book).selectinload(Book.category),
            selectinload(Loan.student),
        )
        .where(Loan.id == loan_id)
    )
    return db.execute(statement).scalar_one_or_none()
