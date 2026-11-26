from dashboard.sprints import split_sprints, sprint_changes


def test_empty_value_means_no_sprints():
    assert split_sprints("") == []
    assert split_sprints(float("nan")) == []


def test_splits_on_comma_space():
    assert split_sprints("Sprint 29, Sprint 30") == ["Sprint 29", "Sprint 30"]


def test_first_event_adds_everything_and_removes_nothing():
    changes = sprint_changes(["Sprint 29, Sprint 30"])
    assert changes == [({"Sprint 29", "Sprint 30"}, set())]


def test_adding_a_sprint_reports_only_the_new_one():
    changes = sprint_changes(["Sprint 29", "Sprint 29, Sprint 30"])
    assert changes[1] == ({"Sprint 30"}, set())


def test_removing_a_sprint_reports_it_as_removed():
    changes = sprint_changes(["Sprint 29, Sprint 30", "Sprint 29"])
    assert changes[1] == (set(), {"Sprint 30"})


def test_moved_out_and_back_in_is_recorded_both_ways():
    changes = sprint_changes(["Sprint 29", "", "Sprint 29"])
    assert changes[1] == (set(), {"Sprint 29"})
    assert changes[2] == ({"Sprint 29"}, set())