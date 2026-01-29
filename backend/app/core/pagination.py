"""
Pagination utilities for ErgoLab API
Provides standard pagination for list endpoints
"""
from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query
from sqlalchemy import func
from fastapi import Query as QueryParam

T = TypeVar('T')


class PaginationParams:
    """Standard pagination parameters for API endpoints"""
    
    def __init__(
        self,
        page: int = QueryParam(1, ge=1, description="Page number (1-indexed)"),
        per_page: int = QueryParam(50, ge=1, le=200, description="Items per page (max 200)"),
        sort_by: Optional[str] = QueryParam(None, description="Field to sort by"),
        sort_order: str = QueryParam("asc", regex="^(asc|desc)$", description="Sort order")
    ):
        self.page = page
        self.per_page = per_page
        self.sort_by = sort_by
        self.sort_order = sort_order
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        return self.per_page


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    
    items: List[Any] = Field(description="List of items in current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_prev: bool = Field(description="Whether there are previous pages")
    
    class Config:
        from_attributes = True


def paginate(
    query: Query,
    page: int = 1,
    per_page: int = 50,
    sort_column: Optional[Any] = None,
    sort_desc: bool = False
) -> PaginatedResponse:
    """
    Apply pagination to a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Number of items per page
        sort_column: Optional SQLAlchemy column to sort by
        sort_desc: Whether to sort descending
    
    Returns:
        PaginatedResponse with items and pagination metadata
    """
    # Count total items (optimized count query)
    total = query.count()
    
    # Calculate pagination
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # Ensure page is within bounds
    page = max(1, min(page, pages))
    
    # Apply sorting if specified
    if sort_column is not None:
        if sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # Apply pagination
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


def paginate_with_params(
    query: Query,
    params: PaginationParams,
    model: Any = None
) -> PaginatedResponse:
    """
    Apply pagination using PaginationParams
    
    Args:
        query: SQLAlchemy query object
        params: PaginationParams instance
        model: Optional SQLAlchemy model for sorting
    
    Returns:
        PaginatedResponse with items and pagination metadata
    """
    sort_column = None
    sort_desc = params.sort_order == "desc"
    
    # Get sort column from model if specified
    if params.sort_by and model:
        sort_column = getattr(model, params.sort_by, None)
    
    return paginate(
        query=query,
        page=params.page,
        per_page=params.per_page,
        sort_column=sort_column,
        sort_desc=sort_desc
    )


class CursorPagination:
    """
    Cursor-based pagination for large datasets
    More efficient than offset pagination for deep pages
    """
    
    @staticmethod
    def paginate(
        query: Query,
        cursor_column: Any,
        cursor_value: Optional[Any] = None,
        limit: int = 50,
        direction: str = "next"
    ) -> dict:
        """
        Apply cursor-based pagination
        
        Args:
            query: SQLAlchemy query object
            cursor_column: Column to use as cursor (usually id or created_at)
            cursor_value: Current cursor position
            limit: Number of items to return
            direction: "next" or "prev"
        
        Returns:
            Dictionary with items and cursor information
        """
        # Apply cursor filter
        if cursor_value is not None:
            if direction == "next":
                query = query.filter(cursor_column > cursor_value)
            else:
                query = query.filter(cursor_column < cursor_value)
        
        # Order by cursor column
        if direction == "next":
            query = query.order_by(cursor_column.asc())
        else:
            query = query.order_by(cursor_column.desc())
        
        # Fetch one extra to check if there are more
        items = query.limit(limit + 1).all()
        
        has_more = len(items) > limit
        items = items[:limit]
        
        # Reverse for prev direction
        if direction == "prev":
            items = list(reversed(items))
        
        # Get cursors
        next_cursor = None
        prev_cursor = None
        
        if items:
            if has_more or direction == "prev":
                next_cursor = getattr(items[-1], cursor_column.key)
            if cursor_value is not None or direction == "prev":
                prev_cursor = getattr(items[0], cursor_column.key)
        
        return {
            "items": items,
            "next_cursor": next_cursor,
            "prev_cursor": prev_cursor,
            "has_more": has_more
        }


# Convenience functions for common use cases
def get_page_range(total: int, page: int, per_page: int, window: int = 5) -> List[int]:
    """
    Get a list of page numbers for pagination UI
    
    Args:
        total: Total number of items
        page: Current page
        per_page: Items per page
        window: Number of pages to show around current page
    
    Returns:
        List of page numbers to display
    """
    pages = (total + per_page - 1) // per_page
    
    if pages <= window * 2 + 1:
        return list(range(1, pages + 1))
    
    start = max(1, page - window)
    end = min(pages, page + window)
    
    # Adjust if at edges
    if start == 1:
        end = min(pages, window * 2 + 1)
    elif end == pages:
        start = max(1, pages - window * 2)
    
    return list(range(start, end + 1))
