"""Unit tests for database utility functions."""
import pytest
from datetime import date, time, datetime
from decimal import Decimal

from backend.app.db.utils import (
    parse_date,
    parse_time,
    parse_decimal,
    normalized,
    chunked,
)


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_date_dm_yyyy(self):
        """Test parsing date in d.m.yyyy format."""
        result = parse_date("15.03.2024")
        assert result == date(2024, 3, 15)

    def test_parse_date_yyyy_mm_dd(self):
        """Test parsing date in yyyy-mm-dd format."""
        result = parse_date("2024-03-15")
        assert result == date(2024, 3, 15)

    def test_parse_date_mm_dd_yyyy(self):
        """Test parsing date in mm/dd/yyyy format."""
        result = parse_date("03/15/2024")
        assert result == date(2024, 3, 15)

    def test_parse_date_none(self):
        """Test parsing None returns None."""
        assert parse_date(None) is None

    def test_parse_date_invalid(self):
        """Test parsing invalid date returns None."""
        assert parse_date("invalid") is None
        assert parse_date("2024-13-45") is None


class TestParseTime:
    """Tests for parse_time function."""

    def test_parse_time_hh_mm(self):
        """Test parsing time in HH:MM format."""
        result = parse_time("14:30")
        assert result == time(14, 30)

    def test_parse_time_hh_mm_ss(self):
        """Test parsing time in HH:MM:SS format."""
        result = parse_time("14:30:45")
        assert result == time(14, 30, 45)

    def test_parse_time_12h_am(self):
        """Test parsing 12-hour format with AM."""
        result = parse_time("2:30 AM")
        assert result == time(2, 30)

    def test_parse_time_12h_pm(self):
        """Test parsing 12-hour format with PM."""
        result = parse_time("2:30 PM")
        assert result == time(14, 30)

    def test_parse_time_none(self):
        """Test parsing None returns None."""
        assert parse_time(None) is None

    def test_parse_time_invalid(self):
        """Test parsing invalid time returns None."""
        assert parse_time("invalid") is None
        assert parse_time("25:00") is None


class TestParseDecimal:
    """Tests for parse_decimal function."""

    def test_parse_decimal_string(self):
        """Test parsing decimal from string."""
        result = parse_decimal("123.45")
        assert result == Decimal("123.45")

    def test_parse_decimal_int(self):
        """Test parsing decimal from integer."""
        result = parse_decimal(123)
        assert result == Decimal("123")

    def test_parse_decimal_float(self):
        """Test parsing decimal from float."""
        result = parse_decimal(123.45)
        assert result == Decimal("123.45")

    def test_parse_decimal_decimal(self):
        """Test parsing decimal from Decimal."""
        value = Decimal("123.45")
        result = parse_decimal(value)
        assert result == Decimal("123.45")

    def test_parse_decimal_none(self):
        """Test parsing None returns None."""
        assert parse_decimal(None) is None

    def test_parse_decimal_na(self):
        """Test parsing 'NA' returns None."""
        assert parse_decimal("NA") is None
        assert parse_decimal("na") is None

    def test_parse_decimal_empty(self):
        """Test parsing empty string returns None."""
        assert parse_decimal("") is None

    def test_parse_decimal_invalid(self):
        """Test parsing invalid value returns None."""
        assert parse_decimal("invalid") is None


class TestNormalized:
    """Tests for normalized function."""

    def test_normalized_string(self):
        """Test normalizing a valid string."""
        result = normalized("  test  ")
        assert result == "test"

    def test_normalized_none(self):
        """Test normalizing None returns None."""
        assert normalized(None) is None

    def test_normalized_null_indicators(self):
        """Test normalizing null indicators returns None."""
        assert normalized("NULL") is None
        assert normalized("N/A") is None
        assert normalized("NA") is None
        assert normalized("") is None
        assert normalized("  ") is None

    def test_normalized_case_insensitive(self):
        """Test null indicators are case-insensitive."""
        assert normalized("null") is None
        assert normalized("n/a") is None
        assert normalized("na") is None


class TestChunked:
    """Tests for chunked function."""

    def test_chunked_exact_size(self):
        """Test chunking list with exact size."""
        data = list(range(10))
        chunks = list(chunked(data, size=5))
        assert len(chunks) == 2
        assert chunks[0] == [0, 1, 2, 3, 4]
        assert chunks[1] == [5, 6, 7, 8, 9]

    def test_chunked_remainder(self):
        """Test chunking list with remainder."""
        data = list(range(10))
        chunks = list(chunked(data, size=3))
        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[3] == [9]

    def test_chunked_empty(self):
        """Test chunking empty list."""
        chunks = list(chunked([], size=5))
        assert len(chunks) == 0

    def test_chunked_single_chunk(self):
        """Test chunking list smaller than chunk size."""
        data = list(range(3))
        chunks = list(chunked(data, size=5))
        assert len(chunks) == 1
        assert chunks[0] == [0, 1, 2]

    def test_chunked_default_size(self):
        """Test chunking with default size."""
        data = list(range(1500))
        chunks = list(chunked(data))
        assert len(chunks) == 3
        assert len(chunks[0]) == 500
        assert len(chunks[2]) == 500

