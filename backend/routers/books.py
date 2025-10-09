"""Book and category endpoints for the library system backend."""
from __future__ import annotations

import logging
from typing import Any, Iterable

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .. import cache
from ..database import get_db
from ..excel_utils import read_excel_sheets, validate_book_sheet_data
from ..models import Book, Category
from ..schemas import BookCreate, BookRead, BookUpdate, CategoryCreate, CategoryRead, CategoryUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


def _serialize_books(books: Iterable[Book]) -> list[dict[str, object]]:
    """Convert SQLAlchemy book instances to serializable dicts."""
    return [BookRead.model_validate(book, from_attributes=True).model_dump() for book in books]


@router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: Session = Depends(get_db)) -> BookRead:
    """Create a new book entry."""
    book = Book(**payload.model_dump())
    db.add(book)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create book due to integrity error: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book could not be created")
    db.refresh(book)
    cache.invalidate_book_search_cache()
    return BookRead.model_validate(book, from_attributes=True)


@router.get("/", response_model=list[BookRead])
def list_books(
    search: str | None = Query(default=None, description="Optional search term for book name"),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    """Return books optionally filtered by name with Redis cache support."""
    if search:
        normalized = search.strip().lower()
        if normalized:
            cache_key = cache.build_book_search_key(normalized)
            cached = cache.get_cached_value(cache_key)
            if cached is not None:
                return [BookRead.model_validate(item) for item in cached]

            statement = (
                select(Book)
                .options(selectinload(Book.category))
                .where(Book.name.ilike(f"%{normalized}%"))
                .order_by(Book.name.asc())
            )
            books = db.execute(statement).scalars().all()
            serialized = _serialize_books(books)
            cache.set_cached_value(cache_key, serialized)
            return [BookRead.model_validate(item) for item in serialized]

    statement = select(Book).options(selectinload(Book.category)).order_by(Book.name.asc())
    books = db.execute(statement).scalars().all()
    return [BookRead.model_validate(book, from_attributes=True) for book in books]


# Category endpoints (must be before /{book_id} to avoid path conflicts)
@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryRead:
    """Create a new category."""
    category = Category(**payload.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create category due to integrity error: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name must be unique")
    db.refresh(category)
    return CategoryRead.model_validate(category, from_attributes=True)


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    """Return all categories."""
    statement = select(Category).order_by(Category.name.asc())
    categories = db.execute(statement).scalars().all()
    return [CategoryRead.model_validate(category, from_attributes=True) for category in categories]


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)) -> CategoryRead:
    """Update an existing category."""
    statement = select(Category).where(Category.id == category_id)
    category = db.execute(statement).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update category due to integrity error: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name must be unique")
    db.refresh(category)
    return CategoryRead.model_validate(category, from_attributes=True)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a category and detach related books."""
    statement = select(Category).where(Category.id == category_id)
    category = db.execute(statement).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    db.delete(category)
    db.commit()


# Book endpoints with path parameters
@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> BookRead:
    """Retrieve a book by its identifier."""
    statement = (
        select(Book)
        .options(selectinload(Book.category))
        .where(Book.id == book_id)
    )
    book = db.execute(statement).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookRead.model_validate(book, from_attributes=True)


@router.patch("/{book_id}", response_model=BookRead)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)) -> BookRead:
    """Update an existing book entry."""
    statement = select(Book).where(Book.id == book_id)
    book = db.execute(statement).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(book, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update book due to integrity error: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book could not be updated")
    db.refresh(book)
    cache.invalidate_book_search_cache()
    return BookRead.model_validate(book, from_attributes=True)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a book by its identifier."""
    statement = select(Book).where(Book.id == book_id)
    book = db.execute(statement).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    db.delete(book)
    db.commit()
    cache.invalidate_book_search_cache()


@router.post("/upload-excel", status_code=status.HTTP_201_CREATED)
async def upload_books_excel(
    file: UploadFile = File(..., description="Excel file with books data"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Upload Excel file to bulk import books.
    
    Excel file format:
    - Each sheet name represents a category (دسته‌بندی)
    - Required column: 'نام کتاب' or 'نام' or 'عنوان'
    - Books will be created with the category matching the sheet name
    
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
    categories_created = []
    
    # Get or create categories based on sheet names
    category_map: dict[str, int] = {}
    
    for sheet_name, sheet_rows in sheets_data.items():
        if not sheet_rows:
            continue
        
        # Find or create category
        statement = select(Category).where(Category.name == sheet_name)
        category = db.execute(statement).scalar_one_or_none()
        
        if category is None:
            category = Category(name=sheet_name, description=f"دسته‌بندی {sheet_name}")
            db.add(category)
            try:
                db.flush()
                categories_created.append(sheet_name)
                logger.info(f"Created category: {sheet_name}")
            except IntegrityError:
                db.rollback()
                # Try to fetch again in case of race condition
                statement = select(Category).where(Category.name == sheet_name)
                category = db.execute(statement).scalar_one_or_none()
                if category is None:
                    errors.append(f"خطا در ایجاد دسته‌بندی '{sheet_name}'")
                    continue
        
        category_map[sheet_name] = category.id
        
        # Validate and import books
        try:
            validated_books = validate_book_sheet_data(sheet_rows)
        except ValueError as e:
            errors.append(f"شیت '{sheet_name}': {str(e)}")
            continue
        
        for book_data in validated_books:
            book_name = book_data["name"]
            
            # Check if book already exists
            existing_statement = select(Book).where(
                Book.name == book_name,
                Book.category_id == category.id
            )
            existing = db.execute(existing_statement).scalar_one_or_none()
            
            if existing:
                total_skipped += 1
                continue
            
            book = Book(name=book_name, category_id=category.id)
            db.add(book)
            total_created += 1
    
    try:
        db.commit()
        cache.invalidate_book_search_cache()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit books: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در ذخیره‌سازی: {str(e)}"
        )
    
    return {
        "message": "عملیات آپلود با موفقیت انجام شد",
        "total_created": total_created,
        "total_skipped": total_skipped,
        "categories_created": categories_created,
        "errors": errors if errors else None,
    }
