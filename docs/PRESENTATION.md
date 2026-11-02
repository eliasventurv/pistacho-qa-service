# Three-minute pitch and Q&A preparation

> **Outdated draft.** This plan describes the DistilBERT baseline. The submitted
> model is RoBERTa-base; use the figures in REPORT.md when updating the pitch.

Present in English. Replace any pending metric with its measured value before
presenting; never claim results based on the untrained scaffold.

## 0:00–0:40 — Model choice

We fine-tuned distilbert-base-uncased ourselves on SQuAD 2.0. Its six-layer
encoder reduces CPU compute compared with twelve-layer BERT-base. We accepted
some accuracy tradeoff to meet a five-second HTTP deadline on our laptop.
We did not start from a checkpoint already fine-tuned for question answering.

## 0:40–1:25 — Training and evidence

Explain the seeded 40,000-example subset, two epochs, learning rate 3e-5,
batch eight and four accumulation steps. Show logs/loss.png and actual held-out
EM/F1 in logs/validation.json. Explain separate calibration and evaluation
sets, and show the actual selected no-answer threshold.

## 1:25–2:10 — Serving

Trace one request: Bearer token check, Pydantic validation, tokenizer windows,
CPU forward pass, best valid span, CLS comparison, original character offsets,
and JSON response. The model loads once; health stays 503 until ready. One
worker serves the model behind an HTTPS tunnel, without cloud inference.

## 2:10–3:00 — Problems and decoder investigation

The scaffold did not actually train and its token function was not registered
as a dependency. Show the fixes and their commits. Discuss the real public
sample failures, if any. A decoder could generate yes/no or combined answers,
but those would violate this task's contiguous-span contract, increase CPU
latency and require different evaluation. Long inputs still require a context
strategy; generation alone does not remove token limits or hallucinations.

## Individual code questions

- Why CLS? Unanswerable examples (or windows without the labeled span) train
  both boundary labels at CLS; its summed logits compete with valid spans.
- Why minimum null score across windows? One answer-bearing window should be
  able to defeat windows that do not contain the answer.
- Why offsets? Token IDs cannot locate repeated text reliably. Offsets map
  the winning tokens directly into the unchanged original context.
- What does raising the threshold do? The null-score difference must be larger
  to abstain, so a higher threshold produces fewer null answers.
- Why Depends? A default Python function value does not call authentication.
- Why not train on public samples? They are a sanity check; tuning on them
  would overstate generalization. We calibrate with separate SQuAD examples.
- What remains limited? English, contiguous spans up to 30 tokens, questions
  truncated to 64 tokens, imperfect abstention, and CPU/network deadlines.
- Why is the score not a calibrated probability? It is a sigmoid of a logit
  margin around the chosen threshold, used only as a bounded confidence.

Open the repository during practice and identify each answer in code. During
individual Q&A, teammates and AI agents cannot answer for the student.
