from dashboard.parsers import parse_labels


def test_empty_list_gives_no_labels():
    assert parse_labels("[]") == []


def test_single_label():
    assert parse_labels("['bite-sized']") == ["bite-sized"]


def test_space_separated_labels_are_split():
    # Exact format seen in the Kaggle issues.csv
    assert parse_labels("['JDK1.5' 'PatchAvailable']") == ["JDK1.5", "PatchAvailable"]


def test_missing_value_gives_no_labels():
    # Empty cells in a CSV load as NaN, not as a string
    assert parse_labels(float("nan")) == []


def test_labels_with_hyphens_and_dots_are_kept_whole():
    assert parse_labels("['tech-debt' 'v1.2.3']") == ["tech-debt", "v1.2.3"]