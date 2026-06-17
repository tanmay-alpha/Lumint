# Lumint Frontend

Next.js 16 App Router frontend for Lumint.

## Local development

From the repository root:

```bash
npm install
npm run dev:frontend
```

Or from this directory:

```bash
npm install
cp .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local` when running
against a local FastAPI backend.

Open http://localhost:3000.

## Scripts

```bash
npm run dev        # Next.js dev server
npm run lint       # ESLint
npm run typecheck  # TypeScript no-emit check
npm run test       # lint + typecheck
npm run build      # production build
```

## Runtime config

- `NEXT_PUBLIC_API_URL`: FastAPI base URL. Leave blank on deployed demos to use the same-origin proxy/fallback.
- `LUMINT_API_KEY`: required server-only API key for the Next.js proxy route in production. Must match the backend key. Never expose this with a `NEXT_PUBLIC_` prefix.
- `NEXT_PUBLIC_DISABLE_PROXY=1`: bypasses the Vercel same-origin proxy and calls the backend directly.
