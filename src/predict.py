from transformers import AutoTokenizer
import yaml
from pathlib import Path


def load_config(path="configs/default.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_tokenizer(model_name=None, config_path="configs/default.yaml"):
    cfg = load_config(config_path)
    model_name = model_name or cfg["model"]["name"]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return tokenizer


def tokenize_for_qa(examples, tokenizer, max_seq_length=384, doc_stride=128):
    questions = [q.strip() for q in examples["question"]]
    inputs = tokenizer(
        questions,
        examples["context"],
        max_length=max_seq_length,
        truncation="only_second",
        stride=doc_stride,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )
    return inputs
