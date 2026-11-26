# Project progress

Updated at the end of each working session.

## Phase summary

| # | Phase | Status | Notes |
|---|---|---|---|
| 1 | Requirements | Done | Requirements v0.4 closed |
| 2 | Design | Done | Decisions D-001 to D-012 logged |
| 3 | Build | In progress | Loader, labels parser, sprint parser done |
| 4 | Test | Not started | Scenario and scale tests; synthetic generator |
| 5 | CI/CD | In progress | Tests and ruff lint on every push |
| 6 | Deploy | Not started | Streamlit Community Cloud, synthetic data only |
| 7 | Portfolio | In progress | README, CHANGELOG, architecture note |

## Phase 3: step tracker

| Step | Item | Status | Tests |
|---|---|---|---|
| 1 | Repository skeleton | Done | 1 |
| 2 | CI pipeline | Done | Green |
| 3 | Loader and named missing-column errors | Done | 3 |
| 4 | Labels parser | Done | 5 |
| 5 | Sprint parser (diff of sprint lists) | Done | 6 |
| 5a | Story points default and Not assessed rule (D-019) | Done | 9 |
| 6 | Events table (replay of changes) | Not started | — |
| 7 | Commitment at sprint start | Not started | — |
| 8 | Team lookup at sprint start | Not started | — |
| 9 | Metrics: throughput, velocity, cycle time | Not started | — |
| 10 | Status rules (midpoint, minimum size) | Not started | — |
| 11 | Blocked items with owners | Not started | — |
| 12 | Streamlit UI | Not started | — |

## Current test count

24 passing (1 config, 3 loader, 5 parsers, 6 sprint, 8 story points, 1 config story points).

## Next action

Write the events table tests: replay label and sprint changes to rebuild each issue's state on any date.

## Open items

1. **Sprint table columns:** proposed as `sprint_id`, `sprint_name`, `board_id`, `state`, `start_date`, `end_date`. Awaiting your confirmation and the Jira admin's export.
2. **Admin request:** changelog (status, Sprint, labels, assignee) and sprint list, per board.
3. **Holiday calendar:** Barcelona 2027 local holidays unverified; use the Ajuntament `.ics` file.
4. **Sprint names with commas:** unresolved. The parser splits on comma-space.
5. **Kaggle license:** check before any public sharing of derived data.