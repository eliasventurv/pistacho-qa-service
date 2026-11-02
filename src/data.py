from pathlib import Path
import json
from datasets import load_dataset

ROOT=Path(__file__).resolve().parents[1]
DATASET_REVISION='3ffb306f725f7d2ce8394bc1873b24868140c412'

def load_squad_v2():
    return load_dataset('rajpurkar/squad_v2', revision=DATASET_REVISION,
                        cache_dir=str(ROOT/'.cache/datasets'))

def save_raw():
    ds=load_squad_v2()
    output=ROOT/'data/raw';output.mkdir(parents=True,exist_ok=True)
    for split in ['train','validation']:
        (output/f'{split}.json').write_text(json.dumps(ds[split].to_list(),ensure_ascii=False),encoding='utf-8')
    return ds

def prepare_splits(val_holdout=500,seed=42):
    ds=load_squad_v2();val=ds['validation'].shuffle(seed=seed)
    return ds['train'],val.select(range(val_holdout)),val.select(range(val_holdout,len(val)))
