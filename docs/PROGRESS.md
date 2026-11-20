# Project progress

Updated at the end of each working session. Status values: Done, In progress, Not started, Blocked.

## Phase summary

| # | Phase | Status | Exit criteria | Notes |
|---|---|---|---|---|
| 1 | Requirements | Done | Requirements doc reviewed; backlog agreed | v0.4 closed, data access confirmed |
| 2 | Design | Done | Module layout, data model, and config agreed | Decisions D-001 to D-012 logged |
| 3 | Build | In progress | All must-have stories implemented with tests passing | See step tracker below |
| 4 | Test | Not started | Scenario, edge-case, and scale tests passing | Synthetic generator belongs here |
| 5 | CI/CD | In progress | Pipeline runs tests on every push, green on main | Basic test job done; add lint and coverage |
| 6 | Deploy | Not started | Public app running on Streamlit Community Cloud | Requires synthetic data only in the repo |
| 7 | Portfolio | In progress | README, CHANGELOG, and architecture note complete | CHANGELOG started |

## Phase 3: step tracker

| Step | Item | Status | Tests |
|---|---|---|---|
| 1 | Repository skeleton | Done | 1 |
| 2 | CI pipeline | Done | Green on skeleton |
| 3 | Loader and named missing-column errors | Done | 3 |
| 4 | Labels parser | Done (confirm CI) | 5 |
| 5 | Sprint parser (diff of sprint lists) | Not started | — |
| 6 | Events table (replay of changes) | Not started | — |
| 7 | Commitment at sprint start | Not started | — |
| 8 | Team lookup at sprint start | Not started | — |
| 9 | Metrics: throughput, velocity, cycle time | Not started | — |
| 10 | Status rules (midpoint, minimum size) | Not started | — |
| 11 | Blocked items with owners | Not started | — |
| 12 | Streamlit UI | Not started | — |

## Current test count

9 passing (1 config, 3 loader, 5 parsers).

## Next action

Confirm the latest push is green on GitHub Actions. Then write the sprint parser tests, starting with the diff rules in the Phase 3 plan.

## Open items

1. **Sprint table columns.** Proposed as `sprint_name`, `board`, `start_date`, `end_date`. Needs confirmation from the user, and from the Jira admin when the real export is requested.
2. **Admin request for real exports.** Changelog with status, Sprint, labels, and assignee, plus the sprint table. Status not yet confirmed.
3. **Holiday calendar.** Barcelona 2027 local holidays are unverified, pending the Ajuntament `.ics` file.
4. **Kaggle license.** Check before any public sharing of derived data.
5. **Second machine.** Confirm it's on the latest commit before the next session.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Admin cannot export changelog history | Core metrics cannot be built on real data | Synthetic data carries the project; raise with admin this week |
| Changelog format differs from Kaggle | Parsers fail on real data | Parsers tested on Kaggle and synthetic formats; loader fails clearly |
| Linear burn-down misleads on back-loaded teams | Wrong status on the report | Backtest thresholds on past sprints before relying on them |
| Work split across two machines | Uncommitted code lost or out of sync | Commit and pull before switching; `git status` check at start and end |

## Session log

| Date | Session outcome |
|---|---|
| Phase 1 | Requirements v0.1 to v0.4, key questions revised, thresholds agreed |
| Phase 2 | Module layout, data model, config, parser rules agreed |
| Phase 3 | Skeleton, CI green, loader pushed, labels parser written, 9 tests passing |