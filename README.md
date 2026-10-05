# NoteTaker

A Flask note-taking app with an OpenRouter-powered translation action.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Open <http://127.0.0.1:5000>. The SQLite database is created at
`database/app.db` automatically. Set `OPENROUTER_API_KEY` in your environment
or in a root `.env` file to enable translation:

```dotenv
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Deploy to Vercel

Deploy this repository as a Python project. All requests are rewritten to
`api/index.py`, which serves both the SPA and `/api/notes` endpoints. When
`VERCEL` is set, SQLite uses `/tmp/app.db` and does not create directories.
Vercel's `/tmp` filesystem is ephemeral, so notes are not durable across
serverless instance replacement; use a persistent database for production
data retention.

Set `OPENROUTER_API_KEY` as a Vercel environment variable to enable translation.
