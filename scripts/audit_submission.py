"""Evidence checks for section V. Does not claim hidden-set/oral performance."""
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    meta=read('logs/run_metadata.json');service=read('logs/service_verification.json')
    tests=ET.parse(ROOT/'logs/tests.xml').getroot()
    suites=list(tests.iter('testsuite'))
    failed=sum(int(s.get('failures','0'))+int(s.get('errors','0')) for s in suites)
    checks={
      'base_checkpoint':meta['base_checkpoint']=='distilbert-base-uncased' and bool(meta['base_revision']),
      'completed_local_training':meta.get('completed') is True and meta.get('global_step',0)>0,
      'training_logs_and_curve':all((ROOT/p).is_file() for p in ['logs/training_log.json','logs/loss.png']),
      'tests_passed':failed==0 and sum(int(s.get('tests','0')) for s in suites)>=30,
      'real_auth_checks':len(service['auth_checks'])==8 and all(r['status']==401 for r in service['auth_checks']),
      'no_tracked_token_file':not any(Path(p).name=='.env' for p in tracked),
      'no_tracked_model_weights':not any(p.startswith(('artifacts/','models/','checkpoints/')) or p.endswith('.safetensors') for p in tracked),
      'original_history_preserved':subprocess.run(['git','merge-base','--is-ancestor','597fad611996a0d9547ca1c1175f2ee9acf7c02c','HEAD'],cwd=ROOT).returncode==0,
      'feature_branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='codex/local-training-api-compliance',
    }
    report=(ROOT/'REPORT.md').read_text(encoding='utf-8')
    checks['all_report_headings']=re.findall(r'^## (\d+)\.',report,re.M)==[str(i) for i in range(10)]
    weights=ROOT/'artifacts/distilbert-squad2/model.safetensors'
    with weights.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    result={'section_v_evidence_checks':checks,'all_checks_passed':all(checks.values()),
      'served_weights_sha256':digest,'public_sample_correct':sum(r['em'] for r in read('logs/public_sample_results.json')['rows']),
      'public_sample_count':5,
      'manual_code_review':'Serving loads only local files; no commercial model calls. QA_API_TOKEN comes only from environment. Test tokens are generated in memory.',
      'submission_ready':False,
      'remaining':['Instructor token and registered team name confirmation','Backup ngrok account/configuration and actual tunnel test','Instructor dry run from another network','Pitch and individual Q&A'],
      'limits':'No claim of perfect public-sample accuracy, hidden-set grade, instructor dry-run acceptance or individual Q&A performance.'}
    (ROOT/'logs/compliance_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()

