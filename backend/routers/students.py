"""Student endpoints for the library system backend."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..excel_utils import read_excel_sheets, validate_student_sheet_data
from ..models import Student
from ..schemas import StudentCreate, StudentRead, StudentUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> StudentRead:
    """Create a new student."""
    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student could not be created") from exc
    db.refresh(student)
    return StudentRead.model_validate(student, from_attributes=True)


@router.get("/", response_model=list[StudentRead])
def list_students(
    search: str | None = Query(default=None, description="Optional search term for student name"),
    grade: str | None = Query(default=None, description="Filter by grade"),
    major: str | None = Query(default=None, description="Filter by major"),
    db: Session = Depends(get_db),
) -> list[StudentRead]:
    """Return students optionally filtered by name, grade, or major."""
    statement = select(Student)
    if search:
        normalized = search.strip().lower()
        if normalized:
            statement = statement.where(
                (Student.first_name.ilike(f"%{normalized}%")) |
                (Student.last_name.ilike(f"%{normalized}%"))
            )
    if grade:
        statement = statement.where(Student.grade == grade)
    if major:
        statement = statement.where(Student.major == major)
    statement = statement.order_by(Student.first_name.asc(), Student.last_name.asc())
    students = db.execute(statement).scalars().all()
    return [StudentRead.model_validate(student, from_attributes=True) for student in students]


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)) -> StudentRead:
    """Retrieve a student by identifier."""
    statement = select(Student).where(Student.id == student_id)
    student = db.execute(statement).scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentRead.model_validate(student, from_attributes=True)


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)) -> StudentRead:
    """Update an existing student."""
    statement = select(Student).where(Student.id == student_id)
    student = db.execute(statement).scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student could not be updated") from exc
    db.refresh(student)
    return StudentRead.model_validate(student, from_attributes=True)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a student."""
    statement = select(Student).where(Student.id == student_id)
    student = db.execute(statement).scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    db.delete(student)
    db.commit()


@router.post("/upload-excel", status_code=status.HTTP_201_CREATED)
async def upload_students_excel(
    file: UploadFile = File(..., description="Excel file with students data"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Upload Excel file to bulk import students.
    
    Excel file format:
    - Each sheet name represents a major/field (رشته)
    - Required columns: 'نام', 'نام خانوادگی', 'پایه'
    - Students will be created with the major from the sheet name
    
    Returns:
        Summary of import operation including counts and any errors
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="فایل باید از نوع اکسل (.xlsx یا .xls) باشد"
        )
    
    try:
        content = await file.read()
        sheets_data = read_excel_sheets(content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در خواندن فایل: {str(e)}"
        )
    
    total_created = 0
    total_skipped = 0
    errors = []
    
    for sheet_name, sheet_rows in sheets_data.items():
        if not sheet_rows:
            continue
        
        # Validate and import students
        try:
            validated_students = validate_student_sheet_data(sheet_rows, sheet_name)
        except ValueError as e:
            errors.append(f"شیت '{sheet_name}': {str(e)}")
            continue
        
        for student_data in validated_students:
            # Check if student already exists (by name and grade)
            existing_statement = select(Student).where(
                Student.first_name == student_data["first_name"],
                Student.last_name == student_data["last_name"],
                Student.grade == student_data["grade"],
                Student.major == student_data["major"]
            )
            existing = db.execute(existing_statement).scalar_one_or_none()
            
            if existing:
                total_skipped += 1
                continue
            
            student = Student(**student_data)
            db.add(student)
            total_created += 1
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit students: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در ذخیره‌سازی: {str(e)}"
        )
    
    return {
        "message": "عملیات آپلود با موفقیت انجام شد",
        "total_created": total_created,
        "total_skipped": total_skipped,
        "errors": errors if errors else None,
    }
