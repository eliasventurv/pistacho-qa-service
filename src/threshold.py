from pathlib import Path
import yaml
import json


def load_config(path="configs/default.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def sweep_threshold(scores_and_labels):
    # Placeholder: sweep null vs span scores
    cfg = load_config()
    best = cfg["threshold"]["selected_threshold"]
    return best


def update_threshold(config_path="configs/default.yaml", threshold=0.0):
    cfg = load_config(config_path)
    cfg["threshold"]["selected_threshold"] = float(threshold)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)
    return threshold
