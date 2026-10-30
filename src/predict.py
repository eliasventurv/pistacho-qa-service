"""Local QA with overlapping windows and CLS no-answer scores."""
import math
import json
from pathlib import Path
import numpy as np
import torch
import yaml
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]

def load_config(path=None):
    with open(path or ROOT / 'configs/default.yaml', encoding='utf-8') as f:
        return yaml.safe_load(f)

def tokenize_for_qa(examples, tokenizer, max_seq_length=384, doc_stride=128):
    questions = [tokenizer.decode(tokenizer.encode(q.strip(), add_special_tokens=False)[:64],
                                  skip_special_tokens=True) for q in examples['question']]
    return tokenizer(questions, examples['context'], max_length=max_seq_length,
                     truncation='only_second', stride=doc_stride,
                     return_overflowing_tokens=True, return_offsets_mapping=True,
                     padding='max_length')

def decode_windows(context, features, start_logits, end_logits, tokenizer, max_answer_length=30):
    best_score, best_span, null_score = -float('inf'), None, float('inf')
    for i, (starts, ends) in enumerate(zip(start_logits, end_logits)):
        ids, offsets = features['input_ids'][i], features['offset_mapping'][i]
        cls = ids.index(tokenizer.cls_token_id)
        null_score = min(null_score, float(starts[cls] + ends[cls]))
        valid = np.array([s == 1 and b > a for s, (a, b) in
                          zip(features.sequence_ids(i), offsets)])
        s_order = np.argsort(np.where(valid, starts, -np.inf))[-20:]
        e_order = np.argsort(np.where(valid, ends, -np.inf))[-20:]
        for s in s_order:
            for e in e_order:
                if not valid[s] or not valid[e] or e < s or e-s+1 > max_answer_length:
                    continue
                score = float(starts[s] + ends[e])
                if score > best_score:
                    best_score, best_span = score, (offsets[s][0], offsets[e][1])
    if best_span is None:
        return {'answer': None, 'start': None, 'null_diff': 1e6}
    a, b = best_span
    return {'answer': context[a:b], 'start': a, 'null_diff': null_score-best_score}

def apply_threshold(raw, threshold):
    no_answer = raw['answer'] is None or raw['null_diff'] > threshold
    margin = max(-60., min(60., raw['null_diff'] - threshold))
    p_null = 1 / (1 + math.exp(-margin))
    return {'answer': None if no_answer else raw['answer'],
            'start': None if no_answer else raw['start'],
            'score': p_null if no_answer else 1-p_null}

class QAPredictor:
    def __init__(self, config=None, device='cpu'):
        self.config = config or load_config()
        path = ROOT / self.config['model']['output_dir']
        if not (path / 'training_provenance.json').is_file():
            raise RuntimeError('Trained model missing. Run python -m src.train first.')
        provenance = json.loads((path / 'training_provenance.json').read_text(encoding='utf-8'))
        if not provenance.get('completed') or provenance.get('global_step', 0) <= 0:
            raise RuntimeError('Model does not have evidence of completed fine-tuning.')
        if provenance.get('base_checkpoint') != self.config['model']['name']:
            raise RuntimeError('Model provenance and configured base checkpoint disagree.')
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.model = AutoModelForQuestionAnswering.from_pretrained(path, local_files_only=True)
        self.device = torch.device(device)
        self.model.to(self.device).eval()
        self.params = sum(p.numel() for p in self.model.parameters())

    def raw_predict(self, context, question):
        cfg = self.config['model']
        features = tokenize_for_qa({'context': [context], 'question': [question]}, self.tokenizer,
                                   cfg['max_seq_length'], cfg['doc_stride'])
        starts, ends = [], []
        with torch.inference_mode():
            for first in range(0, len(features['input_ids']), 8):
                inputs = {k: torch.tensor(v[first:first+8], device=self.device)
                          for k, v in features.items() if k in self.tokenizer.model_input_names}
                outputs = self.model(**inputs)
                starts.extend(outputs.start_logits.float().cpu().numpy())
                ends.extend(outputs.end_logits.float().cpu().numpy())
        return decode_windows(context, features, starts, ends, self.tokenizer)

    def predict(self, context, question):
        return apply_threshold(self.raw_predict(context, question),
                               self.config['threshold']['selected_threshold'])
