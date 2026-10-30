"""Keep download caches inside the project; never store API credentials here."""
import os
from pathlib import Path
os.environ.setdefault('HF_HOME', str(Path(__file__).resolve().parents[1]/'.cache/huggingface'))
