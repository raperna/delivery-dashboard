from datetime import date

import pandas as pd
import streamlit as st

from dashboard.calendar import holidays_from_csv
from dashboard.config import (
    PROJECT_ROOT,
    holiday_path,
    load_config,
    status_settings,
    statuses_mapped_to,
)
from dashboard.loader import CHANGELOG_COLUMNS, MissingColumnsError, read_export
from dashboard.report import build_report, sprint_names

DATA_DIR = PROJECT_ROOT / "data"

BLOCKED_COLUMNS = {
    "key": "Issue",
    "team": "Team",
    "team_flag": "Team check",
    "developer": "Developer",
    "waiting_since": "Waiting since",
    "days_waiting": "Working days waiting",
}

TEAM_LEGEND = [
    ("Team", "Team label from Jira, as listed in config.yaml."),
    ("Status", "On track, At risk (shortfall of 5% or more), Off track (shortfall of 10% or more), Too early (before working day 5), or Not assessed (the blank-point share is over the limit, the items carry no points, or no items are committed)."),
    ("Committed (story points)", "Story points of the items in the sprint at the end of its start day. Blank points count as 1. Blank for Not assessed teams."),
    ("Expected by today (story points)", "Committed points × working days elapsed ÷ working days in the sprint, capped at the sprint length. Blank for Not assessed teams."),
    ("Done (story points)", "Story points of committed items whose status is Done on the report date. Blank for Not assessed teams."),
    ("Shortfall (%)", "(Expected − Done) ÷ Committed. Positive means behind plan, negative means ahead. Blank for Not assessed teams."),
    ("Velocity (story points)", "Story points Done on the report date, for teams assessed against commitment. Blank for Not assessed teams. N/A when no items are committed."),
    ("Throughput (work items)", "Committed items Done on the report date, for teams with status 'Not assessed'. Blank for assessed teams. N/A when no items are committed."),
]

BLOCKED_LEGEND = [
    ("Issue", "Jira issue key."),
    ("Team", "Team from the label on the report date. Team Unassigned if there is no team label or more than one."),
    ("Team check", "ok: one team label found. no_team: no team label, flagged. conflict: two team labels, flagged."),
    ("Developer", "Jira assignee on the report date. Blank if unassigned."),
    ("Waiting since", "Date of the most recent move into Blocked."),
    ("Working days waiting", "Working days after the Waiting since date, up to and including the report date. Weekends and holidays are skipped."),
]


def show_legend(title, legend):
    with st.expander(title):
        rows = "\n".join(f"| {name} | {meaning} |" for name, meaning in legend)
        st.markdown(f"| Column | Meaning |\n|---|---|\n{rows}")


def _points(value):
    return None if value is None else round(float(value), 1)


def team_display(teams):
    """Shape the team results for the screen. Numbers are not recalculated here."""
    rows = []
    for row in teams:
        na = row["speed"] == "N/A"
        rows.append({
            "Team": row["team"],
            "Status": row["status"],
            "Committed (story points)": _points(row["committed"]),
            "Expected by today (story points)": _points(row["expected"]),
            "Done (story points)": _points(row["done"]),
            "Shortfall (%)": None if row["shortfall"] is None else round(row["shortfall"] * 100, 1),
            "Velocity (story points)": "N/A" if na else _points(row["velocity"]),
            "Throughput (work items)": "N/A" if na else row["throughput"],
        })
    return pd.DataFrame(rows)


@st.cache_data
def load_changelog(raw_bytes):
    """Write the upload to data/ so the existing loader can check and read it."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / "uploaded_changelog.csv"
    path.write_bytes(raw_bytes)
    return read_export(path, CHANGELOG_COLUMNS, "changelog")


st.set_page_config(page_title="Delivery dashboard", layout="wide")
st.title("Delivery dashboard")

config = load_config()
settings = status_settings(config)
holidays = holidays_from_csv(holiday_path(config))
done_statuses = statuses_mapped_to(config, "Done")
blocked_statuses = statuses_mapped_to(config, "Blocked")
team_labels = config["team_labels"]

upload = st.sidebar.file_uploader("Jira changelog (CSV)", type="csv")
if upload is None:
    st.info("Upload a changelog CSV to begin. For a test run, use the synthetic file described in the project notes.")
    st.stop()

try:
    events = load_changelog(upload.getvalue())
except MissingColumnsError as error:
    st.error(str(error))
    st.stop()

names = sprint_names(events)
if not names:
    st.error("No Sprint events found in this changelog.")
    st.stop()

sprint = st.sidebar.selectbox("Sprint", names)
start = st.sidebar.date_input("Sprint start", value=date(2026, 3, 2))
end = st.sidebar.date_input("Sprint end", value=date(2026, 3, 13))
report_day = st.sidebar.date_input("Report date", value=date(2026, 3, 6))

report = build_report(
    events, sprint, start, end, report_day,
    team_labels, done_statuses, blocked_statuses, holidays, settings,
)

st.header(f"Sprint: {sprint}")
st.caption(
    f"{start:%d %b %Y} to {end:%d %b %Y} · Report date {report_day:%d %b %Y} · "
    f"Working day {report['elapsed_days']} of {report['sprint_days']}"
)

st.subheader("Team status")
st.dataframe(team_display(report["teams"]), hide_index=True, use_container_width=True)
show_legend("What the team status columns mean", TEAM_LEGEND)

st.subheader("Blocked items")
if report["blocked"]:
    blocked_table = pd.DataFrame(report["blocked"])[list(BLOCKED_COLUMNS)].rename(columns=BLOCKED_COLUMNS)
    st.dataframe(blocked_table, hide_index=True, use_container_width=True)
    show_legend("What the blocked item columns mean", BLOCKED_LEGEND)
else:
    st.write("No blocked items on this date.")

st.caption(
    "Status uses the percentage thresholds alone (D-024). Items with blank story "
    "points count as 1 point and are flagged (D-019). Unassigned blockers appear "
    "as Team Unassigned (D-025)."
)