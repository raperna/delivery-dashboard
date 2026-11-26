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
- At risk or Off track requires a shortfall of at least two average-sized committed items.
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

### Changed

- Project location standardised per machine (D-016).
- Test discovery configured in `pyproject.toml` so `dashboard` imports correctly.

### Fixed

- Loader file missing from Git history: the working copy had the code but it was never committed. Recovered and committed (see the WIP commit history).