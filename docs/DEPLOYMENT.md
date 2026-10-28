# Deploying EvidenceFlow

One Docker container serves the React app and the FastAPI API from the same
address. The SQLite database lives in `/data`, which must be a persistent volume.

## Railway (recommended)

Why Railway: its free and trial plans include a persistent volume (0.5 GB), so the
SQLite database survives restarts and redeploys. Render's free web services cannot
attach a disk and lose local files on every restart or after 15 idle minutes.
Check current plan limits before relying on them.

1. Sign in at railway.com with GitHub and create a **New Project → Deploy from
   GitHub repo**, choosing the team repository (or your fork). Railway reads
   `railway.json` and builds the root `Dockerfile`.
2. In the service, **add a Volume** with mount path **`/data`**. Without it every
   redeploy starts with an empty database.
3. **Variables** (Settings → Variables):

   | Variable | Value | Required |
   |---|---|---|
   | `NCBI_EMAIL` | a team contact email (NCBI asks every tool to identify itself) | Yes for PubMed |
   | `NCBI_API_KEY` | NCBI key, raises PubMed from 3 to 10 requests/s | No |
   | `IMPORT_CAP` | max records per import (default 500) | No |

   `DATABASE_URL`, `FRONTEND_DIST` and `PORT` are already handled by the image
   and Railway. Never commit real values.
4. **Settings → Networking → Generate Domain** to get the public HTTPS URL.
5. Deploys run `alembic upgrade head` before starting, so migrations apply
   automatically. The health check is `GET /api/health`.

### Verify the deployment (record the results)

1. Open the URL: the app loads. `<url>/docs` shows the API.
2. `<url>/api/health` returns `"database": "connected"`.
3. Create a review, run a small Europe PMC search with titles/abstracts only,
   preview and import. The run reaches `completed`.
4. **Persistence:** in Railway, **Restart** the service. Reload the app: the review
   and records are still there. If not, the volume is missing or not at `/data`.
5. Repeat with PubMed (needs `NCBI_EMAIL`).

## Run the same container locally

```bash
docker build -t evidenceflow .
docker run --rm -p 8000:8000 -v evidenceflow-data:/data -e NCBI_EMAIL=you@example.org evidenceflow
# open http://localhost:8000
```

## Without Docker (single server, no Vite)

```bash
cd frontend && npm ci && npm run build && cd ..
cd backend && alembic upgrade head && uvicorn app.main:app --port 8000
# open http://127.0.0.1:8000 (FastAPI serves frontend/dist automatically when it exists)
```

## Limits to state honestly

- SQLite with one container: fine for a single demo team, not for many writers.
- Background imports run inside the web process; a restart during an import marks
  that run failed and the import can be retried.
- Free tiers change; the verification above is the evidence, not the plan name.
