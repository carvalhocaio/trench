# Trench

NFL regular-season analytics built only from the data you record: win probabilities, projected points, the impact of injuries, season leaders and matchup previews written by Gemini, grounded in the numbers.

> Named after the battle in the trenches — and after a certain 2018 album.

Every week you record the schedule, the final scores, team and player stats and the injury report. Trench turns that into a statistical projection for each game, lets you record snapshots from Wednesday to Sunday and measures how well calibrated the model actually is as the season goes on.

## Features

- **Win probabilities and projected points** for every game, computed from the current season only.
- **Injury impact**: each reported absence shifts the projection, weighted by position and by the chance the player misses the game.
- **Season leaders**: passing touchdowns, yards per carry among qualified running backs and sacks.
- **Matchup previews** written by Gemini from a facts-only context, with a validator that rejects invented probabilities.
- **Prediction snapshots** recorded along the week, so you can see how a forecast evolved.
- **Calibration**: Brier score, log loss, favorite accuracy and a reliability table, both for a leakage-free backtest and for the snapshots recorded live.
- **Web interface** to follow the week, inspect a matchup and record everything above.

## How the model works

The model is deliberately simple, transparent and testable. The LLM never computes a number.

1. **Team ratings.** For each team, the average points scored and allowed in final games, shrunk towards the league average of the current season:

   ```text
   shrunk_avg = (team_points + k × league_avg) / (games_played + k)      k = 3
   ```

   Early in the season the prior dominates; by midseason the team's own results do. Offense and defense strengths are these averages divided by the league average.

2. **Projected points.**

   ```text
   projected(A) = league_avg × offense(A) × defense(B) ± home_field / 2 + absences
   ```

   The home field advantage (1.7 points) is split between both sides, so it widens the spread without inflating the total.

3. **Absences.** A starter's weight (QB 6.0 points, WR 1.0, CB 0.8, …) times the probability of missing the game (OUT 1.0, DOUBTFUL 0.9, QUESTIONABLE 0.25). Offensive and special teams absences lower the team's own projection; defensive absences raise the opponent's.

4. **Win probability.** The projected spread through a normal distribution of score margins (σ = 13.5 points).

5. **No leakage.** A game is always rated using only games that kicked off before it, which makes the backtest honest.

Every parameter lives in the analytics settings and can be overridden through environment variables, with no code changes.

## Architecture

```text
api / agent / cli  →  application  →  analytics  →  domain
                           ↓                          ↑
                   domain.repositories  ←  infrastructure
```

| Layer | Responsibility |
|---|---|
| `domain` | Entities and invariants (`Game`, `Score`, `Player`, `Absence`, …) and repository ports as `Protocol`s. |
| `analytics` | Pure functions: ratings, projection, absences, highlights and calibration. |
| `application` | Use cases orchestrating ports and analytics: schedule, roster, stats, injury report, predictions, previews and calibration. |
| `infrastructure` | SQLAlchemy models and repositories on Postgres, plus the Alembic migrations. |
| `agent` | PydanticAI agent that writes previews with Gemini, validated against the context. |
| `api` | FastAPI routes, schemas and the mapping of domain errors to HTTP. |
| `web/` | Next.js interface that reads through Server Components and writes through Server Actions. |

## Stack

- **Backend:** Python 3.14, FastAPI, SQLAlchemy 2 (async), Alembic, Postgres 18, PydanticAI with Gemini 3.8 Flash.
- **Web:** Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, types generated from the OpenAPI schema.
- **Tooling:** uv, pnpm, ruff, mypy strict, pytest, Vitest, pre-commit, GitHub Actions.

## Getting started

Requirements: [uv](https://docs.astral.sh/uv/), Docker, Node 22 and pnpm.

```bash
cp .env.example .env              # add GOOGLE_API_KEY to enable previews
cp web/.env.example web/.env.local

make sync                         # Python dependencies
make web-install                  # web dependencies
make db-up                        # Postgres 18 via Docker Compose
make migrate                      # database schema
make seed                         # the 32 NFL teams
make import-schedule SEASON=2026  # full season schedule and final scores, from ESPN
make dev                          # API on :8000 and web on :3000
```

The interactive API docs live at <http://localhost:8000/docs>.

## Weekly workflow

| When | What to record |
|---|---|
| After each game | Final score, team stats and player stats. |
| Wednesday | Injury report, then **Record prediction** for the week's games. |
| Saturday | Updated injury report and a new snapshot. |
| Sunday | Last snapshot before kickoff. |

The calibration page compares the snapshots recorded live with the actual results as the weeks go by.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | — | Database credentials, shared by Docker Compose and the app. |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `localhost`, `5432` | Database address. |
| `GOOGLE_API_KEY` | — | Gemini key. Only the preview route needs it; without it, previews answer 503. |
| `TRENCH_LLM_MODEL` | `google:gemini-3.8-flash` | Model used for previews. |
| `TRENCH_LLM_LANGUAGE` | `pt-BR` | Language of the previews. |
| `TRENCH_LLM_PREVIEW_CACHE_SIZE` | `256` | Previews cached in memory, keyed by their context. |
| `TRENCH_ANALYTICS_SHRINKAGE_GAMES` | `3` | Prior games of league average added to each team. |
| `TRENCH_ANALYTICS_HOME_FIELD_ADVANTAGE` | `1.7` | Home field advantage in points. |
| `TRENCH_ANALYTICS_SCORE_MARGIN_STDDEV` | `13.5` | Standard deviation of score margins. |
| `TRENCH_ANALYTICS_POSITION_WEIGHTS` | see `config.py` | JSON with the points lost per absent starter, for every position. |
| `TRENCH_ANALYTICS_ABSENCE_PROBABILITIES` | see `config.py` | JSON with the chance of missing the game, for every status. |
| `TRENCH_API_URL` (web) | `http://localhost:8000` | API address, used only on the server. |
| `TRENCH_TIMEZONE` (web) | `America/Cuiaba` | Time zone used to display and enter kickoffs. |

## API

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Health check, including the database. |
| `GET` `POST` | `/teams` | List or create teams. |
| `GET` | `/teams/{id}` · `/teams/{id}/players` | A team and its roster. |
| `GET` `POST` | `/games` | List by `season`, `week` and `team_id`, or schedule a game. |
| `GET` | `/games/{id}` | A game. |
| `PUT` | `/games/{id}/score` | Record or correct the final score. |
| `GET` | `/games/{id}/stats` | Team and player stats recorded for a game. |
| `PUT` | `/games/{id}/team-stats/{team_id}` | Record a team's stats. |
| `PUT` | `/games/{id}/player-stats/{player_id}` | Record a player's stats. |
| `GET` `PUT` `DELETE` | `/games/{id}/absences[/{player_id}]` | Injury report. |
| `POST` `GET` `PUT` | `/players` · `/players/{id}` | Register, fetch or update (and trade) a player. |
| `GET` `POST` | `/games/{id}/prediction` | Live projection, or record a snapshot. |
| `GET` | `/games/{id}/prediction/history` | Recorded snapshots. |
| `GET` | `/predictions?season&week` | Projections for a whole week. |
| `GET` | `/games/{id}/preview` | Projection and the Gemini preview. |
| `GET` | `/highlights?season` | Season leaders. |
| `GET` | `/calibration?season` | Backtest and live calibration, with optional model parameters. |

Domain errors map to consistent responses: 404 for unknown resources, 409 for conflicts or seasons without data yet, 422 for invalid input and 503 when the LLM is unavailable.

## Development

```bash
make help       # every available command
make ci         # lint, format check, mypy, pip-audit and tests
make web-types  # regenerate the web API types after changing the API
make migration m="describe the change"
```

- Integration tests run against a dedicated `<db>_test` database, created on demand, with each test rolled back.
- In-memory fakes follow the same contract suite as the SQL repositories, so use cases are tested without a database.
- Tests never call a real model: `ALLOW_MODEL_REQUESTS` is disabled, and the agent is exercised with PydanticAI's `FunctionModel`.
- The CI also regenerates the OpenAPI types and fails if the committed `schema.d.ts` is out of date.

## Project structure

```text
.
├── src/trench/
│   ├── domain/          entities, enums, reference data and repository ports
│   ├── analytics/       ratings, projection, absences, highlights, calibration
│   ├── application/     use cases
│   ├── infrastructure/  database, models and SQL repositories
│   ├── agent/           Gemini preview agent
│   ├── api/             FastAPI app, routes and schemas
│   ├── cli.py           `trench seed-teams`, `trench import-schedule` and `trench openapi`
│   └── config.py        settings
├── migrations/          Alembic revisions
├── tests/               unit, contract and API tests
├── web/                 Next.js interface
├── compose.yaml         Postgres for local development
└── Makefile
```

## Roadmap

- Playoffs, as a separate phase from the regular season.
- A conversational agent with tools, for open questions about the week.
- Opponent-adjusted ratings, if calibration shows they help.
- Per-player absence weights derived from season stats.

## Author

Built by [Caio Carvalho](https://github.com/carvalhocaio).
