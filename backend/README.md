# Accounting OCR Backend

FastAPI backend for the Accounting OCR Platform.

## Local Run

```bash
cd backend
python3 -m pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8001
```

Open:

- `http://localhost:8001/api/v1/health`
- `http://localhost:8001/docs`

## Demo Context

```text
X-Organization-Id: org_demo
X-User-Id: user_admin
X-Role: admin
```

## Google SSO

```bash
GOOGLE_TOKEN_VERIFIER_MODE=demo
```

For production-like verification:

```bash
GOOGLE_TOKEN_VERIFIER_MODE=google
GOOGLE_CLIENT_ID=<your-google-client-id>
```

## Database Bootstrap

```bash
cd backend
alembic upgrade head
python -m scripts.seed_demo
```

## Tests

```bash
cd backend
pytest -q -m 'not integration'
```

## Worker

```bash
cd backend
python -m scripts.run_worker
```

## OCR Provider

```bash
OPENAI_API_KEY=<your-api-key>
OPENAI_OCR_MODEL=gpt-4.1-mini
```
