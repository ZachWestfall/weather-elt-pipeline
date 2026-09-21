# Weather ELT Pipeline

A containerised ELT pipeline: weather observations are extracted from a REST API, loaded raw into Postgres, transformed into a dimensional model with dbt, and served to a Superset dashboard — orchestrated hourly by Airflow.

---

## The problem

I wanted to build a data pipeline properly rather than write three scripts and call it one. The distinction I cared about was **ELT versus ETL**: most tutorial pipelines transform data in flight and load the result, which means a bug in the transformation costs you the source data. If the API is rate-limited — and weatherstack's free tier is — you may not be able to re-fetch what you lost, and even if you can, a live weather API will not return the same values an hour later.

So the raw payload lands first and is never mutated in place. Every transformation reads from stored rows and writes new ones. Fixing a transformation bug means re-running dbt, not re-running extraction.

## Architecture

```
                    ┌──────────────── Airflow (hourly) ────────────────┐
                    │                                                   │
  weatherstack  ──▶ │  extract ──▶ load ──▶ dbt run ──▶ dbt test       │
   REST API         │     │          │         │            │           │
                    └─────┼──────────┼─────────┼────────────┼───────────┘
                          │          ▼         ▼            ▼
                          │   dev.raw_weather_data     assertions fail
                          │      (immutable)           the task, so a bad
                          │          │                 mart is never
                          │          ▼                 published
                          │   stg_weather (view)
                          │          │
                          │          ├──▶ dim_location  (table)
                          │          └──▶ fct_weather_observation (table)
                          │                     │
                          └─────────────────────┴──▶ Superset dashboard
```

**Stack:** Apache Airflow 3.2.1 · dbt-postgres 1.8.2 · PostgreSQL 14.22 · Apache Superset 4.0.2 · Docker Compose · Python (`requests`, `psycopg2`).

### The model

| Layer | Object | Materialisation | Purpose |
|---|---|---|---|
| Raw | `dev.raw_weather_data` | table | Untouched API payload, append-only |
| Staging | `stg_weather` | view | Type casting, trimming, null filtering. No business logic. |
| Mart | `dim_location` | table | One row per city, md5 surrogate key |
| Mart | `fct_weather_observation` | table | One row per reading; unit conversions and date grain |

Staging exists as a seam: the marts never read the raw table, so a change in the source payload shape is absorbed in exactly one model.

## What I built

- **The DAG's task boundaries follow the failure modes, not the code structure.** `extract` and `load` are separate tasks because network failure and database failure need different retry behaviour and because a failed load should not force a re-fetch — the payload is already in XCom. Retries use exponential backoff capped at 15 minutes, since hammering a rate-limited API on a fixed interval is how you get blocked.
- **`dbt test` is a distinct task downstream of `dbt run`.** This is the part I would previously have skipped. Running the tests as their own task means a failing assertion fails the DAG visibly instead of leaving a quietly wrong mart in place for a dashboard to read.
- **A range test that catches the bug that looks like valid data.** `temperature_c` is asserted between −90 and 60 °C. The failure this exists for is a unit-conversion error: Fahrenheit values loaded into a Celsius column are all perfectly plausible numbers, pass every not-null and uniqueness check, and are completely wrong. Physical bounds are the only assertion that catches it.
- **Referential integrity enforced in the mart**, via a `relationships` test from `fct_weather_observation.location_key` to `dim_location`.
- **Offline mode as a first-class path.** `WEATHER_USE_MOCK=true` runs the entire DAG against a bundled fixture, so the stack is demonstrable from a clean clone with no API key. The mock was already in the original extraction script; promoting it to a configuration flag made the whole pipeline reproducible.
- **Postgres moved to a named Docker volume.** It was previously bind-mounted to `./postgres/data` inside the project directory, which put 50 MB of live database state in the working tree. A named volume keeps container state out of the repository entirely.
- **Health-gated startup.** Airflow and Superset wait on a real `pg_isready` healthcheck rather than `depends_on` alone, which only waits for the container to start, not for Postgres to accept connections.

## What I learned

- **ELT versus ETL is a decision about what you can recover from, not a style preference.** I understood the acronyms before building this. What I did not appreciate until I had a transformation bug was that the ordering determines whether a mistake is a five-second re-run or unrecoverable data loss against a rate-limited source.
- **The tests that matter assert things the type system cannot.** Uniqueness and not-null checks catch broken plumbing. The range check catches a category of error where the plumbing works perfectly and the numbers are meaningless — and that is the failure that actually reaches a dashboard and gets believed.
- **Orchestration is mostly about failure.** The interesting parts of this DAG are retries, backoff, `max_active_runs=1` preventing overlapping runs from double-inserting, and gating on health rather than container start. The happy path was the quickest part to write.
- **Where I was wrong:** the original version had a working Airflow container in the compose file and an empty `dags/` directory. Standing up an orchestrator is not orchestration, and I had been describing it as though it were. That gap is the direct reason this repository exists in its current form.

## Why it mattered

Building this taught me to design for the failure path first — what happens on a partial load, a rate limit, an upstream schema change, a plausible-looking wrong number. Those are the same questions that decide whether a system's output can be relied on for a decision, which is the property I care about in the systems work I want to do.

## Running it

```bash
cp .env.example .env        # optional: add WEATHERSTACK_API_KEY for live data
docker compose up -d
```

| Service | URL | Notes |
|---|---|---|
| Airflow | <http://localhost:8000> | Credentials printed in the container logs on first start |
| Superset | <http://localhost:8088> | `admin` / value of `SUPERSET_ADMIN_PASSWORD` (default `admin`) |
| Postgres | `localhost:5432` | `db_user` / `db_password` / database `db` |

Then enable the `weather_elt` DAG in the Airflow UI and trigger a run. It runs hourly thereafter.

By default `WEATHER_USE_MOCK=true`, so it works with no API key. Set it to `false` and supply `WEATHERSTACK_API_KEY` in `.env` for live data.

Connect Superset to Postgres with:
```
postgresql://db_user:db_password@db:5432/db
```
and build charts against `marts.fct_weather_observation` joined to `marts.dim_location`.

### Running dbt directly

```bash
docker compose exec af bash -c "cd /opt/airflow/project/dbt/weather && dbt build --profiles-dir ."
```

## Status and verification

Honest account of what has been checked:

- ✅ DAG parses; `docker compose config` validates the full three-service stack.
- ✅ Extraction and loading logic are the original working scripts, with the API key moved to an environment variable.
- ⚠️ **The full stack has not yet been run end to end on this machine** — Docker Desktop was not running when this was assembled. Bringing it up and confirming the DAG completes green, the dbt tests pass, and the Superset dashboard renders is the outstanding verification step.
- ⚠️ **No Superset dashboard definition is committed yet.** The connection is documented; the exported dashboard JSON is not in the repository.

## Limitations

- **Single city per run.** The schema supports many, the DAG fetches one.
- **No incremental materialisation.** Marts are rebuilt in full each run, which is fine at this volume and would not be at scale.
- **`dim_location` is not a slowly-changing dimension.** A city's `utc_offset` changing would not be historised.
- **Secrets are plain environment variables.** Adequate locally; a real deployment wants a secret manager.
- **The previous `postgres/data` bind mount is superseded** by a named volume. Existing local database state in that directory is not picked up by the new configuration.

## License

MIT — see [LICENSE](LICENSE).
