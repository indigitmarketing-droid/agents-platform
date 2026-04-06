# agents-platform

Multi-agent orchestrator platform with 3 AI agents.

## Stack

- **Backend workers**: Python 3.12+, deployed on Railway
- **Dashboard**: Next.js, deployed on Vercel
- **Database / Realtime / Auth**: Supabase

## Structure

```
agents-platform/
├── apps/
│   ├── dashboard/          # Next.js frontend
│   └── workers/            # Python agent workers
│       ├── scraping_stub/
│       ├── setting_stub/
│       └── builder_stub/
├── packages/
│   ├── events_schema/      # Shared event schemas
│   └── agent_framework/    # Shared agent utilities
├── supabase/
│   └── migrations/
└── tests/
    └── integration/
```

## Setup

1. Copy `.env.example` to `.env` and fill in your values.
2. Install Python deps: `pip install -e ".[dev]"`
3. Install dashboard deps: `cd apps/dashboard && npm install`
