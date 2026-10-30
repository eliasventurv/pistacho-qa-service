"""Create a portable archive, preserving Git history and excluding credentials."""
import argparse
import subprocess
import tempfile
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--include-weights',action='store_true');args=parser.parse_args()
    files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    target=ROOT/'pistacho-delivery.zip'
    with tempfile.TemporaryDirectory() as temporary:
        bundle=Path(temporary)/'history.bundle'
        subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=ROOT,check=True)
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
            z.write(bundle,'history.bundle')
            for name in files:
                if name and (ROOT/name).is_file():
                    if name=='.env' or name.startswith(('.venv/','tools/','artifacts/')):
                        raise ValueError('Unexpected private/runtime file tracked in Git: '+name)
                    z.write(ROOT/name,name)
            if args.include_weights:
                model=ROOT/'artifacts/distilbert-squad2'
                if not (model/'training_provenance.json').exists(): raise ValueError('No trained model')
                for file in model.iterdir():
                    if file.is_file(): z.write(file,file.relative_to(ROOT))
    print(target)

if __name__=='__main__':main()
