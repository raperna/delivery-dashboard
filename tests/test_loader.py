from pathlib import Path

import pytest

from dashboard.loader import CHANGELOG_COLUMNS, MissingColumnsError, read_export

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_loads_changelog_with_required_columns():
    df = read_export(FIXTURES / "changelog_small.csv", CHANGELOG_COLUMNS, "changelog")
    assert len(df) == 4
    assert set(df["key"]) == {"DEMO-1", "DEMO-2"}


def test_extra_columns_are_allowed():
    # The fixture has an 'author' column that isn't required. Real Jira exports
    # have dozens of extra columns, and they must not cause an error.
    df = read_export(FIXTURES / "changelog_small.csv", CHANGELOG_COLUMNS, "changelog")
    assert "author" in df.columns


def test_missing_column_is_named_in_error():
    with pytest.raises(MissingColumnsError) as excinfo:
        read_export(
            FIXTURES / "changelog_missing_column.csv", CHANGELOG_COLUMNS, "changelog"
        )
    assert excinfo.value.missing == ["fromString"]
    assert "fromString" in str(excinfo.value)
    assert "changelog" in str(excinfo.value)