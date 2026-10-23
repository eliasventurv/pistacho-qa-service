import json
from pathlib import Path


def main():
    sample_path = Path("docs/public_sample.json")
    if not sample_path.exists():
        print("Sample not found")
        return
    with open(sample_path) as f:
        sample = json.load(f)
    print("Loaded sample:", len(sample["items"]), "items")


if __name__ == "__main__":
    main()
