"""Evaluate actual HTTP responses; no expected answers are sent to the model."""
import argparse
import json
import os
import time
import requests
from src.metrics import score_answer, summarize
from src.predict import ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8000');args=p.parse_args()
    token=os.environ['QA_API_TOKEN']
    headers={'Authorization':f'Bearer {token}'}
    items=json.loads((ROOT/'docs/public_sample.json').read_text(encoding='utf-8'))['items']
    rows=[]
    for item in items:
        before=time.perf_counter()
        response=requests.post(args.url+'/predict',headers=headers,
            json={k:item[k] for k in ('id','context','question')},timeout=5)
        elapsed=time.perf_counter()-before;response.raise_for_status();pred=response.json()
        assert pred['id']==item['id']
        assert 0<=pred['score']<=1
        assert (pred['answer'] is None)==(pred['start'] is None)
        if pred['answer'] is not None:
            assert isinstance(pred['start'],int) and pred['start']>=0
            assert item['context'][pred['start']:pred['start']+len(pred['answer'])]==pred['answer']
        refs=[a['text'] for a in item['answers']]
        em,f1=score_answer(pred['answer'],refs)
        rows.append({'id':item['id'],'references':refs,'prediction':pred,'em':em,'f1':f1,'seconds':elapsed})
    report={'url':args.url,'metrics':summarize(rows),'mean_seconds':sum(r['seconds'] for r in rows)/len(rows),'rows':rows}
    (ROOT/'logs/public_sample_results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
