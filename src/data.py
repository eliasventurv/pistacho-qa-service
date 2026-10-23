from pathlib import Path
import json
from datasets import load_dataset


def load_squad_v2():
    dataset = load_dataset("squad_v2")
    return dataset


def save_raw():
    ds = load_squad_v2()
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    for split in ["train", "validation"]:
        with open(data_dir / f"{split}.json", "w", encoding="utf-8") as f:
            json.dump(ds[split].to_list(), f, ensure_ascii=False)
    return ds


def prepare_splits(val_holdout=2000, seed=42):
    ds = load_squad_v2()
    train = ds["train"]
    val = ds["validation"]
    # simple held-out split from validation for threshold tuning
    val = val.shuffle(seed=seed)
    val_tune = val.select(range(min(val_holdout, len(val))))
    val_test = val.select(range(min(val_holdout, len(val)), len(val)))
    return train, val_tune, val_test
