import base64
from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import DateTime, Date

from app.models.job_application import JobApplication


def encode_cursor(sort_val, uid: UUID) -> str:
    """Combines a timestamp and UUID into a Base64 string."""
    if isinstance(sort_val, datetime):
        sort_val = sort_val.isoformat()
    if isinstance(sort_val, str):
        sort_val = sort_val
    combined = f"{sort_val}|{uid}"
    return base64.b64encode(combined.encode()).decode()

def decode_cursor(cursor_str: str) -> tuple[str, UUID]:
    """Decodes a Base64 string back into Python objects."""
    try:
        decoded = base64.b64decode(cursor_str.encode()).decode()
        dt_str, uid_str = decoded.split("|")
        return dt_str, UUID(uid_str)
    except Exception:
        raise ValueError("Invalid cursor format")


def cast_to_column_type(value: str, column):
    """
    Casts a string value from a cursor into the Python type
    required by the SQLAlchemy column.
    """
    column_type = column.type
    if isinstance(column_type, DateTime):
        return datetime.fromisoformat(value)
    if isinstance(column_type, Date):
        return datetime.fromisoformat(value)
    return value


def retrieve_last_item_key(sort_val, last_item: JobApplication):
    if sort_val == "created_at":
        return last_item.created_at
    elif sort_val == "updated_at":
        return last_item.updated_at
    elif sort_val == "date_applied":
        return last_item.date_applied
    elif sort_val == "company_name":
        return last_item.company_name
    else:
        raise HTTPException(status_code=404, detail="Error retrieving last item key")