# Changelog

Project log for the Delivery Metrics Dashboard. It records objectives, requirements, decisions, user stories, and changes, so the history of the project is visible in one place.

Format follows [Keep a Changelog](https://keepachangelog.com). Decisions are logged as numbered records (D-001 onward) with the reason and the alternatives considered. Entries are never deleted. If a decision changes, a new record supersedes the old one.

## Objectives

- **O1.** Show whether each team's committed sprint scope will land, with a confidence status.
- **O2.** Show whether each project is improving or worsening over the last 3 to 4 sprints.
- **O3.** Show what is blocked, who owns unblocking it, and how long it has waited.
- **O4.** Demonstrate the full SDLC: requirements, design, build, test, CI/CD, and deployment, with AI assistance used and reviewed at each stage.

## Scope

**In scope (v1):** CSV ingestion of Jira changelog and sprint exports, team status with a linear burn-down, trends, blocked items, filters, a leadership summary export.

**Out of scope (v1):** live Jira API sync, authentication, forecasting beyond the burn-down, ranking individuals, cross-team "waiting on" fields.

## Requirements

Version 0.4. The full requirements text lives in `docs/REQUIREMENTS.md` (to be created in Phase 2 close-out).

**Key questions the dashboard must answer**

1. Will the committed scope for this sprint or release land, and how confident are we?
2. Is each project getting better or worse over the last 3 to 4 sprints?
3. What is holding up delivery, who owns unblocking it, and how long has it been waiting?

**Status rules**

- Expected done = committed points × (working days elapsed ÷ working days in sprint).
- Shortfall = (expected done − done) ÷ committed.
- On track below 5%. At risk from 5% to below 10%. Off track at 10% or more.
- Too early before working day 5 of a 10-day sprint.
- Not assessed applies when the defaulted-points share is over the limit, or when no committed item in the sprint has points (D-019). Throughput is shown in those cases.

**Data requirements**

- Changelog export: issue key, timestamp, field, from, to. Fields: status, Sprint, labels, assignee.
- Issues export: current values per issue.
- Sprint table: sprint name, board, start date, end date. Proposed columns, pending confirmation.

## Decisions

| ID | Decision | Reason | Alternatives considered | Phase |
|---|---|---|---|---|
| D-001 | Use Python 3.11, managed with uv | 3.7 is end-of-life and unsupported by current pandas and Streamlit. uv pins the version per project. | Replace system Python; use conda | 3 |
| D-002 | Keep calculations in pure functions under `dashboard/`, with the UI in `app.py` only | Logic can be unit-tested without a browser. Most bugs will be in the maths. | Logic inside Streamlit callbacks | 2 |
| D-003 | Put all thresholds, mappings, and holidays in `config.yaml` | A PM can adjust rules without a code change, and a test checks the config is consistent. | Constants in code | 2 |
| D-004 | Two tables: an events table from the changelog, and an issues table for current state | History questions (cycle time, commitment) and current-state questions (blocked list, status) need different data. Mixing them causes wrong numbers for past sprints. | One flat table | 2 |
| D-005 | Team comes from Jira labels | Confirmed in the Kaggle `issues.csv` labels column. Labels are free text, so matching is case-insensitive against a configured list. | Custom team field (not present in the export) | 2 |
| D-006 | Developer is the Jira assignee | Matches the export and how Jira records ownership. | Separate developer field | 1 |
| D-007 | Team leads are accountable for their team's blockers | Confirmed by the user. The team is the escalation unit, and the assignee is the person doing the work. | Assignee as owner | 1 |
| D-008 | Use working days from the Barcelona calendar | Weekends and holidays otherwise distort the expected line. Catalonia and local holidays come from the Ajuntament calendar. | Calendar days | 1 |
| D-009 | Use a linear burn-down with a midpoint rule and a two-item minimum | Simple to explain to leadership, and the rules stop single late tickets from changing a status. Linear burn is flagged as a risk to backtest. | Historical curve; forecasting models | 1 |
| D-010 | Show cause signals as prompts for team leads, not as conclusions | Jira records what happened, not why. Presenting causes as facts would overstate what the data supports. | Labelled root causes | 1 |
| D-011 | Use synthetic data as the main test source, and Kaggle as a robustness check | Synthetic data has known correct answers. Kaggle has real messiness but no sprint dates or team labels. | Real company data (not allowed in repo) | 2 |
| D-012 | Identify sprints by name plus board | Sprint names aren't unique across projects and carry no parseable dates. | Name alone | 2 |
| D-013 | Parse the labels list with a regular expression matching quoted items | The Kaggle format is space-separated and quoted, so a comma or space split would break labels. | `ast.literal_eval`; comma split | 3 |
| D-014 | Exclude `data/` and `*.csv` from Git, with an exception for `tests/fixtures/` | Exports may contain company data, and the Kaggle changelog is 2.7 GB. Fixtures must be committed so CI can run. | Commit everything | 3 |
| D-015 | Write failing tests before the code they test | Confirms each test checks real behaviour. A test that never fails proves nothing. | Code first, tests after | 3 |
| D-016 | Keep the project in `C:\...\SDLC\delivery-dashboard` on the first PC, and in `D:\...` on the second | Each machine follows its own folder convention. The remote repository is the shared source. | One fixed path | 3 |
| D-017 | Sprint changes are the diff between consecutive full-list events for the same issue | Jira stores the full sprint list after each change, so a single event can't show what was added or removed. Comparing with the previous state gives an explicit record of each change, including moves out and back in. | Treating each event as a single change | 3 |
| D-018 | Effort is measured in story points for every team. Item counts are not used. | Points are each team's own estimate and already drive the status rules. Counts for some teams would make percentages incomparable across teams. Overriding points would make the report disagree with what teams recognise. | Item counts as a fallback for non-estimating teams; a separate effort weight | 1 |
| D-019 | Items with no story points get a default of 1 point, set in config.yaml. Each defaulted item is counted and shown as a warning. If the defaulted share of a team's commitment exceeds the configured limit, the team's status is Not assessed. If no committed item in a sprint has points, the status is Not assessed and throughput (item count) is the only speed measure shown. Speed and commitment status are labelled separately on the dashboard. | Real exports and test data will have gaps. A default keeps totals complete, while the warning and the limit stop a default from producing a confident status. A fully unpointed sprint has no basis for a commitment comparison, so it shows throughput only. Excluding unpointed items hides scope, and counting them as 0 understates work. | Exclude unpointed items; count them as 0; show a status built on defaults for unpointed sprints | 3 |
| D-020 | Commitment is the set of items in a sprint at the end of its start day. An item's team is the single team label it has at that moment. Items with no team label, or two team labels, are flagged and excluded from team status. Label matching is case-insensitive. | The end of the start day lets planning-day additions count as committed, and later additions are scope change. A team can only be read from one label, so ambiguity is flagged rather than guessed. | Start of day (excludes planning-day additions); labels at the time of reporting | 3 |
| D-021 | Single-valued fields (story points, status) are replayed with the same cutoff as labels and sprints. The latest event at or before the cutoff gives the value. A blank or cleared value is None, not zero. Points are read as numbers. | One replay rule for every field means one set of cutoff and ordering behaviour to test. Treating a cleared value as zero would count an unestimated item as trivial. | A separate function per field; storing values as text and converting later | 3 |
| D-022 | Working days are Monday to Friday, excluding holidays from the configured calendar. A sprint's working days are counted inclusively from its start date to its end date. Working days elapsed on a date are counted inclusively from the start date to that date, and are zero before the start. A holiday on a weekend does not remove a working day. | Expected done depends on working days, not calendar days, so weekends and holidays do not distort the burn-down. Counting from the start date keeps the midpoint rule (working day 5) simple to explain. | Calendar days; counting from the first working day after a weekend start | 3 |
| D-023 | A team's status compares committed points done by the report date with the linear expected amount: committed × working days elapsed (capped at sprint length) ÷ sprint working days. Shortfall = (expected − done) ÷ committed. Too early before the midpoint working day. At risk at a shortfall of 5% or more, Off track at 10% or more, using the percentage alone. Not assessed when the sprint rule in D-019 applies or no points are committed. | Each part of the rule is a separate, testable step. The cap stops a report run after sprint end from inflating the expected amount. | Count-based expectation; percentage with a minimum-size gate (see D-024) | 3 |
| D-024 | The minimum-size gate from D-009 is removed. The percentage thresholds alone decide the status. The report states which rule produced each status. | The team chose to let the percentage decide, so one late item can change a status on small teams. This is accepted and made visible, rather than hidden by a gate. | Keep the two-item minimum from D-009 | 3 |
| D-025 | Blocked items with no team label, or with two team labels, appear in the blocked list under "Team Unassigned", flagged. They are never dropped from the report. | A blocker that disappears from the report is the problem leadership most needs to see. Showing it as unassigned makes the gap visible, so someone fixes the label. | Hide until the label is fixed; attribute to the assignee | 1 |
| D-026 | A team snapshot joins three sources into plain item records: committed membership and team from the start day (D-020), points from the start day (D-021), and done status from the report date. The status rule receives these records and never reads events directly. | Each source answers one question at one date, and the join is the only place those dates meet. Keeping the status rule free of events means it can be tested with plain lists, as it already is. | Status rule reads events directly; one function that does everything | 3 |
| D-027 | The blocked list shows items whose status is a configured blocked status on the report date. Days waiting are calendar days from the latest change into Blocked to the report date. The team comes from the label on the report date, and the developer is the assignee on the report date. The list is sorted longest wait first. | A blocker is a clock running in real time, so calendar days match what the team experiences. The report date is used throughout, so the list agrees with the status view for the same day. | Working days (a one-line change if preferred); waiting from the first block ever, which hides re-blocks | 3 |
| D-028 | Throughput counts items whose first Done transition falls between the sprint's start and end dates, inclusive, by completion date, regardless of sprint membership. Velocity sums the effective points (D-019 default for blanks) of those items, using points as at the end of the sprint's end date. Velocity is shown only when the blank share of completed items is at or below the limit; otherwise the sprint shows throughput only. | Counting by completion date, not membership, matches how the team experiences delivery (US-03). Points at sprint end are a single, reproducible snapshot; points at each completion date would need a lookup per item. | Count by sprint membership; points at each completion date | 3 |
| D-029 | Cycle time is calendar days from the first transition into a started status to the first transition into a Done status. An item whose first Done comes before its first start, or that never reaches Done, is counted separately and excluded. Median and 85th percentile use linear interpolation. | Calendar days match the time a work item takes in real life. Reporting the excluded counts stops a short median from hiding unfinished or unstarted work. | Working days; excluding the counts | 3 |
| D-030 | Rolling velocity averages the last three sprints, oldest to newest. A sprint with no velocity makes the average blank. | Averaging over three sprints smooths single outliers for the trend view (Question 2). A blank average, rather than an average of the sprints that have data, avoids a trend that silently skips a sprint. | Average the sprints that have data; a five-sprint window | 3 |
| D-031 | Settings are read from config.yaml through one loader that validates the status settings before use. The holiday list is read from the CSV path in config. Synthetic scenarios are generated in code with expected results worked out by hand, and end-to-end tests check the full chain against them. The generator lives in dashboard/, so tests can import it. A command-line wrapper that writes a CSV is deferred to the interface step. | One validated loader means a bad threshold fails at startup, not in a report. Hand-worked expectations catch errors that unit tests can miss, because each unit can be correct while the chain between them is wrong. Keeping the generator importable avoids a packaging problem for scripts/ that we don't need yet. | Settings as module constants; generator in scripts/ | 3 |

## User stories

Status: Not started, In progress, Done.

| ID | Story | Priority | Status |
|---|---|---|---|
| US-01 | Upload and validate a CSV, naming missing columns | Must | In progress (loader done; upload UI not started) |
| US-02 | Configure rules without editing code | Must | In progress (config file done; UI not started) |
| US-03 | See each team's committed scope at sprint start | Must | Not started |
| US-04 | See each team's health: On track, At risk, Off track, Too early | Must | Not started |
| US-05 | See throughput, velocity, and cycle time trends over 3 to 4 sprints | Must | Not started |
| US-06 | See blocked items with owner team, developer, and days waiting | Must | Not started |
| US-07 | See scope changes after sprint start | Should | Not started |
| US-08 | See "where to look next" prompts for At risk or Off track teams | Should | Not started |
| US-09 | Filter by team, project, and sprint | Should | Not started |
| US-10 | Export a one-page leadership summary | Should | Not started |

## [Unreleased]

### Phase 1: Requirements (closed)

- Requirements v0.1: one-page draft with metric definitions, data requirements, and the first backlog.
- Requirements v0.2: key questions revised after senior DM review. Lagging became a forecast, trends replaced snapshots, and blocked items gained owners.
- Requirements v0.3: team source defined as Jira labels.
- Requirements v0.4: sprint table added as a third data source, and the labels and sprint formats confirmed from Kaggle.

### Phase 2: Design (closed)

- Module layout: `app.py` (UI only), `dashboard/` (pure logic), `tests/`, `scripts/`, `.github/workflows/`.
- Config file structure and the decisions D-001 to D-012.
- Test strategy outline: unit, scenario, edge-case, and scale tests.

### Phase 3: Build (in progress)

- Repository skeleton: layout, `config.yaml`, first config test, `.gitignore`.
- CI pipeline: GitHub Actions runs `uv sync --locked`, `ruff check`, and `pytest` on every push.
- Loader: header check before reading, and a named error for missing columns. Three tests.
- Labels parser: handles the quoted, space-separated Kaggle format and empty cells. Five tests.
- Sprint parser: diffs full-list Sprint events into added and removed sets. Six tests.
- Story points rule (D-019): blank points default to 1 and are flagged, zero is kept as an estimate, and a sprint over the defaulted-share limit or with no points shows Not assessed with throughput. Nine tests, including the config check.
- Events table: replays label changes to rebuild each issue's labels on any date. Ten tests.
- Sprint membership on any date: replays full-list Sprint events so each issue's sprints are known on any date. Nine tests.
- Commitment at sprint start (D-020): items in a sprint at the end of its start day, with the team read from labels at that moment. Conflicts and missing teams are flagged. Ten tests.
- Field state on any date (D-021): one replay rule for status, story points, labels and sprints. Cleared points are blank, not zero. Seven tests.
- Working-day calendar (D-022): Monday to Friday, minus configured holidays, with inclusive counts from the start date. Weekend holidays do not reduce working days. Twelve tests.
- Team status rules (D-023): linear expected against committed points, Too early before the midpoint, At risk at 5%, Off track at 10%, Not assessed under the D-019 rules. Percentage alone decides (D-024). Twelve tests.
- Team snapshot (D-026): joins start-day membership and points with report-date status into item records, then runs the status rule. Unassigned blockers are shown as "Team Unassigned" (D-025). Thirteen tests.
- Blocked items with owners (D-027): items blocked on the report date, team from the label on that date (D-025), developer from the assignee, calendar days waiting from the latest block, longest first. Fifteen tests.
- Metrics (D-028 to D-030): throughput and velocity by completion date within the sprint, velocity blank when most completed items are unpointed, cycle time in calendar days with excluded counts, and a three-sprint rolling average. Thirteen tests.
- Config connection and synthetic scenarios (D-031): settings loaded and validated from config.yaml, holidays read from the committed 2026 CSV, and four teams plus one blocker with hand-worked expected results. Twelve tests.


### Changed

- Project location standardised per machine (D-016).
- Test discovery configured in `pyproject.toml` so `dashboard` imports correctly.

### Fixed

- Loader file missing from Git history: the working copy had the code but it was never committed. Recovered and committed (see the WIP commit history).