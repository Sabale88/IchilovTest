"""Unit tests for snapshot builder functions."""
import pytest
from datetime import date, time, datetime, timedelta
from decimal import Decimal

from backend.app.db.snapshot_builder import (
    _coerce_date,
    _coerce_time,
    _combine_datetime,
    _hours_between,
    _format_duration,
    _calculate_age,
    _max_datetime,
    _to_float,
    _is_active,
)


class TestCoerceDate:
    """Tests for _coerce_date function."""

    def test_coerce_date_from_date(self):
        """Test coercing a date object."""
        d = date(2024, 3, 15)
        assert _coerce_date(d) == date(2024, 3, 15)

    def test_coerce_date_from_datetime(self):
        """Test coercing a datetime object."""
        dt = datetime(2024, 3, 15, 14, 30)
        assert _coerce_date(dt) == date(2024, 3, 15)

    def test_coerce_date_from_string_dm_yyyy(self):
        """Test coercing date string in d.m.yyyy format."""
        assert _coerce_date("15.03.2024") == date(2024, 3, 15)

    def test_coerce_date_from_string_yyyy_mm_dd(self):
        """Test coercing date string in yyyy-mm-dd format."""
        assert _coerce_date("2024-03-15") == date(2024, 3, 15)

    def test_coerce_date_none(self):
        """Test coercing None returns None."""
        assert _coerce_date(None) is None

    def test_coerce_date_invalid(self):
        """Test coercing invalid value returns None."""
        assert _coerce_date("invalid") is None
        assert _coerce_date(123) is None


class TestCoerceTime:
    """Tests for _coerce_time function."""

    def test_coerce_time_from_time(self):
        """Test coercing a time object."""
        t = time(14, 30, 45)
        assert _coerce_time(t) == time(14, 30, 45)

    def test_coerce_time_from_datetime(self):
        """Test coercing a datetime object."""
        dt = datetime(2024, 3, 15, 14, 30, 45)
        assert _coerce_time(dt) == time(14, 30, 45)

    def test_coerce_time_from_string_hh_mm(self):
        """Test coercing time string in HH:MM format."""
        assert _coerce_time("14:30") == time(14, 30)

    def test_coerce_time_from_string_hh_mm_ss(self):
        """Test coercing time string in HH:MM:SS format."""
        assert _coerce_time("14:30:45") == time(14, 30, 45)

    def test_coerce_time_none(self):
        """Test coercing None returns None."""
        assert _coerce_time(None) is None

    def test_coerce_time_invalid(self):
        """Test coercing invalid value returns None."""
        assert _coerce_time("invalid") is None


class TestCombineDatetime:
    """Tests for _combine_datetime function."""

    def test_combine_datetime_with_time(self):
        """Test combining date and time."""
        d = date(2024, 3, 15)
        t = time(14, 30)
        result = _combine_datetime(d, t)
        assert result == datetime(2024, 3, 15, 14, 30)

    def test_combine_datetime_without_time(self):
        """Test combining date without time uses time.min."""
        d = date(2024, 3, 15)
        result = _combine_datetime(d, None)
        assert result == datetime(2024, 3, 15, 0, 0)

    def test_combine_datetime_none_date(self):
        """Test combining None date returns None."""
        assert _combine_datetime(None, time(14, 30)) is None

    def test_combine_datetime_strings(self):
        """Test combining date and time strings."""
        result = _combine_datetime("15.03.2024", "14:30")
        assert result == datetime(2024, 3, 15, 14, 30)


class TestHoursBetween:
    """Tests for _hours_between function."""

    def test_hours_between_positive(self):
        """Test calculating hours between two datetimes."""
        start = datetime(2024, 3, 15, 10, 0)
        end = datetime(2024, 3, 15, 14, 30)
        result = _hours_between(start, end)
        assert result == 4.5

    def test_hours_between_negative(self):
        """Test calculating hours when end is before start."""
        start = datetime(2024, 3, 15, 14, 30)
        end = datetime(2024, 3, 15, 10, 0)
        result = _hours_between(start, end)
        assert result == -4.5

    def test_hours_between_none_start(self):
        """Test calculating hours with None start returns None."""
        end = datetime(2024, 3, 15, 14, 30)
        assert _hours_between(None, end) is None

    def test_hours_between_rounding(self):
        """Test hours are rounded to 2 decimal places."""
        start = datetime(2024, 3, 15, 10, 0, 0)
        end = datetime(2024, 3, 15, 10, 1, 30)  # 1.5 minutes = 0.025 hours
        result = _hours_between(start, end)
        assert result == 0.03  # Rounded to 2 decimals


class TestFormatDuration:
    """Tests for _format_duration function."""

    def test_format_duration_hours_only(self):
        """Test formatting duration with only hours."""
        assert _format_duration(5.5) == "5h"

    def test_format_duration_days(self):
        """Test formatting duration with days."""
        assert _format_duration(48.0) == "2d"

    def test_format_duration_weeks(self):
        """Test formatting duration with weeks."""
        assert _format_duration(336.0) == "2w"  # 14 days

    def test_format_duration_years(self):
        """Test formatting duration with years."""
        assert _format_duration(8760.0) == "1y"  # 365 days

    def test_format_duration_complex(self):
        """Test formatting complex duration."""
        # 1 year, 2 weeks, 3 days, 4 hours
        hours = (365 * 24) + (2 * 7 * 24) + (3 * 24) + 4
        result = _format_duration(float(hours))
        assert result == "1y, 2w, 3d, 4h"

    def test_format_duration_none(self):
        """Test formatting None duration."""
        assert _format_duration(None) == "N/A"

    def test_format_duration_negative(self):
        """Test formatting negative duration."""
        assert _format_duration(-5.0) == "N/A"


class TestCalculateAge:
    """Tests for _calculate_age function."""

    def test_calculate_age_birthday_passed(self):
        """Test age calculation when birthday has passed."""
        dob = date(2000, 1, 15)
        ref = datetime(2024, 3, 20)
        assert _calculate_age(dob, ref) == 24

    def test_calculate_age_birthday_not_passed(self):
        """Test age calculation when birthday hasn't passed."""
        dob = date(2000, 5, 15)
        ref = datetime(2024, 3, 20)
        assert _calculate_age(dob, ref) == 23

    def test_calculate_age_birthday_today(self):
        """Test age calculation on birthday."""
        dob = date(2000, 3, 20)
        ref = datetime(2024, 3, 20)
        assert _calculate_age(dob, ref) == 24

    def test_calculate_age_none(self):
        """Test age calculation with None date of birth."""
        ref = datetime(2024, 3, 20)
        assert _calculate_age(None, ref) is None


class TestMaxDatetime:
    """Tests for _max_datetime function."""

    def test_max_datetime_multiple(self):
        """Test finding max datetime from multiple values."""
        dt1 = datetime(2024, 3, 15, 10, 0)
        dt2 = datetime(2024, 3, 15, 14, 30)
        dt3 = datetime(2024, 3, 15, 12, 0)
        assert _max_datetime(dt1, dt2, dt3) == dt2

    def test_max_datetime_with_none(self):
        """Test finding max datetime with None values."""
        dt1 = datetime(2024, 3, 15, 10, 0)
        dt2 = None
        dt3 = datetime(2024, 3, 15, 14, 30)
        assert _max_datetime(dt1, dt2, dt3) == dt3

    def test_max_datetime_all_none(self):
        """Test finding max datetime when all are None."""
        assert _max_datetime(None, None) is None

    def test_max_datetime_single(self):
        """Test finding max datetime with single value."""
        dt = datetime(2024, 3, 15, 10, 0)
        assert _max_datetime(dt) == dt


class TestToFloat:
    """Tests for _to_float function."""

    def test_to_float_from_decimal(self):
        """Test converting Decimal to float."""
        value = Decimal("123.45")
        assert _to_float(value) == 123.45

    def test_to_float_from_int(self):
        """Test converting int to float."""
        assert _to_float(123) == 123.0

    def test_to_float_from_float(self):
        """Test converting float to float."""
        assert _to_float(123.45) == 123.45

    def test_to_float_from_string(self):
        """Test converting string to float."""
        assert _to_float("123.45") == 123.45

    def test_to_float_none(self):
        """Test converting None returns None."""
        assert _to_float(None) is None

    def test_to_float_invalid(self):
        """Test converting invalid value returns None."""
        assert _to_float("invalid") is None


class TestIsActive:
    """Tests for _is_active function."""

    def test_is_active_no_release(self):
        """Test admission with no release date is active."""
        admission = {"release_date": None, "release_time": None}
        now = datetime(2024, 3, 15, 14, 30)
        grace = timedelta(hours=2)
        assert _is_active(admission, now, grace) is True

    def test_is_active_within_grace(self):
        """Test admission released within grace period is active."""
        admission = {"release_date": "15.03.2024", "release_time": "13:00"}
        now = datetime(2024, 3, 15, 14, 30)
        grace = timedelta(hours=2)
        assert _is_active(admission, now, grace) is True

    def test_is_active_beyond_grace(self):
        """Test admission released beyond grace period is not active."""
        admission = {"release_date": "15.03.2024", "release_time": "10:00"}
        now = datetime(2024, 3, 15, 14, 30)
        grace = timedelta(hours=2)
        assert _is_active(admission, now, grace) is False

