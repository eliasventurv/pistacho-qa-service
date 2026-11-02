# Pistacho QA Service

Team: **pistacho** — Elías Ventura, Lilly Flores, Andrés Avilés.

Local extractive question answering with no-answer detection, trained from the
base `FacebookAI/roberta-base` encoder on SQuAD 2.0. No commercial inference API.

## Windows / CUDA GPU setup

Use Python **3.12** (3.10 also works with `requirements.txt`). Open PowerShell in this repository:

```powershell
.\setup.ps1
.\.venv\Scripts\python.exe -m pytest -q
.\train.ps1
```

The training script uses the full SQuAD 2.0 train set (130,319 questions), two epochs, batch 8,
gradient accumulation 4 and CUDA mixed precision when available. It downloads
the base encoder and SQuAD data, then trains locally. Downloading pretrained
base weights is not using an inference API. The QA head starts untrained.

`train.ps1` also calibrates the no-answer threshold. Validation indices after
shuffling with seed 42: 0–1999 for calibration, 2000–3999 for held-out EM/F1,
4000–4499 for loss monitoring. Full training takes about 2 h on an RTX 4050 Laptop GPU. No public sample is used for training or tuning.

To resume an interrupted run, provide an existing checkpoint directory:

```powershell
.\train.ps1 -Resume 'artifacts/roberta-squad2/checkpoints/checkpoint-7000'
```

## Serve on CPU

Set `QA_API_TOKEN` in the terminal to the token agreed with the instructor.
Never put the value in source code, commits, screenshots, or logs. `.env` files
are ignored, but are **not automatically loaded**.

```powershell
# Set QA_API_TOKEN in this terminal first.
.\run.ps1
# In a second terminal with QA_API_TOKEN set:
.\.venv\Scripts\python.exe -m scripts.eval_sample
```

`/health` is public. `/info` and `/predict` require the exact, case-sensitive
`Authorization: Bearer <token>` header. The service binds to 127.0.0.1:8000,
loads only local weights, uses one worker and four CPU inference threads.
Set `QA_CPU_THREADS` to benchmark a different thread count.

See [DEPLOY.md](DEPLOY.md) for the required HTTPS tunnel and backup.
See [docs/COMPLIANCE.md](docs/COMPLIANCE.md) for the section V audit.

## Evidence and delivery

- `logs/run_metadata.json`: base checkpoint, data IDs, hardware and actual run.
- `logs/training_log.json` and `logs/loss.png`: real training evidence.
- `logs/validation.json`: calibration and disjoint validation results.
- `logs/public_sample_results.json`: actual HTTP predictions and CPU latency.
- `logs/distilbert-baseline/`: evidence of the earlier DistilBERT model, kept for comparison.
- `REPORT.md`: report in English, with all required headings.
- `docs/PRESENTATION.md`: three-minute pitch and code-specific Q&A preparation.

Model weights and checkpoints stay in `artifacts/`, outside Git. Keep the
original Git history and push changes only to the feature branch. Create the
`submission` tag only after the report and real evaluation evidence are ready.
A ZIP of the source code is not a replacement for Git history.
