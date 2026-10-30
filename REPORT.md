# Project Report — Extractive QA as a Service

## 0. Team

| Field | Value |
|---|---|
| Team id | Pistacho (chosen by team; instructor registration pending) |
| Members | Elías Ventura, Lilly Flores, Andrés Avilés |
| Repository URL | https://github.com/eliasventurv/pistacho-qa-service |
| `submission` commit hash | Pending final dry run and submission tag; resolve with `git rev-parse submission` |
| Public service URL used at the dry run | Team self-test: https://indexed-bibliographic-glossary-contributing.trycloudflare.com (temporary tunnel stopped); instructor dry run pending |
| AI tools used (which, and for what) | Codex: scaffold audit, implementation, tests, local training orchestration and documentation; team must understand and defend code |

## 1. Model choice and justification

We started from **distilbert-base-uncased**, a base encoder, not a SQuAD checkpoint. Its six
layers make CPU serving more practical than twelve-layer BERT-base, which we
considered but did not select because of compute and latency. The QA head was
randomly initialized and trained locally. This trades some accuracy for a
smaller model under the five-second HTTP deadline.

## 2. Training

| Item | Value |
|---|---|
| Training data | SQuAD 2.0 train, seeded subset of 40000 questions |
| Validation data | 500 loss-monitoring, 500 calibration, 500 disjoint held-out questions |
| Epochs | 2 |
| Learning rate and schedule | 3e-05, linear decay, warmup ratio 0.1 |
| Batch size | 8, accumulation 4 |
| max_seq_length / doc_stride | 384 / 128 |
| Hardware and training time | NVIDIA GeForce RTX 4060 Laptop GPU; 140.6 minutes including preparation |

Loss curve: [logs/loss.png](logs/loss.png). Raw losses and data IDs are committed.
Held-out EM/F1: **58.40/60.37**.
Answerable: 45.63/49.54;
unanswerable: 71.37/71.37.
These are local SQuAD measurements, not the instructor's hidden-test score.

## 3. No-answer threshold

Each window has start/end logits. We compare the minimum summed CLS score
across windows with the best valid context-span score. Return null when
`CLS minus span > -1.872282`. We selected this threshold by maximizing
F1 on 500 calibration questions, never the public samples. Too low a threshold
causes excessive abstention; too high produces unsupported spans. The sigmoid
margin score is a heuristic confidence, not a calibrated probability.

## 4. Serving architecture

FastAPI plus uvicorn, one worker. Background startup loads local model/tokenizer
once on CPU. Health stays 503 until ready. Protected requests check the exact
Bearer token from `QA_API_TOKEN` using constant-time comparison, then validate
the JSON body. Overlapping windows handle long contexts; non-context tokens
are masked. Winning token offsets slice the unchanged input. A lock serializes
inference. Errors follow the supplied JSON schema. No remote inference is used.

```powershell
.\setup.ps1
.\train.ps1
# Set QA_API_TOKEN privately in this terminal.
.\run.ps1
.\tools\cloudflared.exe tunnel --url http://127.0.0.1:8000
```

Cloudflare is the primary tunnel. ngrok backup account/setup and instructor
token remain pending. `.env` files are ignored but not loaded automatically.

## 5. Results on the public sample set

| Item | Expected | Your answer | start | Correct? |
|---|---|---|---|---|
| sample-01 | 16, 16 attention heads | null | None | No |
| sample-02 | 3.5 days | 3.5 days | 437 | Yes |
| sample-03 | null | null | None | Yes |
| sample-04 | null | 10,000 times | 263 | No |
| sample-05 | 50,257, 50,257 tokens | 50,257 | 3157 | Yes |

The model returned null for sample-01 even though the context states 16 heads:
its null margin exceeded the independently calibrated threshold. In sample-04,
it returned "10,000 times", confusing a parameter-reduction figure for GPT-3
with a question about BERT-base GPU memory; the requested fact is absent.
These are semantic failures despite valid JSON and offsets. Sample-05's late
answer was found through sliding windows. Public samples were never used to
train or select the threshold. Local and HTTPS predictions agreed (3/5 correct).

## 6. Model size and latency (not graded)

| Item | Value |
|---|---|
| Parameters | 66,364,418 |
| Size on disk (model directory, excluding checkpoints) | 255.4 MiB |
| Mean CPU HTTP latency, 5 samples | 0.297 s |
| Laptop CPU and RAM | 13th Gen Intel(R) Core(TM) i9-13900H; 31.7 GiB |

Repeating the five items ten times took 12.71s
for 50 local HTTP requests (maximum 0.538s).
The five HTTPS requests averaged 0.480s. Authentication
checks passed locally and over HTTPS. These samples do not guarantee the
150-second cap for unseen texts or changing network conditions.

## 7. Problems encountered and how you fixed them

1. **Problem:** no actual learning. **Cause:** scaffold only saved base weights.
   **Fix:** overflow-aware span/CLS labels, Trainer.train(), loss logging and
   provenance written only after successful training.
2. **Problem:** endpoints did not enforce authentication. **Cause:** function
   assigned as a default argument instead of a FastAPI dependency. **Fix:**
   Depends registration, exact Bearer checking and negative authentication tests.

Fix commits (preserved history):
```
8ea964c fix: pin compatible Arrow and verify training provenance
b206e65 docs: add reproducible Windows workflow and evidence-based submission checklist
07e82db fix: enforce QA API contract and bearer authentication
9ab27d3 feat: implement local SQuAD2 fine-tuning and windowed QA
597fad6 merge: docs/report
```

## 8. Decoder investigation

An unsupported-question failure could be addressed with a decoder instructed
to reason about evidence, but it may hallucinate; it still needs abstention
validation. A decoder or encoder–decoder could combine disjoint evidence or
answer yes/no, which our span-only head cannot. Such outputs break this API's
span rule and require a different evaluator. Larger autoregressive models also
increase memory and CPU latency. For long contexts, generation does not remove
input limits: chunking or retrieval is still needed. Our implementation uses
overlapping windows instead and follows the encoder-only constraint.

## 9. Known limitations

English extractive answers only, maximum 30 answer tokens. Questions are
truncated to 64 tokens; context is limited to 5000 characters. The threshold
may not transfer perfectly to the instructor's texts. Network latency, thermal
throttling and concurrency can exceed deadlines. Missing weights/token keep
the service unready. Instructor dry run, backup tunnel, agreed token and final
submission tag must be completed before submission on 31 October 2026.
