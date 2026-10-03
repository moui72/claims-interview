"""Opaque cursors for keyset pagination over the claims queue."""

import base64
from datetime import datetime


def encode_cursor(submitted_at: datetime) -> str:
    return base64.urlsafe_b64encode(submitted_at.isoformat().encode()).decode()


def decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())
