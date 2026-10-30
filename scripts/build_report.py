"""Generate the English report from measured evidence; fail if evidence is missing."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
    meta=read('logs/run_metadata.json');val=read('logs/validation.json');sample=read('logs/public_sample_results.json')
    hardware=read('logs/hardware.json')
    service=read('logs/service_verification.json')
    tunnel=read('logs/tunnel_sample_results.json')
    assert meta['completed'] and meta['global_step']>0
    cfg=meta['config'];t=cfg['training'];m=cfg['model'];score=val['held_out']
    table='\n'.join(f"| {r['id']} | {', '.join(r['references']) or 'null'} | {r['prediction']['answer'] or 'null'} | {r['prediction']['start']} | {'Yes' if r['em'] else 'No'} |" for r in sample['rows'])
    model=ROOT/m['output_dir'];size=sum(p.stat().st_size for p in model.iterdir() if p.is_file())
    revisions=subprocess.check_output(['git','log','--format=%h %s','-5'],cwd=ROOT,text=True).strip()
    report=f'''# Project Report — Extractive QA as a Service

## 0. Team

| Field | Value |
|---|---|
| Team id | Pistacho (chosen by team; instructor registration pending) |
| Members | Elías Ventura, Lilly Flores, Andrés Avilés |
| Repository URL | https://github.com/eliasventurv/pistacho-qa-service |
| `submission` commit hash | This version is identified by the `submission` tag; exact hash: `git rev-parse submission` |
| Public service URL used at the dry run | Team self-test: {service['public_url_tested']} (temporary tunnel stopped); instructor dry run pending |
| AI tools used (which, and for what) | Codex: scaffold audit, implementation, tests, local training orchestration and documentation; team must understand and defend code |

## 1. Model choice and justification

We started from **{m['name']}**, a base encoder, not a SQuAD checkpoint. Its six
layers make CPU serving more practical than twelve-layer BERT-base, which we
considered but did not select because of compute and latency. The QA head was
randomly initialized and trained locally. This trades some accuracy for a
smaller model under the five-second HTTP deadline.

## 2. Training

| Item | Value |
|---|---|
| Training data | SQuAD 2.0 train, seeded subset of {meta['train_examples']} questions |
| Validation data | 500 loss-monitoring, 500 calibration, 500 disjoint held-out questions |
| Epochs | {t['epochs']} |
| Learning rate and schedule | {t['learning_rate']}, linear decay, warmup ratio {t['warmup_ratio']} |
| Batch size | {t['batch_size']}, accumulation {t['gradient_accumulation_steps']} |
| max_seq_length / doc_stride | {m['max_seq_length']} / {m['doc_stride']} |
| Hardware and training time | {meta['hardware']}; {meta['training_seconds']/60:.1f} minutes including preparation |

Loss curve: [logs/loss.png](logs/loss.png). Raw losses and data IDs are committed.
Held-out EM/F1: **{score['overall']['exact_match']:.2f}/{score['overall']['f1']:.2f}**.
Answerable: {score['answerable']['exact_match']:.2f}/{score['answerable']['f1']:.2f};
unanswerable: {score['unanswerable']['exact_match']:.2f}/{score['unanswerable']['f1']:.2f}.
These are local SQuAD measurements, not the instructor's hidden-test score.

## 3. No-answer threshold

Each window has start/end logits. We compare the minimum summed CLS score
across windows with the best valid context-span score. Return null when
`CLS minus span > {val['threshold']:.6f}`. We selected this threshold by maximizing
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
.\\setup.ps1
.\\train.ps1
# Set QA_API_TOKEN privately in this terminal.
.\\run.ps1
.\\tools\\cloudflared.exe tunnel --url http://127.0.0.1:8000
```

Cloudflare is the primary tunnel. ngrok backup account/setup and instructor
token remain pending. `.env` files are ignored but not loaded automatically.

## 5. Results on the public sample set

| Item | Expected | Your answer | start | Correct? |
|---|---|---|---|---|
{table}

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
| Parameters | {hardware['params']:,} |
| Size on disk (model directory, excluding checkpoints) | {size/1024**2:.1f} MiB |
| Mean CPU HTTP latency, 5 samples | {sample['mean_seconds']:.3f} s |
| Laptop CPU and RAM | {hardware['cpu']}; {hardware['ram_gb']:.1f} GiB |

Repeating the five items ten times took {service['cpu_benchmark']['total_seconds']:.2f}s
for 50 local HTTP requests (maximum {service['cpu_benchmark']['max_seconds']:.3f}s).
The five HTTPS requests averaged {tunnel['mean_seconds']:.3f}s. Authentication
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
{revisions}
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
'''
    (ROOT/'REPORT.md').write_text(report,encoding='utf-8')

if __name__=='__main__':main()

