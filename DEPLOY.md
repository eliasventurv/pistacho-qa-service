# Deployment README (Windows)
1. Install Python 3.12
2. `python -m venv .venv; .venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` or set `$env:QA_API_TOKEN = "<agreed-token>"`
5. Place model files in `artifacts/distilbert-squad2/`
6. Run `.\run.ps1` or `uvicorn app:app --host 0.0.0.0 --port 8000`
7. Start Cloudflare Quick Tunnel: `cloudflared tunnel --url http://localhost:8000` (or ngrok backup)
8. Share public URL with instructor; keep machine plugged in and awake
