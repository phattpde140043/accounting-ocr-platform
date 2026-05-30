# Accounting OCR Frontend

NextJS frontend for the Accounting OCR Platform.

## Local Run

```bash
cd frontend
npm install
npm run dev -- --port 3001
```

Open `http://localhost:3001`.

Current pages:

- `/`
- `/dashboard`
- `/accounting`
- `/accounting/review`
- `/auth/google/callback`
- `/ai`
- `/admin`

Set the backend URL with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api/v1
NEXT_PUBLIC_AUTH_MODE=demo
```

The accounting intake page includes approved-document export. The reviewer page
supports versioned field correction and approval. API calls use a bounded
timeout and show an unavailable state when backend services are offline.
