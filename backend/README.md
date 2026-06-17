# Lumint Backend

Full-featured FastAPI backend for Lumint - advanced threat detection platform with ML/AI capabilities.

## Features

- **Multi-shield analysis**: UPI, Document Forensics (PDF, image), Phishing, Fraud DNA Network
- **Real-time streaming**: WebSockets for live threat telemetry
- **ML-powered**: Fraud DNA clustering, UPI pattern analysis, document forensics, phishing detection
- **AI integration**: Groq for enhanced detection capabilities
- **Research endpoints**: Ablation, SHAP values, dataset analysis
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: In-process TTL cache for duplicate analysis suppression
- **Auth & rate limiting**: Production-grade security
- **CORS ready**: Configured for frontend integration

## Deploy to Render

Use the canonical blueprint at the repository root: `../render.yaml`.

It configures:

- Docker runtime with `backend/Dockerfile.prod`
- Gunicorn with Uvicorn workers
- PostgreSQL database
- Health checks at `/healthz`
- Required production env vars: `APP_ENV=production`, `DATABASE_URL`, `CORS_ALLOW_ORIGINS`, `LUMINT_API_KEY`
- Optional AI env var: `GROQ_API_KEY`

Do not use the Python buildpack start command for production. FastAPI is ASGI;
the production command must use `uvicorn.workers.UvicornWorker` as defined in
`Dockerfile.prod`.

## Local Development

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env
python main.py
```

API docs: http://localhost:8000/docs

## Architecture

```
backend/
├── app/
│   ├── main.py          # FastAPI app with middleware
│   ├── config.py        # Environment config, settings, logging
│   ├── database.py      # DB connection, models, session
│   ├── dependencies/    # Auth, security utilities
│   ├── routers/         # API routes (health, upi, documents, etc.)
│   └── services/        # Core business logic
├── ml/                 # Machine learning models, registry, research
├── research/           # Research outputs, datasets, paper results
├── reports/            # Generated PDF reports
└── uploads/            # File upload storage
```

## Endpoints

The backend exposes all endpoints expected by the frontend:

- **Health checks**: `/healthz`, `/readyz`, `/health` (legacy alias)
- **UPI Shield**: `/api/upi/report`, `/api/upi/stats`
- **DocShield**: `/api/documents/analyze` (PDF + image)
- **PhishShield**: `/api/phishing/check`
- **Fraud DNA**: `/api/fraud-dna/*` (network analysis, campaigns)
- **Dashboard**: `/api/dashboard/*` (stats, events, metrics)
- **Research**: `/api/research/*` (ablation, SHAP, metrics)

## File Uploads

- Max size: 20MB (enforced by middleware)
- Supported formats: PDF, JPG, JPEG, PNG
- Document analysis includes metadata, creator info, ELA (Error Level Analysis)

## Rate Limiting

Enabled via SlowAPI - see `app/rate_limit.py` for details.

## Development vs Production

| Environment | Config | Features |
|-------------|--------|----------|
| Development | `DEBUG=True` | Hot reload, verbose logs, local DB |
| Production | `DEBUG=False` | Gunicorn, rate limiting, strict CORS |