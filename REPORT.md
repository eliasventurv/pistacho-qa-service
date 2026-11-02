# Project Report — Extractive QA as a Service

## 0. Team

| Field | Value |
|---|---|
| Team id | `pistacho` |
| Members | Elías Ventura, Lilly Flores, Andrés Avilés |
| Repository URL | https://github.com/eliasventurv/pistacho-qa-service |
| `submission` commit hash | The commit tagged `submission` (`git rev-parse submission`) |
| Public service URL used at the dry run | https://boil-confiding-default.ngrok-free.dev (ngrok fixed domain); Cloudflare Quick Tunnel as backup |
| AI tools used (which, and for what) | Codex: first DistilBERT pipeline, API hardening, tests. Claude Code: RoBERTa retraining setup, threshold calibration changes, evaluation and this report. The team reviewed and can explain the code. |

## 1. Model choice and justification

- **Base checkpoint:** `FacebookAI/roberta-base` (124,056,578 parameters), a base encoder with
  no SQuAD fine-tuning. The QA head (start/end logits) is newly initialized and trained by us.
- **Alternatives considered:**
  - `distilbert-base-uncased`: our first submission. We actually trained it (40k questions,
    2 epochs) and it reached only 58.4 EM / 60.4 F1 on held-out SQuAD 2.0 validation and 3/5 on
    the public samples (evidence in `logs/distilbert-baseline/`). Answerable questions were the
    weak point (45.6 EM), which the 0.70 reference anchor would punish.
  - `deberta-v3-base`: stronger on SQuAD 2.0, but ~184M parameters, a slower CPU forward pass,
    a sentencepiece tokenizer and known fp16 instability on a 6 GB laptop GPU. Too risky for the
    remaining time.
- **Trade-off:** RoBERTa-base doubles DistilBERT's size and CPU cost, but we measured the cost
  before switching: 0.40 s mean and 0.87 s worst case per HTTP request on a laptop CPU, far under
  the 5 s timeout, and 19.9 s for 50 requests against the 150 s global cap. In exchange,
  held-out F1 rose from 60.4 to 83.8. Its byte-level BPE tokenizer is also cased and has no
  `[UNK]` tokens, so spans copied from the context keep exact casing and symbols.

## 2. Training

| Item | Value |
|---|---|
| Training data | Full SQuAD 2.0 train: 130,319 questions → 131,821 windows |
| Validation data | SQuAD 2.0 validation shuffled with seed 42: `[4000:4500]` for loss monitoring, `[0:2000]` for threshold calibration, `[2000:4000]` held out for reporting |
| Epochs | 2 (8,238 optimizer steps) |
| Learning rate and schedule | 3e-5, linear decay, 10 % warmup, weight decay 0.01 |
| Batch size | 8 per step × 4 gradient accumulation = 32 effective |
| `max_seq_length` / `doc_stride` | 384 / 128 |
| Hardware and training time | NVIDIA RTX 4050 Laptop GPU (6 GB), fp16; 112 min including tokenization |

- **Loss curve:** [logs/loss.png](logs/loss.png); raw values in `logs/training_log.json`,
  data IDs and base revision in `logs/run_metadata.json`.
  Validation loss fell from 1.25 (step 500) to 0.81 (step 3,500) and ended at 0.85. The slight
  rise during epoch 2 is a mild overfitting signal, so we stopped at 2 epochs.
- **Validation results:** held-out (2,000 questions) **81.25 EM / 83.77 F1**.
  Answerable: 76.76 EM / 81.73 F1; unanswerable: 85.84 EM. The calibration slice gave
  80.90 / 83.61, so the threshold did not overfit its own slice.
  These are SQuAD measurements, not the instructor's hidden-test score.

## 3. No-answer threshold

- Every window yields start/end logits. The null score is the start+end logit at `<s>` (CLS),
  taking the minimum across windows; the best span score is the maximum start+end over valid
  context tokens (end ≥ start, ≤ 30 tokens, question and padding masked). We return `null` when
  `null_score − best_span_score > threshold`.
- We swept every distinct score difference on the 2,000 calibration questions and kept the
  value that maximized F1: **−1.779**. The public samples were never used for selection.
  Calibration was raised from 500 to 2,000 questions in this version to make the value more stable.
- A threshold set too low returns `null` too often and loses answerable questions. Set too high,
  it answers unanswerable questions with plausible but unsupported spans. The hidden set is about
  25 % unanswerable, versus about 50 % in SQuAD validation. We kept the F1-optimal value rather
  than guess a shift for the hidden set.

## 4. Serving architecture

- **Framework and server:** FastAPI + uvicorn, 1 worker, CPU only, 4 torch threads.
- **Model loading:** at startup, a background task loads tokenizer and weights from
  `artifacts/roberta-squad2/` with `local_files_only=True`. It refuses weights without a
  completed-training provenance file. `/health` returns 503 `loading` until the model is ready.
- **Request flow:** Pydantic validates the body (strict types, length limits, no extra fields;
  otherwise 422 `bad_request`). The context is split into 384-token windows with a 128-token
  stride, which covers contexts longer than 512 tokens. Windows are batched (8 at a time) under
  `torch.inference_mode`, and a lock serializes inference. The best span is mapped back to
  character offsets and sliced from the unchanged context, so `context[start:start+len(answer)] == answer`
  holds by construction. Score is a sigmoid of the margin to the threshold.
- **Access control:** a FastAPI `Depends(verify_token)` on `/info` and `/predict` compares the
  `Authorization: Bearer` value with `QA_API_TOKEN` read from the environment, using
  `hmac.compare_digest`; a missing or wrong token gives 401 `{"error":"unauthorized"}`.
  The token is never in code or git (`.env` is ignored).
- **Tunnel:** ngrok with the account's fixed domain; Cloudflare Quick Tunnel as backup.
- **How to run:**

```powershell
.\setup.ps1                          # venv + CUDA torch + pinned requirements (or Python 3.10/3.12 venv + requirements.txt)
# put the trained model in artifacts/roberta-squad2/ (GitHub release asset), or run .\train.ps1
$env:QA_API_TOKEN = "<team token>"   # set privately in this terminal
.\run.ps1                            # uvicorn app:app on 127.0.0.1:8000
ngrok http 8000                      # second terminal → https://boil-confiding-default.ngrok-free.dev
```

## 5. Results on the public sample set

| Item | Expected | Your answer | `start` | Correct? |
|---|---|---|---|---|
| sample-01 | 16, 16 attention heads | 16 | 383 | Yes |
| sample-02 | 3.5 days | 3.5 days | 437 | Yes |
| sample-03 | `null` | `null` | `null` | Yes |
| sample-04 | `null` | `null` | `null` | Yes |
| sample-05 | 50,257, 50,257 tokens | 50,257 | 3157 | Yes |

5/5 exact match through real HTTP requests (`logs/public_sample_results.json`). DistilBERT
failed two of these. On sample-01 it returned a false `null`. On sample-04 it returned
"10,000 times", a figure about GPT-3 parameter reduction, for a question whose fact is absent.
RoBERTa fixed both. Sample-05's answer is at character 3157, beyond the first window, and was
found by the sliding windows.

## 6. Model size and latency (not graded)

| Item | Value |
|---|---|
| Parameters | 124,056,578 |
| Size on disk | 482 MiB (fp32 safetensors + tokenizer) |
| Mean latency per `/predict` request on your laptop (CPU) | 0.40 s (50 local HTTP requests: 19.9 s total, max 0.87 s) |
| Laptop CPU and RAM | 13th Gen Intel Core i7-13620H, 16 GB |

The tunnel adds network round-trip time on top of these numbers (to be measured at the dry run).

## 7. Problems encountered and how you fixed them

1. **Problem:** the first model scored too low (58.4 EM held-out, 3/5 public). **Cause:**
   DistilBERT trained on a 40k subset; answerable questions only reached 45.6 EM. **Fix:** measured
   GPU throughput and CPU latency for RoBERTa-base first, then retrained on all 130k questions.
   Held-out EM rose to 81.25, public samples to 5/5. **Commit:** `8c78b22`.
2. **Problem:** the threshold was chosen on only 500 questions. **Cause:** a small calibration slice makes
   the F1-optimal value noisy and the held-out estimate wide. **Fix:** 2,000 calibration and 2,000
   held-out questions, with loss monitoring moved to a further disjoint slice. **Commit:** `8c78b22`.
3. **Problem:** endpoints did not enforce authentication. **Cause:** the check was a default
   argument, not a FastAPI dependency. **Fix:** `Depends(verify_token)` with exact Bearer
   comparison, plus negative tests. **Commit:** `07e82db`.

## 8. Decoder investigation

- **Unsupported answers (DistilBERT, sample-04).** The span head returned "10,000 times", a
  related number from the wrong model. A decoder prompted to quote evidence before answering
  could reject it, but it can also hallucinate a fluent answer. It would still need a calibrated
  abstention rule, and free text breaks the `context[start:...] == answer` contract. Our fix
  stayed encoder-side: a stronger encoder plus a better-calibrated null threshold.
- **Lists and yes/no.** Our head can only return one contiguous span, at most 30 tokens. It cannot
  answer "yes" or "no", or join two separate facts. An encoder–decoder such as T5 can generate
  those, at the cost of exact-match evaluation and offsets.
- **Long contexts.** A 5,000-character context needs several 384-token windows, and each window
  scores its spans independently. A long-context decoder could read the whole text at once, but on
  a laptop CPU, generating token by token with a model of 1B+ parameters would likely break the
  5 s timeout. RoBERTa answers in about 0.4 s.
- **Cost.** Decoders also cost more memory, and LoRA would be needed even to fine-tune them on
  our 6 GB GPU.

## 9. Known limitations

- English, single contiguous spans of at most 30 tokens. No yes/no answers, lists, or
  arithmetic.
- Questions are truncated to 64 tokens. Context is limited to 5,000 characters (longer → 422).
- The threshold was calibrated on SQuAD (about 50 % unanswerable). The instructor's texts
  (about 25 % unanswerable, not from Wikipedia) may shift the optimum.
- The model scores each window independently: distractor facts in another window can win.
- Inference is serialized (one request at a time). Heavy parallel load would queue requests.
  Tunnel latency or a laptop slowed by heat could approach the deadlines.
- Without the weights or `QA_API_TOKEN`, `/health` stays 503 and nothing is served.
