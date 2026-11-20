from pathlib import Path

import pandas as pd

# Columns the changelog must have. Extra columns are allowed, because real
# Jira exports contain many more fields than we need.
CHANGELOG_COLUMNS = ["key", "created", "field", "fromString", "toString"]


class MissingColumnsError(ValueError):
    def __init__(self, missing, source):
        self.missing = list(missing)
        self.source = source
        super().__init__(
            f"{source} is missing required column(s): {', '.join(self.missing)}"
        )


def read_export(path, required, source):
    """Read a CSV export after checking that the required columns exist."""
    header = pd.read_csv(Path(path), nrows=0).columns.tolist()
    missing = [column for column in required if column not in header]
    if missing:
        raise MissingColumnsError(missing, source)
    return pd.read_csv(Path(path))