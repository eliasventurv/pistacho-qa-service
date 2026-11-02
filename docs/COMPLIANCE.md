# Compliance audit — 2 November 2026

## Section V

| Rule | Implementation | Verified evidence |
|---|---|---|
| Start from a base checkpoint; train yourselves | FacebookAI/roberta-base, new QA head, local SQuAD 2.0 fine-tuning | logs/run_metadata.json: base revision, source commit, 130,319 train IDs, 8,238 optimizer steps; training_log.json and loss.png |
| No commercial inference APIs | CPU model/tokenizer loaded with local_files_only=True | Source review plus real local and HTTPS predictions |
| Exact API contract and access control | FastAPI dependencies, strict body validation, JSON errors, original span offsets and long-context windows | 30 tests passed; eight real 401 checks locally and through Cloudflare; valid predictions over both paths |
| Token from environment; never committed | QA_API_TOKEN read at request time; constant-time comparison | Temporary test tokens generated only in memory; .env ignored; no real token in source |
| Preserve Git history | Original commits retained; changes added as new commits on feature branches | No squash/reset/force push; original main commit remains an ancestor |

`logs/compliance_audit.json` records reproducible checks and the served weights'
SHA256. Static evidence and tests support these conclusions; they do not replace
the instructor's compliance checks or hidden evaluation.

## Measured results

- Held-out SQuAD (2,000 questions): **81.25 EM / 83.77 F1** (DistilBERT baseline: 58.40 / 60.37).
- Public samples: **5/5 correct** over local HTTP (DistilBERT: 3/5).
- Long-context sample: correct `50,257` at character 3157.
- Local CPU benchmark: **50 requests in 19.9 s**, mean **0.40 s**, slowest **0.87 s**.
- Through ngrok: 5/5 correct, mean **0.73 s**, slowest **1.17 s**.

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
- [x] Team name `pistacho`; token chosen by the team (set only in the environment).
- [x] ngrok account configured; fixed domain https://boil-confiding-default.ngrok-free.dev.
- [x] Five brief checks and 401 checks through ngrok with the RoBERTa service.
- [ ] Instructor dry run from another network and URL shared by the team.
- [ ] RoBERTa weights uploaded as a release; `submission` tag moved to the RoBERTa commit.
- [ ] Pitch and individual Q&A rehearsed by each member.

**Not yet a fully completed submission.** Technical operation and section V
have supporting evidence, but public-sample quality is imperfect and the above
external steps remain. A report with missing/empty sections halves the grade.

