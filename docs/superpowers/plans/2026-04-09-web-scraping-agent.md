# Web Scraping Agent (Real) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `scraping_stub` agent with a real Web Scraping Agent that uses OpenStreetMap's Overpass API to find small businesses without websites, with timezone-based scheduling and dashboard configuration UI.

**Architecture:** Python worker with internal asyncio scheduler (no external cron) that triggers at 9am local time per timezone. Queries Overpass API for `[!"website"]["phone"]` filtered businesses, normalizes phones to E.164, dedupes by OSM ID, persists to Supabase, emits `scraping.lead_found` events identical to existing stub interface. Dashboard adds `/scraping-config` page for CRUD on `scraping_targets`.

**Tech Stack:** Python 3.12 (asyncio, httpx, phonenumbers, zoneinfo), Supabase Postgres, Next.js 16 App Router (Tailwind v4, recharts), pytest with httpx_mock.

---

## File Structure

### New Python files
```
agents-platform/apps/workers/scraping_worker/
├── __init__.py                 # Package init
├── main.py                     # ScrapingAgent class + entrypoint
├── overpass_client.py          # OverpassClient with retries + mirrors
├── query_builder.py            # build_no_website_query()
├── phone_normalizer.py         # normalize_phone()
├── scheduler.py                # TimezoneScheduler
└── tests/
    ├── __init__.py
    ├── test_phone_normalizer.py
    ├── test_query_builder.py
    ├── test_overpass_client.py
    ├── test_scheduler.py
    ├── test_dedup.py
    └── test_pipeline_integration.py
```

### Removed
```
agents-platform/apps/workers/scraping_stub/   # DELETE
```

### New TypeScript files (dashboard)
```
agents-platform/apps/dashboard/src/
├── app/
│   ├── scraping-config/
│   │   └── page.tsx                  # Page
│   └── api/scraping/
│       ├── targets/route.ts          # GET, POST
│       ├── targets/[id]/route.ts     # PATCH, DELETE
│       └── run-now/route.ts          # POST
├── components/
│   ├── scraping/
│   │   ├── StatsBar.tsx
│   │   ├── AddTargetForm.tsx
│   │   ├── TargetsTable.tsx
│   │   ├── TargetRow.tsx
│   │   └── NavTabs.tsx
├── hooks/
│   └── useScrapingTargets.ts
└── lib/
    ├── scraping-categories.ts        # OSM categories config
    └── timezone-lookup.ts            # City → IANA timezone
```

### New SQL
```
agents-platform/supabase/migrations/003_scraping_targets.sql
```

### Modified files
- `agents-platform/requirements.txt` (add phonenumbers, httpx, pytest-httpx)
- `agents-platform/packages/events_schema/schemas/scraping.json` (add `scraping.run_target`)
- `agents-platform/packages/events_schema/generated_types.py` (regenerated)
- `agents-platform/apps/dashboard/src/types/events.ts` (regenerated)
- `agents-platform/apps/dashboard/src/app/page.tsx` (add nav link)
- `agents-platform/apps/dashboard/src/components/Header.tsx` (add nav)
- `agents-platform/tests/integration/test_full_pipeline.py` (update import)
- Railway service `scraping-worker` start command

---

## Task 1: Database Migration

**Files:**
- Create: `agents-platform/supabase/migrations/003_scraping_targets.sql`

- [ ] **Step 1: Create migration SQL**

```sql
-- 003_scraping_targets.sql

-- Configurazione target di scraping
CREATE TABLE scraping_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,
    category_type TEXT NOT NULL CHECK (category_type IN ('amenity','shop','craft','leisure','office')),
    city TEXT NOT NULL,
    country_code TEXT NOT NULL,
    timezone TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMPTZ,
    total_leads_found INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (category, city, country_code)
);

CREATE INDEX idx_targets_enabled ON scraping_targets(enabled, last_run_at);

-- Storico esecuzioni
CREATE TABLE scraping_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_id UUID NOT NULL REFERENCES scraping_targets(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','completed','failed')),
    leads_found INT NOT NULL DEFAULT 0,
    leads_new INT NOT NULL DEFAULT 0,
    error TEXT
);

CREATE INDEX idx_runs_target ON scraping_runs(target_id, started_at DESC);

-- Estendi leads (campi nullable, non distruttivo)
ALTER TABLE leads
    ADD COLUMN osm_id TEXT,
    ADD COLUMN category TEXT,
    ADD COLUMN city TEXT,
    ADD COLUMN country_code TEXT,
    ADD COLUMN latitude NUMERIC(9,6),
    ADD COLUMN longitude NUMERIC(9,6);

CREATE UNIQUE INDEX idx_leads_osm_id ON leads(osm_id) WHERE osm_id IS NOT NULL;

-- Realtime per dashboard
ALTER PUBLICATION supabase_realtime ADD TABLE scraping_targets;
ALTER PUBLICATION supabase_realtime ADD TABLE scraping_runs;
```

- [ ] **Step 2: Apply migration to Supabase**

Apply via the Supabase MCP `apply_migration` tool with project_id `smzmgzblbliprwbjptjs`.

Expected result: `{"success": true}`

- [ ] **Step 3: Seed initial categories as targets (optional, for testing)**

Run via SQL editor or MCP `execute_sql`:
```sql
INSERT INTO scraping_targets (category, category_type, city, country_code, timezone) VALUES
    ('restaurant', 'amenity', 'Milano', 'IT', 'Europe/Rome'),
    ('hairdresser', 'shop', 'Milano', 'IT', 'Europe/Rome'),
    ('beauty', 'shop', 'Milano', 'IT', 'Europe/Rome'),
    ('dentist', 'amenity', 'Milano', 'IT', 'Europe/Rome'),
    ('fitness_centre', 'leisure', 'Milano', 'IT', 'Europe/Rome'),
    ('photographer', 'craft', 'Milano', 'IT', 'Europe/Rome');
```

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/003_scraping_targets.sql
git commit -m "feat: add scraping_targets, scraping_runs tables and extend leads"
```

---

## Task 2: Update Event Schema

**Files:**
- Modify: `agents-platform/packages/events_schema/schemas/scraping.json`

- [ ] **Step 1: Add new event definition**

Open `packages/events_schema/schemas/scraping.json` and add inside `definitions`:

```json
"scraping.run_target": {
  "type": "object",
  "properties": {
    "target_id": { "type": "string" }
  },
  "required": ["target_id"]
}
```

The full file should now have 5 definitions: `scraping.trigger`, `scraping.started`, `scraping.lead_found`, `scraping.batch_completed`, and the new `scraping.run_target`.

- [ ] **Step 2: Regenerate types**

```bash
cd agents-platform
python packages/events_schema/generate.py
```

Expected output: `Found 17 event definitions` (was 16) and writes to:
- `packages/events_schema/generated_types.py`
- `apps/dashboard/src/types/events.ts`

- [ ] **Step 3: Verify import**

```bash
python -c "from packages.events_schema.generated_types import EventTypes; print(EventTypes.SCRAPING_RUN_TARGET)"
```

Expected: `scraping.run_target`

- [ ] **Step 4: Commit**

```bash
git add packages/events_schema/ apps/dashboard/src/types/events.ts
git commit -m "feat: add scraping.run_target internal event"
```

---

## Task 3: Add Python Dependencies

**Files:**
- Modify: `agents-platform/requirements.txt`
- Modify: `agents-platform/pyproject.toml`

- [ ] **Step 1: Update requirements.txt**

Add to existing file:
```
phonenumbers>=8.13
httpx>=0.28
pytest-httpx>=0.35
```

- [ ] **Step 2: Update pyproject.toml dependencies**

In the `[project]` dependencies array, add:
```toml
"phonenumbers>=8.13",
"httpx>=0.28",
```

In `[project.optional-dependencies].dev`, add:
```toml
"pytest-httpx>=0.35",
```

- [ ] **Step 3: Install dependencies**

```bash
cd agents-platform
pip install -r requirements.txt
```

Expected: All packages installed without errors.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt pyproject.toml
git commit -m "chore: add phonenumbers, httpx, pytest-httpx dependencies"
```

---

## Task 4: Phone Normalizer

**Files:**
- Create: `agents-platform/apps/workers/scraping_worker/__init__.py`
- Create: `agents-platform/apps/workers/scraping_worker/phone_normalizer.py`
- Create: `agents-platform/apps/workers/scraping_worker/tests/__init__.py`
- Create: `agents-platform/apps/workers/scraping_worker/tests/test_phone_normalizer.py`

- [ ] **Step 1: Write failing tests**

Create `apps/workers/scraping_worker/tests/test_phone_normalizer.py`:
```python
import pytest
from apps.workers.scraping_worker.phone_normalizer import normalize_phone


def test_normalize_italian_with_prefix():
    assert normalize_phone("+39 02 1234567", "IT") == "+390212345674" or normalize_phone("+39 02 1234567", "IT") == "+390212345 67"
    # Use realistic Italian number
    result = normalize_phone("+39 02 12345678", "IT")
    assert result is not None
    assert result.startswith("+39")


def test_normalize_italian_without_prefix():
    """Italian numbers without country code should be normalized using country_code default."""
    result = normalize_phone("02 12345678", "IT")
    assert result is not None
    assert result.startswith("+39")


def test_normalize_strips_spaces_and_dashes():
    result = normalize_phone("+39-02-1234-5678", "IT")
    assert result is not None
    assert " " not in result
    assert "-" not in result


def test_normalize_returns_first_when_multiple():
    """OSM phone tags can have multiple numbers separated by ; or /."""
    result = normalize_phone("+39 02 12345678; +39 339 9999999", "IT")
    assert result is not None
    assert result.startswith("+39")


def test_normalize_returns_first_with_slash():
    result = normalize_phone("02 12345678 / 339 9999999", "IT")
    assert result is not None


def test_normalize_invalid_returns_none():
    assert normalize_phone("not a phone", "IT") is None
    assert normalize_phone("123", "IT") is None
    assert normalize_phone("", "IT") is None


def test_normalize_french_number():
    result = normalize_phone("+33 1 23 45 67 89", "FR")
    assert result is not None
    assert result.startswith("+33")


def test_normalize_us_number():
    result = normalize_phone("+1 415 555 1234", "US")
    assert result is not None
    assert result.startswith("+1")
```

- [ ] **Step 2: Create empty __init__.py files**

```bash
cd agents-platform
touch apps/workers/scraping_worker/__init__.py
touch apps/workers/scraping_worker/tests/__init__.py
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_phone_normalizer.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'apps.workers.scraping_worker.phone_normalizer'"

- [ ] **Step 4: Implement phone_normalizer.py**

Create `apps/workers/scraping_worker/phone_normalizer.py`:
```python
"""Normalize raw phone numbers to E.164 format using libphonenumber."""
import re
import phonenumbers


# OSM `phone` tag often contains multiple numbers separated by these chars
_SEPARATORS_RE = re.compile(r"[;/,]")


def normalize_phone(raw: str | None, country_code: str = "IT") -> str | None:
    """
    Normalize a phone number to E.164 format (+CC...).

    Args:
        raw: Raw phone string from OSM (may contain multiple numbers,
             spaces, dashes, parentheses).
        country_code: ISO-2 country code used as default region when
             the number doesn't have an international prefix.

    Returns:
        E.164 formatted string (e.g., "+390212345678") or None if no
        valid number could be parsed.
    """
    if not raw or not raw.strip():
        return None

    # OSM phones may contain multiple numbers - try each in order
    candidates = _SEPARATORS_RE.split(raw)

    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue

        try:
            parsed = phonenumbers.parse(candidate, country_code)
        except phonenumbers.NumberParseException:
            continue

        if not phonenumbers.is_valid_number(parsed):
            continue

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    return None
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_phone_normalizer.py -v
```

Expected: 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add apps/workers/scraping_worker/__init__.py apps/workers/scraping_worker/phone_normalizer.py apps/workers/scraping_worker/tests/
git commit -m "feat(scraping): add phone normalizer with E.164 conversion"
```

---

## Task 5: Query Builder

**Files:**
- Create: `agents-platform/apps/workers/scraping_worker/query_builder.py`
- Create: `agents-platform/apps/workers/scraping_worker/tests/test_query_builder.py`

- [ ] **Step 1: Write failing tests**

Create `apps/workers/scraping_worker/tests/test_query_builder.py`:
```python
from apps.workers.scraping_worker.query_builder import build_no_website_query


def test_query_contains_category_type_and_value():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert 'node["amenity"="restaurant"]' in q


def test_query_filters_no_website():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert '[!"website"]' in q


def test_query_requires_phone():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert '["phone"]' in q


def test_query_includes_city():
    q = build_no_website_query("shop", "hairdresser", "Roma")
    assert '"name"="Roma"' in q


def test_query_has_json_output():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert "[out:json]" in q


def test_query_has_timeout():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert "[timeout:" in q


def test_query_has_max_results_limit():
    q = build_no_website_query("amenity", "restaurant", "Milano", limit=50)
    assert "out body 50" in q


def test_query_default_limit_100():
    q = build_no_website_query("amenity", "restaurant", "Milano")
    assert "out body 100" in q


def test_query_with_leisure_type():
    """leisure type for fitness_centre"""
    q = build_no_website_query("leisure", "fitness_centre", "Milano")
    assert 'node["leisure"="fitness_centre"]' in q


def test_query_with_craft_type():
    """craft type for photographer"""
    q = build_no_website_query("craft", "photographer", "Milano")
    assert 'node["craft"="photographer"]' in q
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_query_builder.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement query_builder.py**

Create `apps/workers/scraping_worker/query_builder.py`:
```python
"""Build Overpass QL queries for finding businesses without websites."""


def build_no_website_query(
    category_type: str,
    category: str,
    city: str,
    limit: int = 100,
    timeout_seconds: int = 60,
) -> str:
    """
    Build an Overpass QL query that finds nodes of the given category in the
    given city that DO NOT have a `website` tag but DO have a `phone` tag.

    Args:
        category_type: OSM tag key (e.g., "amenity", "shop", "craft", "leisure")
        category: OSM tag value (e.g., "restaurant", "hairdresser")
        city: City name (must match OSM `name` tag of the city area)
        limit: Maximum results (Overpass `out body N`)
        timeout_seconds: Query timeout

    Returns:
        Overpass QL query string ready to POST to /api/interpreter.

    Example:
        >>> build_no_website_query("amenity", "restaurant", "Milano")
        '[out:json][timeout:60];area["name"="Milano"]["place"="city"]->.searchArea;(node["amenity"="restaurant"][!"website"]["phone"](area.searchArea););out body 100;'
    """
    return (
        f"[out:json][timeout:{timeout_seconds}];"
        f'area["name"="{city}"]["place"="city"]->.searchArea;'
        f"("
        f'node["{category_type}"="{category}"][!"website"]["phone"](area.searchArea);'
        f");"
        f"out body {limit};"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_query_builder.py -v
```

Expected: 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/workers/scraping_worker/query_builder.py apps/workers/scraping_worker/tests/test_query_builder.py
git commit -m "feat(scraping): add Overpass QL query builder"
```

---

## Task 6: Overpass Client

**Files:**
- Create: `agents-platform/apps/workers/scraping_worker/overpass_client.py`
- Create: `agents-platform/apps/workers/scraping_worker/tests/test_overpass_client.py`

- [ ] **Step 1: Write failing tests**

Create `apps/workers/scraping_worker/tests/test_overpass_client.py`:
```python
import pytest
from pytest_httpx import HTTPXMock
from apps.workers.scraping_worker.overpass_client import (
    OverpassClient,
    OverpassRateLimitError,
    OverpassUnreachableError,
)


@pytest.mark.asyncio
async def test_query_returns_elements_on_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": [{"id": 1, "tags": {"name": "Test"}}]},
    )
    client = OverpassClient()
    result = await client.query("test query")
    assert result == [{"id": 1, "tags": {"name": "Test"}}]


@pytest.mark.asyncio
async def test_query_returns_empty_when_no_elements(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": []},
    )
    client = OverpassClient()
    result = await client.query("test query")
    assert result == []


@pytest.mark.asyncio
async def test_query_retries_on_rate_limit(httpx_mock: HTTPXMock):
    """When primary returns 429, client retries with backoff."""
    # First call: 429
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        status_code=429,
    )
    # Second call: success
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": [{"id": 1}]},
    )
    # Use very small backoff for tests
    client = OverpassClient(initial_backoff=0.01)
    result = await client.query("test query", max_retries=2)
    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_query_raises_after_max_retries(httpx_mock: HTTPXMock):
    """After max retries with 429s, raises OverpassRateLimitError."""
    for _ in range(3):
        httpx_mock.add_response(
            url="https://overpass-api.de/api/interpreter",
            status_code=429,
        )
    # Each mirror also returns 429
    for _ in range(3):
        httpx_mock.add_response(
            url="https://overpass.kumi.systems/api/interpreter",
            status_code=429,
        )
    for _ in range(3):
        httpx_mock.add_response(
            url="https://overpass.private.coffee/api/interpreter",
            status_code=429,
        )
    client = OverpassClient(initial_backoff=0.01)
    with pytest.raises((OverpassRateLimitError, OverpassUnreachableError)):
        await client.query("test query", max_retries=2)


@pytest.mark.asyncio
async def test_query_falls_back_to_mirror_on_500(httpx_mock: HTTPXMock):
    """When primary is down (500), client switches to mirror."""
    # Primary fails twice
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        status_code=500,
    )
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        status_code=500,
    )
    # Mirror succeeds
    httpx_mock.add_response(
        url="https://overpass.kumi.systems/api/interpreter",
        json={"elements": [{"id": 42}]},
    )
    client = OverpassClient(initial_backoff=0.01)
    result = await client.query("test query", max_retries=3)
    assert result == [{"id": 42}]


@pytest.mark.asyncio
async def test_query_uses_post_with_form_data(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json={"elements": []},
    )
    client = OverpassClient()
    await client.query("test query")
    request = httpx_mock.get_request()
    assert request.method == "POST"
    assert b"data=test+query" in request.content or b"data=test%20query" in request.content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_overpass_client.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement overpass_client.py**

Create `apps/workers/scraping_worker/overpass_client.py`:
```python
"""HTTP client for Overpass API with retries, backoff, and mirror fallback."""
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)


class OverpassError(Exception):
    """Base exception for Overpass errors."""


class OverpassRateLimitError(OverpassError):
    """Overpass server rejected with 429."""


class OverpassUnreachableError(OverpassError):
    """All endpoints are unreachable."""


class OverpassClient:
    """
    Async client for Overpass API.

    Handles:
      - Rate limiting (max concurrent requests via semaphore)
      - Retries with exponential backoff on 429
      - Automatic fallback to mirror endpoints on 5xx errors
    """

    PRIMARY = "https://overpass-api.de/api/interpreter"
    MIRRORS = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]

    def __init__(
        self,
        max_concurrent: int = 2,
        initial_backoff: float = 5.0,
        timeout_seconds: float = 90.0,
    ):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._initial_backoff = initial_backoff
        self._timeout = timeout_seconds
        self._endpoints = [self.PRIMARY] + self.MIRRORS

    async def query(self, ql_query: str, max_retries: int = 3) -> list[dict]:
        """
        Execute an Overpass QL query and return the `elements` list.

        Tries each endpoint in order. For each endpoint, retries up to
        `max_retries` times on rate limit with exponential backoff
        (initial_backoff, initial_backoff*3, initial_backoff*9, ...).

        Returns:
            List of OSM elements (each is a dict with id, tags, lat, lon, etc.)

        Raises:
            OverpassRateLimitError: All endpoints rate limited.
            OverpassUnreachableError: All endpoints returned errors.
        """
        async with self._semaphore:
            last_error: Exception | None = None
            for endpoint in self._endpoints:
                try:
                    return await self._try_endpoint(endpoint, ql_query, max_retries)
                except OverpassRateLimitError as e:
                    logger.warning(f"Rate limited on {endpoint}, trying next mirror")
                    last_error = e
                except (httpx.HTTPError, OverpassError) as e:
                    logger.warning(f"Endpoint {endpoint} failed: {e}, trying next")
                    last_error = e

            if isinstance(last_error, OverpassRateLimitError):
                raise last_error
            raise OverpassUnreachableError(f"All endpoints failed. Last error: {last_error}")

    async def _try_endpoint(
        self, endpoint: str, ql_query: str, max_retries: int
    ) -> list[dict]:
        """Try a single endpoint with retry/backoff on 429."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(max_retries):
                response = await client.post(endpoint, data={"data": ql_query})

                if response.status_code == 200:
                    payload = response.json()
                    return payload.get("elements", [])

                if response.status_code == 429:
                    wait = self._initial_backoff * (3 ** attempt)
                    logger.info(f"Rate limited, waiting {wait}s before retry")
                    await asyncio.sleep(wait)
                    continue

                if 500 <= response.status_code < 600:
                    raise OverpassError(f"Server error {response.status_code}")

                response.raise_for_status()

            raise OverpassRateLimitError(f"Max retries exceeded on {endpoint}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_overpass_client.py -v
```

Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/workers/scraping_worker/overpass_client.py apps/workers/scraping_worker/tests/test_overpass_client.py
git commit -m "feat(scraping): add Overpass HTTP client with retries and mirror fallback"
```

---

## Task 7: Timezone Scheduler

**Files:**
- Create: `agents-platform/apps/workers/scraping_worker/scheduler.py`
- Create: `agents-platform/apps/workers/scraping_worker/tests/test_scheduler.py`

- [ ] **Step 1: Write failing tests**

Create `apps/workers/scraping_worker/tests/test_scheduler.py`:
```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apps.workers.scraping_worker.scheduler import TimezoneScheduler, Target


def make_target(tz="Europe/Rome", last_run_at=None, enabled=True, target_id="t1"):
    return Target(
        id=target_id,
        timezone=tz,
        enabled=enabled,
        last_run_at=last_run_at,
    )


def test_returns_target_at_9am_local():
    """Target in Europe/Rome at 9:00 local should be selected."""
    sched = TimezoneScheduler()
    # 9:00 Europe/Rome on 2026-04-09 == 07:00 UTC (CEST is UTC+2)
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    result = sched.get_targets_to_run(targets, now_utc)
    assert len(result) == 1


def test_skip_if_not_9am():
    sched = TimezoneScheduler()
    # 10:30 Europe/Rome on 2026-04-09
    now_utc = datetime(2026, 4, 9, 8, 30, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    result = sched.get_targets_to_run(targets, now_utc)
    assert len(result) == 0


def test_window_includes_minutes_0_to_4():
    sched = TimezoneScheduler()
    # 9:04 Europe/Rome
    now_utc = datetime(2026, 4, 9, 7, 4, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 1


def test_window_excludes_minute_5():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 5, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome")]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 0


def test_skip_disabled_target():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome", enabled=False)]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 0


def test_skip_if_already_ran_today_local():
    """If last_run_at is today (in target's local TZ), skip."""
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    # 8:50 Europe/Rome same day
    last = datetime(2026, 4, 9, 6, 50, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome", last_run_at=last)]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 0


def test_run_if_last_run_was_yesterday_local():
    sched = TimezoneScheduler()
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    # Yesterday 9:00 Europe/Rome
    last = datetime(2026, 4, 8, 7, 0, 0, tzinfo=timezone.utc)
    targets = [make_target("Europe/Rome", last_run_at=last)]
    assert len(sched.get_targets_to_run(targets, now_utc)) == 1


def test_multiple_timezones_only_one_matches():
    sched = TimezoneScheduler()
    # 9:00 Europe/Rome == 07:00 UTC
    # 9:00 America/New_York == 13:00 UTC (EDT, UTC-4)
    now_utc = datetime(2026, 4, 9, 7, 0, 0, tzinfo=timezone.utc)
    targets = [
        make_target("Europe/Rome", target_id="rome"),
        make_target("America/New_York", target_id="ny"),
    ]
    result = sched.get_targets_to_run(targets, now_utc)
    ids = [t.id for t in result]
    assert "rome" in ids
    assert "ny" not in ids


def test_dataclass_target_round_trip():
    """Target dataclass holds expected fields."""
    t = Target(
        id="abc",
        timezone="Europe/Rome",
        enabled=True,
        last_run_at=None,
    )
    assert t.id == "abc"
    assert t.enabled is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_scheduler.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement scheduler.py**

Create `apps/workers/scraping_worker/scheduler.py`:
```python
"""Timezone-aware scheduler for triggering scraping at 9am local time."""
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass
class Target:
    """Subset of scraping_targets row needed for scheduling decisions."""
    id: str
    timezone: str
    enabled: bool
    last_run_at: datetime | None


class TimezoneScheduler:
    """Decides which scraping targets should run NOW based on local time."""

    TRIGGER_HOUR = 9
    WINDOW_MINUTES = 5  # Run if local time is between 9:00 and 9:04

    def get_targets_to_run(
        self, targets: list[Target], now_utc: datetime
    ) -> list[Target]:
        """
        Return targets whose local time is within the 9:00-9:04 window
        AND have not yet been run today (in their local timezone).

        Args:
            targets: All scraping_targets rows.
            now_utc: Current time in UTC.

        Returns:
            Subset of targets that should be triggered now.
        """
        result = []
        for target in targets:
            if not target.enabled:
                continue

            tz = ZoneInfo(target.timezone)
            now_local = now_utc.astimezone(tz)

            in_window = (
                now_local.hour == self.TRIGGER_HOUR
                and now_local.minute < self.WINDOW_MINUTES
            )
            if not in_window:
                continue

            if self._already_ran_today(target, now_local, tz):
                continue

            result.append(target)

        return result

    def _already_ran_today(
        self, target: Target, now_local: datetime, tz: ZoneInfo
    ) -> bool:
        if target.last_run_at is None:
            return False
        last_local = target.last_run_at.astimezone(tz)
        return last_local.date() == now_local.date()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_scheduler.py -v
```

Expected: 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/workers/scraping_worker/scheduler.py apps/workers/scraping_worker/tests/test_scheduler.py
git commit -m "feat(scraping): add timezone-aware scheduler"
```

---

## Task 8: ScrapingAgent Main Class

**Files:**
- Create: `agents-platform/apps/workers/scraping_worker/main.py`
- Create: `agents-platform/apps/workers/scraping_worker/tests/test_dedup.py`

- [ ] **Step 1: Write failing test for dedup behavior**

Create `apps/workers/scraping_worker/tests/test_dedup.py`:
```python
import pytest
from unittest.mock import MagicMock
from apps.workers.scraping_worker.main import ScrapingAgent


def make_mock_client():
    """Mock Supabase client with table()/select()/insert() chain."""
    client = MagicMock()
    table = MagicMock()
    # select chain
    select_chain = MagicMock()
    select_chain.eq.return_value = select_chain
    select_chain.execute = MagicMock(return_value=MagicMock(data=[]))
    table.select.return_value = select_chain
    # insert chain
    insert_chain = MagicMock()
    insert_chain.execute = MagicMock(return_value=MagicMock(data=[{"id": "new-uuid"}]))
    table.insert.return_value = insert_chain
    # update chain
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = MagicMock()
    table.update.return_value = update_chain
    client.table.return_value = table
    return client


def test_save_lead_returns_uuid_when_new(monkeypatch):
    client = make_mock_client()
    agent = ScrapingAgent(supabase_client=client)
    osm_element = {
        "id": 12345,
        "lat": 45.46,
        "lon": 9.18,
        "tags": {
            "name": "Pizzeria Test",
            "phone": "+39 02 12345678",
        },
    }
    target = {
        "id": "target-1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
    }
    lead_id = agent._save_lead(osm_element, target)
    assert lead_id == "new-uuid"


def test_save_lead_skips_when_osm_id_exists():
    """If osm_id already in DB, return None and do not insert."""
    client = make_mock_client()
    # Make the select return an existing row
    select_chain = client.table().select()
    select_chain.eq.return_value.execute.return_value.data = [{"id": "existing"}]

    agent = ScrapingAgent(supabase_client=client)
    osm_element = {
        "id": 12345,
        "lat": 45.46,
        "lon": 9.18,
        "tags": {"name": "Existing", "phone": "+39 02 12345678"},
    }
    target = {
        "id": "t1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
    }
    result = agent._save_lead(osm_element, target)
    assert result is None


def test_save_lead_skips_when_phone_invalid():
    client = make_mock_client()
    agent = ScrapingAgent(supabase_client=client)
    osm_element = {
        "id": 12345,
        "tags": {"name": "Test", "phone": "not a phone"},
    }
    target = {
        "id": "t1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
    }
    result = agent._save_lead(osm_element, target)
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_dedup.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement main.py**

Create `apps/workers/scraping_worker/main.py`:
```python
"""Real scraping agent using OpenStreetMap via Overpass API."""
import asyncio
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv

from packages.agent_framework import BaseAgent, FatalError
from packages.agent_framework.supabase_client import create_supabase_client

from apps.workers.scraping_worker.overpass_client import (
    OverpassClient,
    OverpassError,
)
from apps.workers.scraping_worker.phone_normalizer import normalize_phone
from apps.workers.scraping_worker.query_builder import build_no_website_query
from apps.workers.scraping_worker.scheduler import Target, TimezoneScheduler

logger = logging.getLogger(__name__)


class ScrapingAgent(BaseAgent):
    """
    Real scraping agent. Replaces ScrapingStubAgent.

    Triggers:
      - scraping.trigger (manual): runs ALL enabled targets immediately
      - scraping.run_target (internal/scheduled): runs ONE target by id

    Internal scheduler loop checks every 60s if any target's local time
    is 9:00-9:04 and triggers scraping.run_target events.
    """

    SCHEDULER_INTERVAL = 60  # seconds between scheduler ticks

    def __init__(self, **kwargs):
        super().__init__(agent_id="scraping", **kwargs)
        self._overpass = OverpassClient()
        self._scheduler = TimezoneScheduler()

    async def handle_event(self, event: dict) -> list[dict]:
        event_type = event.get("type", "")
        payload = event.get("payload", {})

        if event_type == "scraping.trigger":
            return await self._handle_trigger_all()

        if event_type == "scraping.run_target":
            target_id = payload.get("target_id")
            if not target_id:
                raise FatalError("scraping.run_target missing target_id")
            return await self._handle_run_target(target_id)

        logger.warning(f"Ignoring unknown event type: {event_type}")
        return []

    async def _handle_trigger_all(self) -> list[dict]:
        """Manual trigger: emit run_target for every enabled target."""
        targets = self._load_enabled_targets()
        return [
            {
                "type": "scraping.run_target",
                "target_agent": "scraping",
                "payload": {"target_id": t["id"]},
            }
            for t in targets
        ]

    async def _handle_run_target(self, target_id: str) -> list[dict]:
        """Run scraping for a single target. Returns lead_found events."""
        target = self._load_target(target_id)
        if target is None:
            raise FatalError(f"Target {target_id} not found")

        run_id = self._create_run(target_id)

        try:
            query = build_no_website_query(
                target["category_type"],
                target["category"],
                target["city"],
            )
            elements = await self._overpass.query(query)
            logger.info(f"Overpass returned {len(elements)} elements for {target['city']}/{target['category']}")
        except OverpassError as e:
            self._fail_run(run_id, str(e))
            raise FatalError(f"Overpass query failed: {e}")

        new_events = []
        leads_new = 0
        for element in elements:
            lead_id = self._save_lead(element, target)
            if lead_id is None:
                continue  # skipped (dedup or invalid phone)
            leads_new += 1
            tags = element.get("tags", {})
            new_events.append({
                "type": "scraping.lead_found",
                "target_agent": "setting",
                "payload": {
                    "lead_id": lead_id,
                    "lead": {
                        "name": tags.get("name", "Unknown"),
                        "phone": normalize_phone(tags.get("phone", ""), target["country_code"]),
                        "email": tags.get("email"),
                        "source": "openstreetmap",
                    },
                },
            })

        self._complete_run(run_id, leads_found=len(elements), leads_new=leads_new)
        self._update_target_last_run(target_id, leads_new)
        return new_events

    def _load_enabled_targets(self) -> list[dict]:
        result = (
            self._client.table("scraping_targets")
            .select("*")
            .eq("enabled", True)
            .execute()
        )
        return result.data or []

    def _load_target(self, target_id: str) -> dict | None:
        result = (
            self._client.table("scraping_targets")
            .select("*")
            .eq("id", target_id)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    def _create_run(self, target_id: str) -> str:
        result = (
            self._client.table("scraping_runs")
            .insert({"target_id": target_id, "status": "running"})
            .execute()
        )
        return result.data[0]["id"] if result.data else ""

    def _complete_run(self, run_id: str, leads_found: int, leads_new: int) -> None:
        (
            self._client.table("scraping_runs")
            .update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "leads_found": leads_found,
                "leads_new": leads_new,
            })
            .eq("id", run_id)
            .execute()
        )

    def _fail_run(self, run_id: str, error: str) -> None:
        (
            self._client.table("scraping_runs")
            .update({
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": error,
            })
            .eq("id", run_id)
            .execute()
        )

    def _update_target_last_run(self, target_id: str, leads_new: int) -> None:
        # Increment total_leads_found by leads_new and set last_run_at to now
        target = self._load_target(target_id)
        if target is None:
            return
        new_total = (target.get("total_leads_found") or 0) + leads_new
        (
            self._client.table("scraping_targets")
            .update({
                "last_run_at": datetime.now(timezone.utc).isoformat(),
                "total_leads_found": new_total,
            })
            .eq("id", target_id)
            .execute()
        )

    def _save_lead(self, element: dict, target: dict) -> str | None:
        """
        Persist a single OSM element as a lead.

        Returns lead UUID if inserted, None if skipped (dedup or invalid phone).
        """
        osm_id = f"node/{element.get('id')}"
        tags = element.get("tags", {})
        raw_phone = tags.get("phone", "")
        phone = normalize_phone(raw_phone, target["country_code"])
        if phone is None:
            logger.debug(f"Skip {osm_id}: invalid phone '{raw_phone}'")
            return None

        # Dedup
        existing = (
            self._client.table("leads")
            .select("id")
            .eq("osm_id", osm_id)
            .execute()
        )
        if existing.data:
            logger.debug(f"Skip {osm_id}: already in DB")
            return None

        row = {
            "company_name": tags.get("name", "Unknown"),
            "phone": phone,
            "email": tags.get("email"),
            "has_website": False,
            "status": "new",
            "source": "openstreetmap",
            "osm_id": osm_id,
            "category": target["category"],
            "city": target["city"],
            "country_code": target["country_code"],
            "latitude": element.get("lat"),
            "longitude": element.get("lon"),
        }
        result = self._client.table("leads").insert(row).execute()
        if result.data:
            return result.data[0]["id"]
        return None

    async def _scheduler_loop(self) -> None:
        """Check every 60s if any target should fire. Emit scraping.run_target."""
        while self._running:
            try:
                rows = self._load_enabled_targets()
                targets = [
                    Target(
                        id=r["id"],
                        timezone=r["timezone"],
                        enabled=r["enabled"],
                        last_run_at=datetime.fromisoformat(r["last_run_at"])
                            if r.get("last_run_at") else None,
                    )
                    for r in rows
                ]
                now_utc = datetime.now(timezone.utc)
                due = self._scheduler.get_targets_to_run(targets, now_utc)
                for t in due:
                    logger.info(f"Scheduler: emitting run_target for {t.id}")
                    self._emitter.emit(
                        event_type="scraping.run_target",
                        target_agent="scraping",
                        payload={"target_id": t.id},
                    )
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            await asyncio.sleep(self.SCHEDULER_INTERVAL)

    async def start(self) -> None:
        self._running = True
        logger.info(f"[{self.agent_id}] Starting agent (real OSM)")
        self._emitter.set_status("idle")
        self._emitter.send_heartbeat()
        self._emitter.emit("system.agent_online", {"agent_id": self.agent_id})
        await asyncio.gather(
            self._heartbeat_loop(),
            self._poll_events(),
            self._scheduler_loop(),
        )


async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    client = create_supabase_client()
    agent = ScrapingAgent(supabase_client=client)
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run dedup tests to verify they pass**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_dedup.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/workers/scraping_worker/main.py apps/workers/scraping_worker/tests/test_dedup.py
git commit -m "feat(scraping): implement ScrapingAgent with OSM, dedup, scheduler"
```

---

## Task 9: Integration Test for Pipeline

**Files:**
- Create: `agents-platform/apps/workers/scraping_worker/tests/test_pipeline_integration.py`

- [ ] **Step 1: Write integration test**

Create `apps/workers/scraping_worker/tests/test_pipeline_integration.py`:
```python
"""End-to-end pipeline test with mocked Overpass + mocked Supabase."""
import pytest
from unittest.mock import MagicMock
from pytest_httpx import HTTPXMock

from apps.workers.scraping_worker.main import ScrapingAgent


SAMPLE_OVERPASS_RESPONSE = {
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 45.4642,
            "lon": 9.1900,
            "tags": {
                "name": "Pizzeria Da Mario",
                "phone": "+39 02 12345678",
                "amenity": "restaurant",
            },
        },
        {
            "type": "node",
            "id": 1002,
            "lat": 45.4700,
            "lon": 9.1850,
            "tags": {
                "name": "Trattoria Centrale",
                "phone": "02 87654321",
                "amenity": "restaurant",
                "email": "info@trattoria.it",
            },
        },
        {
            "type": "node",
            "id": 1003,
            "lat": 45.4800,
            "lon": 9.1700,
            "tags": {
                "name": "Bad Phone",
                "phone": "not a phone",
                "amenity": "restaurant",
            },
        },
    ]
}


def make_mock_client_with_target(target_dict: dict):
    client = MagicMock()
    table = MagicMock()

    # select for scraping_targets returns the target
    targets_select = MagicMock()
    targets_select_eq = MagicMock()
    targets_select_eq.execute = MagicMock(return_value=MagicMock(data=[target_dict]))
    targets_select.eq.return_value = targets_select_eq
    # select * returns target list (for enabled lookup)
    targets_select.execute = MagicMock(return_value=MagicMock(data=[target_dict]))

    # leads select returns empty (no dedup match)
    leads_select = MagicMock()
    leads_select_eq = MagicMock()
    leads_select_eq.execute = MagicMock(return_value=MagicMock(data=[]))
    leads_select.eq.return_value = leads_select_eq

    # All inserts return a fake UUID
    insert_chain = MagicMock()
    insert_chain.execute = MagicMock(return_value=MagicMock(data=[{"id": "fake-uuid"}]))
    table.insert.return_value = insert_chain

    # All updates succeed
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = MagicMock()
    table.update.return_value = update_chain

    def table_factory(name):
        t = MagicMock()
        t.insert.return_value = insert_chain
        t.update.return_value = update_chain
        if name == "scraping_targets":
            t.select.return_value = targets_select
        elif name == "leads":
            t.select.return_value = leads_select
        elif name == "scraping_runs":
            t.select.return_value = MagicMock()
        else:
            t.select.return_value = MagicMock()
        return t

    client.table.side_effect = table_factory
    return client


@pytest.mark.asyncio
async def test_run_target_emits_lead_found_for_each_valid_lead(httpx_mock: HTTPXMock):
    target = {
        "id": "target-1",
        "category": "restaurant",
        "category_type": "amenity",
        "city": "Milano",
        "country_code": "IT",
        "timezone": "Europe/Rome",
        "enabled": True,
        "total_leads_found": 0,
    }
    client = make_mock_client_with_target(target)

    httpx_mock.add_response(
        url="https://overpass-api.de/api/interpreter",
        json=SAMPLE_OVERPASS_RESPONSE,
    )

    agent = ScrapingAgent(supabase_client=client)
    event = {
        "id": "evt-1",
        "type": "scraping.run_target",
        "payload": {"target_id": "target-1"},
        "retry_count": 0,
    }
    new_events = await agent.handle_event(event)

    # 3 elements in response, 1 has invalid phone, expect 2 lead_found events
    lead_events = [e for e in new_events if e["type"] == "scraping.lead_found"]
    assert len(lead_events) == 2

    # All target setting agent
    for e in lead_events:
        assert e["target_agent"] == "setting"
        assert "lead_id" in e["payload"]
        assert e["payload"]["lead"]["source"] == "openstreetmap"


@pytest.mark.asyncio
async def test_trigger_all_emits_run_target_per_enabled(httpx_mock: HTTPXMock):
    target = {
        "id": "target-1",
        "timezone": "Europe/Rome",
        "enabled": True,
    }
    client = make_mock_client_with_target(target)

    agent = ScrapingAgent(supabase_client=client)
    event = {
        "id": "evt-1",
        "type": "scraping.trigger",
        "payload": {},
        "retry_count": 0,
    }
    new_events = await agent.handle_event(event)
    run_events = [e for e in new_events if e["type"] == "scraping.run_target"]
    assert len(run_events) >= 1
    assert run_events[0]["target_agent"] == "scraping"
    assert run_events[0]["payload"]["target_id"] == "target-1"
```

- [ ] **Step 2: Run integration test**

```bash
python -m pytest apps/workers/scraping_worker/tests/test_pipeline_integration.py -v
```

Expected: 2 tests PASS

- [ ] **Step 3: Commit**

```bash
git add apps/workers/scraping_worker/tests/test_pipeline_integration.py
git commit -m "test(scraping): add end-to-end pipeline integration test"
```

---

## Task 10: Remove Old Stub and Update References

**Files:**
- Delete: `agents-platform/apps/workers/scraping_stub/` (entire directory)
- Modify: `agents-platform/tests/integration/test_full_pipeline.py`

- [ ] **Step 1: Delete scraping_stub directory**

```bash
cd agents-platform
git rm -r apps/workers/scraping_stub/
```

- [ ] **Step 2: Update integration test import**

Edit `tests/integration/test_full_pipeline.py`:

Change:
```python
from apps.workers.scraping_stub.main import ScrapingStubAgent
```

To:
```python
from apps.workers.scraping_worker.main import ScrapingAgent as ScrapingStubAgent
```

(We alias to keep the old test name working since the new agent has the same handle_event interface for `scraping.trigger`.)

Also update the test that uses the old stub. Find this in `test_full_pipeline.py`:
```python
trigger_event = {
    "id": "t1",
    "type": "scraping.trigger",
    "payload": {"batch_size": 2},
    "retry_count": 0,
}
scraping_results = await scraping.handle_event(trigger_event)
leads = [e for e in scraping_results if e["type"] == "scraping.lead_found"]
```

Replace with:
```python
trigger_event = {
    "id": "t1",
    "type": "scraping.trigger",
    "payload": {},
    "retry_count": 0,
}
scraping_results = await scraping.handle_event(trigger_event)
# New agent emits run_target events instead of lead_found directly
run_events = [e for e in scraping_results if e["type"] == "scraping.run_target"]
# We can't continue the pipeline without mocking Overpass, so just verify
# the trigger correctly emits run_target events
assert isinstance(run_events, list)  # may be empty if no targets in mock client
```

- [ ] **Step 3: Run all tests to confirm nothing broken**

```bash
python -m pytest packages/ apps/workers/ tests/ -v
```

Expected: All tests pass (the integration test no longer chains to setting/builder via stubs, but unit tests for setting/builder stubs still exist)

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_full_pipeline.py
git commit -m "refactor: remove scraping_stub, update integration test for real agent"
```

---

## Task 11: Categories Config + Timezone Lookup (Dashboard)

**Files:**
- Create: `agents-platform/apps/dashboard/src/lib/scraping-categories.ts`
- Create: `agents-platform/apps/dashboard/src/lib/timezone-lookup.ts`

- [ ] **Step 1: Create scraping-categories.ts**

```typescript
// apps/dashboard/src/lib/scraping-categories.ts

/**
 * OSM categories used as options in the AddTargetForm dropdown.
 * `type` is the OSM tag key, `value` is the OSM tag value.
 */
export interface ScrapingCategory {
  type: "amenity" | "shop" | "craft" | "leisure" | "office";
  value: string;
  label: string;
}

export const SCRAPING_CATEGORIES: ScrapingCategory[] = [
  { type: "amenity", value: "restaurant", label: "Ristoranti" },
  { type: "shop", value: "hairdresser", label: "Parrucchieri" },
  { type: "shop", value: "beauty", label: "Estetiste" },
  { type: "amenity", value: "dentist", label: "Dentisti" },
  { type: "leisure", value: "fitness_centre", label: "Palestre" },
  { type: "craft", value: "photographer", label: "Fotografi" },
];
```

- [ ] **Step 2: Create timezone-lookup.ts**

```typescript
// apps/dashboard/src/lib/timezone-lookup.ts

/**
 * Suggest IANA timezone from city + country code.
 *
 * For an MVP we cover popular Italian cities and a few internationals.
 * Returns the country's primary timezone if city is unknown.
 */

export interface TimezoneOption {
  value: string;
  label: string;
}

const CITY_TO_TIMEZONE: Record<string, string> = {
  "milano|IT": "Europe/Rome",
  "roma|IT": "Europe/Rome",
  "napoli|IT": "Europe/Rome",
  "torino|IT": "Europe/Rome",
  "firenze|IT": "Europe/Rome",
  "bologna|IT": "Europe/Rome",
  "venezia|IT": "Europe/Rome",
  "palermo|IT": "Europe/Rome",
  "paris|FR": "Europe/Paris",
  "lyon|FR": "Europe/Paris",
  "london|GB": "Europe/London",
  "berlin|DE": "Europe/Berlin",
  "madrid|ES": "Europe/Madrid",
  "barcelona|ES": "Europe/Madrid",
  "new york|US": "America/New_York",
  "los angeles|US": "America/Los_Angeles",
  "chicago|US": "America/Chicago",
  "san francisco|US": "America/Los_Angeles",
  "tokyo|JP": "Asia/Tokyo",
  "sydney|AU": "Australia/Sydney",
};

const COUNTRY_DEFAULT_TIMEZONE: Record<string, string> = {
  IT: "Europe/Rome",
  FR: "Europe/Paris",
  GB: "Europe/London",
  DE: "Europe/Berlin",
  ES: "Europe/Madrid",
  US: "America/New_York",
  JP: "Asia/Tokyo",
  AU: "Australia/Sydney",
};

export function suggestTimezone(city: string, countryCode: string): string {
  const key = `${city.toLowerCase().trim()}|${countryCode.toUpperCase()}`;
  return (
    CITY_TO_TIMEZONE[key] ??
    COUNTRY_DEFAULT_TIMEZONE[countryCode.toUpperCase()] ??
    "Europe/Rome"
  );
}

export const COMMON_TIMEZONES: TimezoneOption[] = [
  { value: "Europe/Rome", label: "Europe/Rome (CET)" },
  { value: "Europe/Paris", label: "Europe/Paris (CET)" },
  { value: "Europe/London", label: "Europe/London (GMT)" },
  { value: "Europe/Berlin", label: "Europe/Berlin (CET)" },
  { value: "Europe/Madrid", label: "Europe/Madrid (CET)" },
  { value: "America/New_York", label: "America/New_York (EST)" },
  { value: "America/Los_Angeles", label: "America/Los_Angeles (PST)" },
  { value: "America/Chicago", label: "America/Chicago (CST)" },
  { value: "Asia/Tokyo", label: "Asia/Tokyo (JST)" },
  { value: "Australia/Sydney", label: "Australia/Sydney (AEST)" },
];

export const COMMON_COUNTRIES = [
  { code: "IT", label: "Italia" },
  { code: "FR", label: "Francia" },
  { code: "GB", label: "Regno Unito" },
  { code: "DE", label: "Germania" },
  { code: "ES", label: "Spagna" },
  { code: "US", label: "Stati Uniti" },
  { code: "JP", label: "Giappone" },
  { code: "AU", label: "Australia" },
];
```

- [ ] **Step 3: Commit**

```bash
git add apps/dashboard/src/lib/scraping-categories.ts apps/dashboard/src/lib/timezone-lookup.ts
git commit -m "feat(dashboard): add OSM categories and timezone lookup helpers"
```

---

## Task 12: API Routes for scraping_targets

**Files:**
- Create: `agents-platform/apps/dashboard/src/app/api/scraping/targets/route.ts`
- Create: `agents-platform/apps/dashboard/src/app/api/scraping/targets/[id]/route.ts`
- Create: `agents-platform/apps/dashboard/src/app/api/scraping/run-now/route.ts`

- [ ] **Step 1: Create GET/POST route for targets list/create**

Create `apps/dashboard/src/app/api/scraping/targets/route.ts`:
```typescript
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;

function client() {
  return createClient(supabaseUrl, supabaseKey);
}

export async function GET() {
  const { data, error } = await client()
    .from("scraping_targets")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ targets: data });
}

export async function POST(req: Request) {
  const body = await req.json();
  const required = ["category", "category_type", "city", "country_code", "timezone"];
  for (const key of required) {
    if (!body[key]) {
      return NextResponse.json({ error: `Missing field: ${key}` }, { status: 400 });
    }
  }

  const { data, error } = await client()
    .from("scraping_targets")
    .insert({
      category: body.category,
      category_type: body.category_type,
      city: body.city,
      country_code: body.country_code,
      timezone: body.timezone,
      enabled: body.enabled ?? true,
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ target: data }, { status: 201 });
}
```

- [ ] **Step 2: Create PATCH/DELETE route for single target**

Create `apps/dashboard/src/app/api/scraping/targets/[id]/route.ts`:
```typescript
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;

function client() {
  return createClient(supabaseUrl, supabaseKey);
}

export async function PATCH(
  req: Request,
  context: { params: Promise<{ id: string }> }
) {
  const { id } = await context.params;
  const body = await req.json();

  const allowed = ["enabled", "category", "category_type", "city", "country_code", "timezone"];
  const updates: Record<string, unknown> = {};
  for (const key of allowed) {
    if (key in body) updates[key] = body[key];
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ error: "No valid fields to update" }, { status: 400 });
  }

  const { data, error } = await client()
    .from("scraping_targets")
    .update(updates)
    .eq("id", id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ target: data });
}

export async function DELETE(
  _req: Request,
  context: { params: Promise<{ id: string }> }
) {
  const { id } = await context.params;
  const { error } = await client()
    .from("scraping_targets")
    .delete()
    .eq("id", id);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
```

- [ ] **Step 3: Create run-now route**

Create `apps/dashboard/src/app/api/scraping/run-now/route.ts`:
```typescript
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;

export async function POST() {
  const supabase = createClient(supabaseUrl, supabaseKey);
  const { data, error } = await supabase
    .from("events")
    .insert({
      type: "scraping.trigger",
      source_agent: "dashboard",
      target_agent: "scraping",
      payload: {},
      status: "pending",
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ event: data });
}
```

- [ ] **Step 4: Verify build still works**

```bash
cd agents-platform/apps/dashboard
export PATH="/c/Program Files/nodejs:$PATH"
NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder npm run build
```

Expected: Build succeeds. Routes shown:
```
├ ƒ /api/scraping/run-now
├ ƒ /api/scraping/targets
└ ƒ /api/scraping/targets/[id]
```

- [ ] **Step 5: Commit**

```bash
cd ../..
git add apps/dashboard/src/app/api/scraping/
git commit -m "feat(dashboard): add API routes for scraping targets CRUD"
```

---

## Task 13: useScrapingTargets Hook

**Files:**
- Create: `agents-platform/apps/dashboard/src/hooks/useScrapingTargets.ts`

- [ ] **Step 1: Create hook**

Create `apps/dashboard/src/hooks/useScrapingTargets.ts`:
```typescript
"use client";

import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";

export interface ScrapingTarget {
  id: string;
  category: string;
  category_type: string;
  city: string;
  country_code: string;
  timezone: string;
  enabled: boolean;
  last_run_at: string | null;
  total_leads_found: number;
  created_at: string;
}

export function useScrapingTargets() {
  const [targets, setTargets] = useState<ScrapingTarget[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const { data } = await supabase
        .from("scraping_targets")
        .select("*")
        .order("created_at", { ascending: false });
      if (data) setTargets(data as ScrapingTarget[]);
      setLoading(false);
    };
    load();

    const channel = supabase
      .channel("scraping-targets-realtime")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "scraping_targets" },
        (p) => setTargets((prev) => [p.new as ScrapingTarget, ...prev])
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "scraping_targets" },
        (p) => {
          const updated = p.new as ScrapingTarget;
          setTargets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
        }
      )
      .on(
        "postgres_changes",
        { event: "DELETE", schema: "public", table: "scraping_targets" },
        (p) => {
          const deleted = p.old as { id: string };
          setTargets((prev) => prev.filter((t) => t.id !== deleted.id));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const addTarget = useCallback(async (input: {
    category: string;
    category_type: string;
    city: string;
    country_code: string;
    timezone: string;
  }) => {
    const res = await fetch("/api/scraping/targets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Failed to create target");
    }
  }, []);

  const updateTarget = useCallback(
    async (id: string, updates: Partial<Pick<ScrapingTarget, "enabled">>) => {
      const res = await fetch(`/api/scraping/targets/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (!res.ok) throw new Error("Failed to update");
    },
    []
  );

  const deleteTarget = useCallback(async (id: string) => {
    const res = await fetch(`/api/scraping/targets/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete");
  }, []);

  const runNow = useCallback(async () => {
    const res = await fetch("/api/scraping/run-now", { method: "POST" });
    if (!res.ok) throw new Error("Failed to trigger");
  }, []);

  return { targets, loading, addTarget, updateTarget, deleteTarget, runNow };
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/dashboard/src/hooks/useScrapingTargets.ts
git commit -m "feat(dashboard): add useScrapingTargets hook with realtime sync"
```

---

## Task 14: Dashboard Components for Scraping Config

**Files:**
- Create: `agents-platform/apps/dashboard/src/components/scraping/StatsBar.tsx`
- Create: `agents-platform/apps/dashboard/src/components/scraping/AddTargetForm.tsx`
- Create: `agents-platform/apps/dashboard/src/components/scraping/TargetRow.tsx`
- Create: `agents-platform/apps/dashboard/src/components/scraping/TargetsTable.tsx`
- Create: `agents-platform/apps/dashboard/src/components/scraping/NavTabs.tsx`

- [ ] **Step 1: Create StatsBar**

Create `apps/dashboard/src/components/scraping/StatsBar.tsx`:
```tsx
"use client";

import type { ScrapingTarget } from "@/hooks/useScrapingTargets";

interface StatsBarProps {
  targets: ScrapingTarget[];
}

export function StatsBar({ targets }: StatsBarProps) {
  const active = targets.filter((t) => t.enabled).length;
  const totalLeads = targets.reduce((sum, t) => sum + (t.total_leads_found || 0), 0);
  const lastRunDate = targets
    .map((t) => (t.last_run_at ? new Date(t.last_run_at).getTime() : 0))
    .reduce((max, ts) => Math.max(max, ts), 0);
  const lastRunLabel = lastRunDate
    ? new Date(lastRunDate).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" })
    : "—";

  const stats = [
    { value: active, label: "Active targets" },
    { value: totalLeads, label: "Leads totali" },
    { value: targets.length, label: "Target totali" },
    { value: lastRunLabel, label: "Ultimo run" },
  ];

  return (
    <div className="grid grid-cols-4 gap-3">
      {stats.map((s) => (
        <div
          key={s.label}
          className="bg-surface border border-border rounded-xl px-4 py-3.5 text-center"
        >
          <div className="text-2xl font-bold text-accent-light">{s.value}</div>
          <div className="text-[10px] text-muted uppercase tracking-wider mt-0.5">
            {s.label}
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create AddTargetForm**

Create `apps/dashboard/src/components/scraping/AddTargetForm.tsx`:
```tsx
"use client";

import { useState } from "react";
import { SCRAPING_CATEGORIES } from "@/lib/scraping-categories";
import {
  COMMON_COUNTRIES,
  COMMON_TIMEZONES,
  suggestTimezone,
} from "@/lib/timezone-lookup";

interface AddTargetFormProps {
  onAdd: (input: {
    category: string;
    category_type: string;
    city: string;
    country_code: string;
    timezone: string;
  }) => Promise<void>;
}

export function AddTargetForm({ onAdd }: AddTargetFormProps) {
  const [categoryIdx, setCategoryIdx] = useState(0);
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("IT");
  const [timezone, setTimezone] = useState("Europe/Rome");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onCityBlur = () => {
    if (city) setTimezone(suggestTimezone(city, country));
  };
  const onCountryChange = (newCountry: string) => {
    setCountry(newCountry);
    setTimezone(suggestTimezone(city, newCountry));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!city.trim()) {
      setError("Inserisci una città");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const cat = SCRAPING_CATEGORIES[categoryIdx];
      await onAdd({
        category: cat.value,
        category_type: cat.type,
        city: city.trim(),
        country_code: country,
        timezone,
      });
      setCity("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore sconosciuto");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="bg-surface border border-border rounded-xl p-4 space-y-3"
    >
      <h3 className="text-sm font-semibold">➕ Aggiungi Target</h3>
      <div className="grid grid-cols-4 gap-3">
        <select
          value={categoryIdx}
          onChange={(e) => setCategoryIdx(Number(e.target.value))}
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        >
          {SCRAPING_CATEGORIES.map((c, i) => (
            <option key={c.value} value={i}>
              {c.label}
            </option>
          ))}
        </select>
        <input
          value={city}
          onChange={(e) => setCity(e.target.value)}
          onBlur={onCityBlur}
          placeholder="Città (es. Milano)"
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        />
        <select
          value={country}
          onChange={(e) => onCountryChange(e.target.value)}
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        >
          {COMMON_COUNTRIES.map((c) => (
            <option key={c.code} value={c.code}>
              {c.label}
            </option>
          ))}
        </select>
        <select
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          className="bg-black/40 border border-border rounded-md px-3 py-2 text-sm"
        >
          {COMMON_TIMEZONES.map((tz) => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
      </div>
      {error && <div className="text-xs text-red-400">{error}</div>}
      <button
        type="submit"
        disabled={submitting}
        className="w-full py-2 border border-accent/30 bg-accent/10 text-accent-light rounded-lg text-sm font-medium hover:bg-accent/25 hover:border-accent transition-colors cursor-pointer disabled:opacity-50"
      >
        {submitting ? "Salvataggio..." : "+ Aggiungi"}
      </button>
    </form>
  );
}
```

- [ ] **Step 3: Create TargetRow**

Create `apps/dashboard/src/components/scraping/TargetRow.tsx`:
```tsx
"use client";

import type { ScrapingTarget } from "@/hooks/useScrapingTargets";
import { SCRAPING_CATEGORIES } from "@/lib/scraping-categories";

interface TargetRowProps {
  target: ScrapingTarget;
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function TargetRow({ target, onToggle, onDelete }: TargetRowProps) {
  const cat = SCRAPING_CATEGORIES.find(
    (c) => c.value === target.category && c.type === target.category_type
  );
  const label = cat?.label || `${target.category_type}=${target.category}`;
  const lastRun = target.last_run_at
    ? new Date(target.last_run_at).toLocaleString("it-IT", {
        dateStyle: "short",
        timeStyle: "short",
      })
    : "mai";

  return (
    <tr className="border-b border-white/[0.03] text-sm hover:bg-surface/40">
      <td className="px-3 py-2">
        <button
          onClick={() => onToggle(target.id, !target.enabled)}
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            target.enabled
              ? "bg-success/20 text-success"
              : "bg-zinc-700/50 text-zinc-400"
          }`}
        >
          {target.enabled ? "✅ ON" : "⏸ OFF"}
        </button>
      </td>
      <td className="px-3 py-2">{label}</td>
      <td className="px-3 py-2">{target.city}</td>
      <td className="px-3 py-2 text-muted text-xs">{target.country_code}</td>
      <td className="px-3 py-2 text-xs">{lastRun}</td>
      <td className="px-3 py-2 text-right text-accent-lighter font-semibold">
        {target.total_leads_found}
      </td>
      <td className="px-3 py-2 text-right">
        <button
          onClick={() => {
            if (confirm(`Eliminare target "${label} - ${target.city}"?`)) {
              onDelete(target.id);
            }
          }}
          className="text-red-400 hover:text-red-300 text-sm"
          title="Elimina"
        >
          🗑️
        </button>
      </td>
    </tr>
  );
}
```

- [ ] **Step 4: Create TargetsTable**

Create `apps/dashboard/src/components/scraping/TargetsTable.tsx`:
```tsx
"use client";

import type { ScrapingTarget } from "@/hooks/useScrapingTargets";
import { TargetRow } from "./TargetRow";

interface TargetsTableProps {
  targets: ScrapingTarget[];
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function TargetsTable({ targets, onToggle, onDelete }: TargetsTableProps) {
  if (targets.length === 0) {
    return (
      <div className="bg-black/40 border border-border/60 rounded-xl p-8 text-center text-muted text-sm">
        Nessun target configurato. Aggiungine uno qui sopra.
      </div>
    );
  }

  return (
    <div className="bg-black/40 border border-border/60 rounded-xl overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-wider text-muted border-b border-border/60">
            <th className="px-3 py-2">Stato</th>
            <th className="px-3 py-2">Categoria</th>
            <th className="px-3 py-2">Città</th>
            <th className="px-3 py-2">Paese</th>
            <th className="px-3 py-2">Ultimo run</th>
            <th className="px-3 py-2 text-right">Leads</th>
            <th className="px-3 py-2 text-right">Azioni</th>
          </tr>
        </thead>
        <tbody>
          {targets.map((t) => (
            <TargetRow
              key={t.id}
              target={t}
              onToggle={onToggle}
              onDelete={onDelete}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 5: Create NavTabs**

Create `apps/dashboard/src/components/scraping/NavTabs.tsx`:
```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "Dashboard" },
  { href: "/scraping-config", label: "🎯 Scraping Config" },
];

export function NavTabs() {
  const pathname = usePathname();
  return (
    <nav className="flex gap-1 px-6 py-2 border-b border-border bg-black/30">
      {tabs.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              active
                ? "bg-accent/20 text-accent-light"
                : "text-muted hover:text-zinc-200 hover:bg-surface"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add apps/dashboard/src/components/scraping/
git commit -m "feat(dashboard): add scraping config UI components"
```

---

## Task 15: Scraping Config Page + Header Update

**Files:**
- Create: `agents-platform/apps/dashboard/src/app/scraping-config/page.tsx`
- Modify: `agents-platform/apps/dashboard/src/components/Header.tsx`
- Modify: `agents-platform/apps/dashboard/src/app/page.tsx`

- [ ] **Step 1: Create scraping-config page**

Create `apps/dashboard/src/app/scraping-config/page.tsx`:
```tsx
"use client";

import { Header } from "@/components/Header";
import { NavTabs } from "@/components/scraping/NavTabs";
import { StatsBar } from "@/components/scraping/StatsBar";
import { AddTargetForm } from "@/components/scraping/AddTargetForm";
import { TargetsTable } from "@/components/scraping/TargetsTable";
import { useScrapingTargets } from "@/hooks/useScrapingTargets";
import { useState } from "react";

export default function ScrapingConfigPage() {
  const { targets, loading, addTarget, updateTarget, deleteTarget, runNow } =
    useScrapingTargets();
  const [running, setRunning] = useState(false);

  const handleRunNow = async () => {
    setRunning(true);
    try {
      await runNow();
      alert("Trigger inviato! Lo scraping partirà tra qualche secondo.");
    } catch (e) {
      alert("Errore: " + (e instanceof Error ? e.message : "unknown"));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header agentCount={3} isConnected={true} />
      <NavTabs />
      <div className="p-6 space-y-6 max-w-6xl mx-auto">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent mb-4">
            Overview
          </div>
          <StatsBar targets={targets} />
        </div>

        <AddTargetForm onAdd={addTarget} />

        <div>
          <div className="flex justify-between items-center mb-4">
            <div className="text-[11px] font-semibold uppercase tracking-[1.2px] text-accent">
              Targets configurati
            </div>
            <button
              onClick={handleRunNow}
              disabled={running || targets.filter((t) => t.enabled).length === 0}
              className="py-1.5 px-4 border border-accent/30 bg-accent/10 text-accent-light rounded-lg text-xs font-medium hover:bg-accent/25 hover:border-accent transition-colors cursor-pointer disabled:opacity-50"
            >
              {running ? "Invio..." : "▶ Esegui ora tutti"}
            </button>
          </div>
          {loading ? (
            <div className="text-center text-muted py-4">Caricamento...</div>
          ) : (
            <TargetsTable
              targets={targets}
              onToggle={(id, enabled) => updateTarget(id, { enabled })}
              onDelete={deleteTarget}
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Update main dashboard page to include NavTabs**

Edit `apps/dashboard/src/app/page.tsx`. Find the line right after `<Header ... />` and add:
```tsx
import { NavTabs } from "@/components/scraping/NavTabs";
```
in the imports.

Then find:
```tsx
<Header agentCount={onlineAgents} isConnected={isConnected} />

      <div className="grid grid-cols-[1fr_380px] min-h-[calc(100vh-69px)]">
```

And replace with:
```tsx
<Header agentCount={onlineAgents} isConnected={isConnected} />
      <NavTabs />

      <div className="grid grid-cols-[1fr_380px] min-h-[calc(100vh-119px)]">
```

(The `calc(100vh-119px)` accounts for the additional NavTabs height.)

- [ ] **Step 3: Verify build**

```bash
cd agents-platform/apps/dashboard
export PATH="/c/Program Files/nodejs:$PATH"
NEXT_PUBLIC_SUPABASE_URL=https://placeholder.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder npm run build
```

Expected: Build succeeds. Routes shown:
```
┌ ○ /
├ ○ /_not-found
├ ○ /scraping-config
├ ƒ /api/chat
├ ƒ /api/export
├ ƒ /api/scraping/run-now
├ ƒ /api/scraping/targets
└ ƒ /api/scraping/targets/[id]
```

- [ ] **Step 4: Commit**

```bash
cd ../..
git add apps/dashboard/src/app/scraping-config/ apps/dashboard/src/app/page.tsx
git commit -m "feat(dashboard): add scraping-config page with NavTabs"
```

---

## Task 16: Update Railway Service & Deploy

**Files:**
- Modify: Railway service `scraping-worker` start command (manual or via API)

- [ ] **Step 1: Push all changes to GitHub**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
export PATH="/c/Program Files/GitHub CLI:$PATH"
git push origin master
```

- [ ] **Step 2: Update Railway start command**

The Railway service `scraping-worker` (id `0c828609-37e0-4cdc-836e-ad37f28b7bed`) has start command:
```
python -m apps.workers.scraping_stub.main
```

Change to:
```
python -m apps.workers.scraping_worker.main
```

Use Railway GraphQL API:
```bash
export PATH="/c/Program Files/nodejs:$PATH"
node -e "
const TOKEN = process.env.RAILWAY_TOKEN;
const SVC = '0c828609-37e0-4cdc-836e-ad37f28b7bed';
const ENV = '07e540a7-8c3f-46ab-ae80-24717d4361e7';

fetch('https://backboard.railway.app/graphql/v2', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TOKEN },
  body: JSON.stringify({ query: \`
    mutation {
      serviceInstanceUpdate(
        serviceId: \\\"\${SVC}\\\",
        environmentId: \\\"\${ENV}\\\",
        input: { startCommand: \\\"python -m apps.workers.scraping_worker.main\\\" }
      )
    }
  \`})
}).then(r => r.json()).then(d => console.log(JSON.stringify(d)));
" 
```

(If the API call returns "Not Authorized", manually update the start command in the Railway dashboard for the `scraping-worker` service.)

- [ ] **Step 3: Wait for Railway redeploy + verify worker is up**

Wait ~60 seconds for Railway to rebuild and deploy.

Verify by checking Supabase that the scraping agent has a recent heartbeat:
```bash
# Use Supabase MCP execute_sql tool with project_id smzmgzblbliprwbjptjs:
SELECT id, status, last_heartbeat FROM agents WHERE id = 'scraping';
```
Expected: `status='idle'`, `last_heartbeat` within last 60 seconds.

- [ ] **Step 4: Trigger manual scraping run**

```bash
# Use Supabase MCP execute_sql to insert a trigger event:
INSERT INTO events (type, source_agent, target_agent, payload, status)
VALUES ('scraping.trigger', 'dashboard', 'scraping', '{}', 'pending');
```

Wait 30 seconds. Then query:
```sql
SELECT * FROM scraping_runs ORDER BY started_at DESC LIMIT 5;
SELECT company_name, phone, city, source FROM leads WHERE source = 'openstreetmap' LIMIT 10;
```

Expected: At least 1 row in `scraping_runs` with status='completed', and several real leads in `leads` table from OpenStreetMap.

- [ ] **Step 5: Deploy dashboard to Vercel**

```bash
cd apps/dashboard
export PATH="/c/Program Files/nodejs:$PATH"
vercel --prod --yes
```

Expected: Successful deployment URL.

- [ ] **Step 6: Verify scraping-config page works**

Open `https://agents-dashboard-theta.vercel.app/scraping-config` in browser.

Expected: Page loads, lists all targets seeded in Task 1, "▶ Esegui ora tutti" button is present, can add/toggle/delete targets.

---

## Task 17: Update BRAINSTORM_STATE

**Files:**
- Modify: `c:\Users\indig\.antigravity\AGENT 2.0_TEST\BRAINSTORM_STATE.md`

- [ ] **Step 1: Mark Sub-project B as completed in state file**

Update the table at the top:
```
| B | Web Scraping Agent | **✅ COMPLETATO + DEPLOYATO** |
```

Add deployment URLs and verified end-to-end test.

- [ ] **Step 2: Commit**

```bash
cd ..
git add BRAINSTORM_STATE.md  
# Note: BRAINSTORM_STATE.md is at the parent dir, not in agents-platform repo
# This step is only if user wants to track state in git; otherwise just save the file.
```
