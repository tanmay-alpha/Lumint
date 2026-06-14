# Lumint Backend

Full-featured FastAPI backend for Lumint - advanced threat detection platform with ML/AI capabilities.

## Features

- **Multi-shield analysis**: UPI, Document Forensics (PDF, image), Phishing, Fraud DNA Network
- **Real-time streaming**: WebSockets for live threat telemetry
- **ML-powered**: Fraud DNA clustering, UPI pattern analysis, document forensics, phishing detection
- **AI integration**: Groq for enhanced detection capabilities
- **Research endpoints**: Ablation, SHAP values, dataset analysis
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Redis**: Caching and session management
- **Auth & rate limiting**: Production-grade security
- **CORS ready**: Configured for frontend integration

## Deploy to Render (Free Tier)

1. Push to GitHub
2. Go to render.com → New + → Web Service
3. Connect your GitHub repo
4. Root Directory: `backend` (not `/app`!)
5. Runtime: Python
6. Build Command: `pip install -r requirements.txt`
7. Start Command: `gunicorn app.main:app --bind 0.0.0.0 --port $PORT`
8. Plan: Free tier
9. Environment variables:
   ```
   DATABASE_URL=[Render generated DB URL]
   REDIS_URL=[Render generated Redis URL]
   ALLOWED_ORIGINS=https://lumint-pi.vercel.app,http://localhost:3000
   CORS_ORIGINS=https://lumint-pi.vercel.app,http://localhost:3000
   ```
10. Deploy

Render will automatically detect the `render.yaml` and configure:

- PostgreSQL database (`free` tier)
- Redis cache (`free` tier)
- Web service (free tier)
- Health checks at `/health`

## Local Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
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

- **Health checks**: `/health`, `/readyz` (Kubernetes-style)
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