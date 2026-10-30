# Compliance audit — 30 October 2026

## Section V

| Rule | Implementation | Verified evidence |
|---|---|---|
| Start from a base checkpoint; train yourselves | distilbert-base-uncased, new QA head, local SQuAD 2.0 fine-tuning | logs/run_metadata.json: base revision, source commit, 40,000 train IDs, 2,526 optimizer steps; training_log.json and loss.png |
| No commercial inference APIs | CPU model/tokenizer loaded with local_files_only=True | Source review plus real local and HTTPS predictions |
| Exact API contract and access control | FastAPI dependencies, strict body validation, JSON errors, original span offsets and long-context windows | 30 tests passed; eight real 401 checks locally and through Cloudflare; valid predictions over both paths |
| Token from environment; never committed | QA_API_TOKEN read at request time; constant-time comparison | Temporary test tokens generated only in memory; .env ignored; no real token in source |
| Preserve Git history | Original 15 commits retained; changes in codex/local-training-api-compliance | No squash/reset/force push; original main commit remains an ancestor |

`logs/compliance_audit.json` records reproducible checks and the served weights'
SHA256. Static evidence and tests support these conclusions; they do not replace
the instructor's compliance checks or hidden evaluation.

## Measured results

- Held-out SQuAD (500 questions): **58.40 EM / 60.37 F1**.
- Public samples: **3/5 correct**, both locally and over HTTPS.
- Public errors: false null on BERT-large; unsupported `10,000 times` on LoRA.
- Long-context sample: correct `50,257` at character 3157.
- Local CPU benchmark: **50 requests in 12.71 s**, slowest **0.54 s**.
- Five HTTPS requests: mean **0.48 s**, slowest **0.72 s**.

This benchmark repeats the five public samples. It cannot guarantee latency or
accuracy on the unseen 50-item evaluation. The public test tunnel was stopped
after verification; its recorded URL is not a currently running service.

## Delivery status

- [x] Actual local fine-tuning, loss logs and loss curve.
- [x] Separate calibration and held-out evaluation.
- [x] Real HTTP sample predictions and CPU latency.
- [x] Primary Cloudflare tunnel and access control tested.
- [x] English REPORT.md with all required headings and actual errors.
- [x] Weights outside Git; original history preserved.
- [x] Three-minute pitch and code-specific Q&A notes prepared.
- [ ] Instructor's token and registered team name confirmed.
- [ ] Backup ngrok account configured and tunnel tested (user has no account).
- [ ] Instructor dry run from another network and URL shared by the team.
- [x] Version closed by the team; submission tag identifies this snapshot.
- [ ] Pitch and individual Q&A rehearsed by each member.

**Not yet a fully completed submission.** Technical operation and section V
have supporting evidence, but public-sample quality is imperfect and the above
external steps remain. A report with missing/empty sections halves the grade.

