# Compliance audit

Status is based on evidence, not on the presence of a script.

## Section V

| Rule | Implementation | Verification/evidence |
|---|---|---|
| Start from a base encoder; train yourselves | Approved base checkpoint allowlist; actual Trainer.train() | Pending completed local run, metadata and loss curve |
| No commercial inference APIs | Model and tokenizer loaded locally; CPU inference | Code inspection; pending real prediction smoke test |
| Exact API contract and access control | FastAPI Depends, strict body validation, JSON errors, span offsets, sliding windows | tests/test_api.py and tests/test_qa.py; test run pending |
| Token only from environment; never committed | QA_API_TOKEN read at request time; constant-time comparison; .env ignored | Tests and Git diff/history scan before push |
| Preserve Git history | Original 15 commits retained; feature branch codex/local-training-api-compliance | git log; no squash/reset/force push |

## Other required evidence

- [ ] Successful fine-tuning, actual training log and loss plot.
- [ ] Calibrated no-answer threshold and disjoint EM/F1 evaluation.
- [ ] Five public samples tested over HTTP with actual trained weights.
- [ ] CPU latency measured against the 5 s/request and 150 s overall caps.
- [ ] Primary tunnel tested; backup tunnel installed and tested.
- [ ] External-network dry run and URL shared with instructor by the team.
- [ ] REPORT.md completed in English with all ten required headings.
- [ ] Weights stored outside Git; source and evidence committed.
- [ ] Final submission tag pushed on the reviewed commit.
- [ ] Pitch and individual Q&A rehearsed (no AI during Q&A).

The hidden test set and individual oral performance cannot be certified locally.
A complete report is mandatory: missing or empty sections halve the final grade.
