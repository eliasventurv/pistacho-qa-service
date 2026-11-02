"""Tune on validation[0:2000], report on disjoint validation[2000:4000]."""
import argparse
import json
import numpy as np
import torch
import yaml
from src.data import load_squad_v2
from src.metrics import score_answer, summarize
from src.predict import ROOT, QAPredictor, apply_threshold

def sweep_threshold(rows):
    values = np.array([r['raw']['null_diff'] for r in rows])
    candidates = np.unique(np.r_[values.min()-1, values, values.max()+1, 0.])
    scored = []
    for threshold in candidates:
        metrics = [score_answer(apply_threshold(r['raw'], float(threshold))['answer'], r['references']) for r in rows]
        scored.append((sum(x[1] for x in metrics), sum(x[0] for x in metrics), -abs(threshold), threshold))
    return float(max(scored)[-1])

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--device', default='cpu'); args=parser.parse_args()
    torch.set_num_threads(4)
    predictor=QAPredictor(device=args.device)
    ds=load_squad_v2()['validation'].shuffle(seed=predictor.config['training']['seed']).select(range(4000))
    rows=[]
    for i, item in enumerate(ds):
        rows.append({'id':item['id'],'references':item['answers']['text'],
                     'raw':predictor.raw_predict(item['context'],item['question'])})
        if (i+1)%50==0: print(f'Validation {i+1}/{len(ds)}',flush=True)
    threshold=sweep_threshold(rows[:2000])
    for row in rows:
        row['prediction']=apply_threshold(row['raw'],threshold)
        row['em'],row['f1']=score_answer(row['prediction']['answer'],row['references'])
    cfg=predictor.config;cfg['threshold']['selected_threshold']=threshold
    (ROOT/'configs/default.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False),encoding='utf-8')
    report={'threshold':threshold,'calibration':summarize(rows[:2000]),'held_out':summarize(rows[2000:]),'rows':rows}
    (ROOT/'logs/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))

if __name__=='__main__': main()
