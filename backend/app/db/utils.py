from __future__ import annotations

import os
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

CSV_DIR = Path(__file__).resolve().parents[3] / "csvFiles"
DOTENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=False)


def get_database_url() -> str:
    """
    Retrieve the database URL from environment variables.
    
    Returns:
        str: The database connection URL.
        
    Raises:
        RuntimeError: If DATABASE_URL environment variable is not set.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return url


def utcnow_sql():
    return text("CURRENT_TIMESTAMP")


def parse_date(value: Optional[str]) -> Optional[datetime.date]:
    """
    Parse a date string into a date object, trying multiple formats.
    
    Attempts to parse the date using the following formats in order:
    - d.m.yyyy (e.g., "15.03.2024")
    - yyyy-mm-dd (e.g., "2024-03-15")
    - mm/dd/yyyy (e.g., "03/15/2024")
    
    Args:
        value: String representation of a date, or None.
        
    Returns:
        Parsed date object if successful, None otherwise.
    """
    if value is None:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def parse_time(value: Optional[str]) -> Optional[time]:
    """
    Parse a time string into a time object, trying multiple formats.
    
    Attempts to parse the time using the following formats in order:
    - HH:MM (24-hour, e.g., "14:30")
    - HH:MM:SS (24-hour with seconds, e.g., "14:30:45")
    - I:M p (12-hour with AM/PM, e.g., "2:30 PM")
    - I:M:S p (12-hour with seconds and AM/PM, e.g., "2:30:45 PM")
    
    Args:
        value: String representation of a time, or None.
        
    Returns:
        Parsed time object if successful, None otherwise.
    """
    if value is None:
        return None
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"):
        try:
            return datetime.strptime(value, fmt).time()
        except (ValueError, TypeError):
            continue
    return None


def parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    """
    Parse a value into a Decimal object, handling various input types.
    
    Accepts strings, integers, floats, or Decimal objects. Handles "NA", "N/A",
    and empty strings as None. Converts numeric types to Decimal for precision.
    
    Args:
        value: String, int, float, Decimal, or None to parse.
        
    Returns:
        Decimal object if parsing succeeds, None otherwise.
    """
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except Exception:
            return None
    if not value or value.upper() == "NA":
        return None
    try:
        return Decimal(value)
    except Exception:
        return None


def normalized(value: Optional[str]) -> Optional[str]:
    """
    Normalize a string value by trimming whitespace and converting null indicators to None.
    
    Strips whitespace and converts common null indicators (NULL, N/A, NA, empty string)
    to None. Useful for cleaning CSV data.
    
    Args:
        value: String value to normalize, or None.
        
    Returns:
        Normalized string or None if value represents a null/empty value.
    """
    if value is None:
        return None
    value = value.strip()
    if value.upper() in {"NULL", "N/A", "NA", ""}:
        return None
    return value


def read_csv(name: str, drop_pk: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
    """
    Read a CSV file and return its contents as a list of dictionaries.
    
    Reads CSV from the csvFiles directory, strips whitespace from string values,
    optionally removes duplicate rows based on primary key columns, and normalizes
    null indicators (NULL, N/A, NA, empty strings) to None.
    
    Args:
        name: Name of the CSV file (e.g., "patients.csv").
        drop_pk: Optional list of column names to use for duplicate detection.
                 If provided, keeps only the first occurrence of each unique combination.
    
    Returns:
        List of dictionaries, where each dictionary represents a row with column
        names as keys.
        
    Raises:
        FileNotFoundError: If the CSV file does not exist in the csvFiles directory.
    """
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    df = pd.read_csv(path, keep_default_na=False).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    if drop_pk:
        df = df.drop_duplicates(subset=drop_pk, keep="first")
    df = df.replace({"NULL": None, "null": None, "N/A": None, "NA": None, "": None})
    return df.to_dict(orient="records")


def chunked(iterable: List[Dict[str, Any]], size: int = 500):
    """
    Split a list into chunks of a specified size.
    
    Useful for batch processing large datasets to avoid memory issues.
    Yields chunks as lists, with the last chunk potentially smaller than the
    specified size.
    
    Args:
        iterable: List to chunk.
        size: Maximum number of items per chunk. Defaults to 500.
        
    Yields:
        Lists of items, each containing up to 'size' elements.
    """
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]

