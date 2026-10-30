"""Reproducible SQuAD2 fine-tuning from a BASE encoder (never a QA checkpoint)."""
import argparse
import json
import platform
import subprocess
import time
from pathlib import Path
import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, Trainer, TrainerCallback, TrainingArguments, set_seed
from src.data import load_squad_v2
from src.predict import ROOT, load_config, tokenize_for_qa

BASE_MODELS = {'distilbert-base-uncased', 'distilbert/distilbert-base-uncased', 'bert-base-uncased'}

def prepare_features(examples, tokenizer, length=384, stride=128):
    encoded = tokenize_for_qa(examples, tokenizer, length, stride)
    mapping = encoded.pop('overflow_to_sample_mapping')
    offsets = encoded.pop('offset_mapping')
    starts, ends = [], []
    for i, offset in enumerate(offsets):
        cls = encoded['input_ids'][i].index(tokenizer.cls_token_id)
        answer = examples['answers'][mapping[i]]
        context = [j for j, sid in enumerate(encoded.sequence_ids(i)) if sid == 1]
        if not context or not answer['answer_start']:
            starts.append(cls); ends.append(cls); continue
        a = answer['answer_start'][0]
        b = a + len(answer['text'][0])
        left, right = context[0], context[-1]
        if offset[left][0] > a or offset[right][1] < b:
            starts.append(cls); ends.append(cls); continue
        while left <= context[-1] and offset[left][0] <= a:
            left += 1
        while right >= context[0] and offset[right][1] >= b:
            right -= 1
        starts.append(left-1); ends.append(right+1)
    encoded['start_positions'], encoded['end_positions'] = starts, ends
    return encoded

class SaveLogs(TrainerCallback):
    def on_log(self, args, state, control, **kwargs):
        path = ROOT / 'logs/training_log.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(state.log_history, indent=2), encoding='utf-8')

def plot_loss(history):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8,4))
    for key, label in [('loss','Train'), ('eval_loss','Validation')]:
        rows = [r for r in history if key in r]
        if rows:
            ax.plot([r['step'] for r in rows], [r[key] for r in rows], label=label)
    ax.set(xlabel='Optimizer step', ylabel='QA cross-entropy loss', title='Pistacho: local SQuAD 2.0 fine-tuning')
    ax.legend(); fig.tight_layout(); fig.savefig(ROOT/'logs/loss.png', dpi=160); plt.close(fig)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default=str(ROOT/'configs/default.yaml'))
    p.add_argument('--max_train_samples', type=int)
    p.add_argument('--epochs', type=float)
    p.add_argument('--max_steps', type=int, default=-1)
    p.add_argument('--resume', default=None)
    args = p.parse_args()
    cfg = load_config(args.config); m, t = cfg['model'], cfg['training']
    if m['name'] not in BASE_MODELS:
        raise ValueError('Use an approved BASE encoder, not a SQuAD-fine-tuned checkpoint.')
    set_seed(t['seed']); torch.set_num_threads(4)
    output = ROOT / m['output_dir']; output.mkdir(parents=True, exist_ok=True)
    logs = ROOT / 'logs'; logs.mkdir(exist_ok=True)
    started = time.time()
    ds = load_squad_v2()
    count = args.max_train_samples or t['max_train_samples'] or len(ds['train'])
    train = ds['train'].shuffle(seed=t['seed']).select(range(min(count, len(ds['train']))))
    val = ds['validation'].shuffle(seed=t['seed']).select(range(1000, 1500))
    tokenizer = AutoTokenizer.from_pretrained(m['name'], use_fast=True)
    model = AutoModelForQuestionAnswering.from_pretrained(m['name'], use_safetensors=True)
    def prepare(batch):
        return prepare_features(batch, tokenizer, m['max_seq_length'], m['doc_stride'])
    train_features = train.map(prepare, batched=True, remove_columns=train.column_names)
    val_features = val.map(prepare, batched=True, remove_columns=val.column_names)
    metadata = dict(base_checkpoint=m['name'], base_revision=getattr(model.config,'_commit_hash',None),
        dataset='squad_v2', train_examples=len(train), validation_examples=len(val),
        train_features=len(train_features), seed=t['seed'], config=cfg,
        hardware=torch.cuda.get_device_name(0) if torch.cuda.is_available() else platform.processor(),
        torch_version=torch.__version__, python_version=platform.python_version(),
        command_args=vars(args), train_ids=list(train['id']), validation_ids=list(val['id']))
    try:
        metadata['source_commit'] = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        metadata['source_commit'] = None
    (logs/'run_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    ta = TrainingArguments(output_dir=str(output/'checkpoints'),
        num_train_epochs=args.epochs or t['epochs'], max_steps=args.max_steps,
        per_device_train_batch_size=t['batch_size'], per_device_eval_batch_size=8,
        gradient_accumulation_steps=t['gradient_accumulation_steps'], learning_rate=float(t['learning_rate']),
        warmup_ratio=t['warmup_ratio'], weight_decay=0.01, fp16=torch.cuda.is_available(),
        logging_steps=20, save_strategy='steps', save_steps=250, save_total_limit=2,
        eval_strategy='steps', eval_steps=250, report_to=[], seed=t['seed'],
        dataloader_num_workers=0, disable_tqdm=True)
    trainer = Trainer(model=model,args=ta,train_dataset=train_features,
        eval_dataset=val_features,tokenizer=tokenizer,callbacks=[SaveLogs()])
    result = trainer.train(resume_from_checkpoint=args.resume)
    trainer.save_model(output); tokenizer.save_pretrained(output)
    trainer.save_state()
    metadata.update(training_seconds=time.time()-started, global_step=trainer.state.global_step,
                    metrics=result.metrics, completed=True)
    # This file is only created AFTER successful fine-tuning, never for a base model.
    (output/'training_provenance.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    (logs/'run_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    plot_loss(trainer.state.log_history)
    print('TRAINING_COMPLETE', json.dumps(result.metrics), flush=True)

if __name__ == '__main__':
    main()
