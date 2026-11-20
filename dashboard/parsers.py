import math
import re

# Matches each single-quoted item, e.g. 'PatchAvailable'
_QUOTED_ITEM = re.compile(r"'([^']*)'")


def parse_labels(value):
    """Parse the labels column from a Kaggle issues.csv export.

    The cell holds a Python-style list printed as text, with quoted items
    separated by spaces: "['JDK1.5' 'PatchAvailable']". An empty list is "[]".
    An empty cell arrives from pandas as NaN, not as a string.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    return _QUOTED_ITEM.findall(str(value))