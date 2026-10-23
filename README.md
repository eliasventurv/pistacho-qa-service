# Pistacho QA Service
Team: Pistacho (Elías Ventura Villatoro, Andrés Avilés, Lilly Vásquez)

Extractive Question Answering as a Service following the SQuAD 2.0 style API contract.

## Quick Start
1. Create venv: `python -m venv .venv` (Windows: `.venv\Scripts\activate`)
2. Install: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `QA_API_TOKEN` (agreed token)
4. Place fine-tuned model in `artifacts/distilbert-squad2/` (from training machine)
5. Run: `uvicorn app:app --host 0.0.0.0 --port 8000` (or `.\run.ps1`)
6. Expose via tunnel (Cloudflare/ngrok) on the serving machine

## Notes
- No cloud hosting allowed. Model runs locally on the serving/training laptop.
- Weights are not tracked in git (see `.gitignore`).
- API contract is in `docs/qa_api_contract.yaml`.
- Do not push to `origin/main` without merging branches; commits are local only.
