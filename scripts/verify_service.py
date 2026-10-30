"""Run genuine CPU HTTP tests with a temporary, unlogged environment token."""
import argparse
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--tunnel',action='store_true');p.add_argument('--benchmark',action='store_true');args=p.parse_args()
    env=os.environ.copy();env['QA_API_TOKEN']=secrets.token_urlsafe(32)
    headers={'Authorization':'Bearer '+env['QA_API_TOKEN']}
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    server_log=(logs/'service.out').open('w',encoding='utf-8')
    server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port','8000','--workers','1'],cwd=ROOT,env=env,stdout=server_log,stderr=subprocess.STDOUT)
    tunnel=None;tunnel_log=None
    try:
        url='http://127.0.0.1:8000'
        for _ in range(120):
            if server.poll() is not None:raise RuntimeError('Service failed: see logs/service.out')
            try:
                if requests.get(url+'/health',timeout=2).status_code==200:break
            except requests.RequestException:pass
            time.sleep(.5)
        else:raise RuntimeError('Model readiness timeout')
        info=requests.get(url+'/info',headers=headers,timeout=5);info.raise_for_status()
        hardware=json.loads((logs/'hardware.json').read_text(encoding='utf-8-sig'))
        hardware['params']=info.json()['params']
        (logs/'hardware.json').write_text(json.dumps(hardware,indent=2),encoding='utf-8')
        summary={'info':info.json(),'local_url':url,'auth_checks':[]}
        item=json.loads((ROOT/'docs/public_sample.json').read_text(encoding='utf-8'))['items'][0]
        body={k:item[k] for k in ['id','context','question']}
        def check_auth(base):
            for endpoint in ['/info','/predict']:
                for h in [{},{'Authorization':'Bearer invalid'}]:
                    r=requests.get(base+endpoint,headers=h,timeout=5) if endpoint=='/info' else requests.post(base+endpoint,headers=h,json=body,timeout=5)
                    assert r.status_code==401 and r.json()['error']=='unauthorized'
                    summary['auth_checks'].append({'url':base,'endpoint':endpoint,'status':r.status_code})
        check_auth(url)
        subprocess.run([sys.executable,'-m','scripts.eval_sample','--url',url],cwd=ROOT,env=env,check=True)
        if args.benchmark:
            items=json.loads((ROOT/'docs/public_sample.json').read_text(encoding='utf-8'))['items']
            timings=[];started=time.perf_counter()
            with requests.Session() as session:
                for i in range(50):
                    entry=items[i%len(items)];before=time.perf_counter()
                    r=session.post(url+'/predict',headers=headers,json={k:entry[k] for k in ['id','context','question']},timeout=5)
                    r.raise_for_status();timings.append(time.perf_counter()-before)
            summary['cpu_benchmark']={'requests':50,'total_seconds':time.perf_counter()-started,'max_seconds':max(timings),'mean_seconds':sum(timings)/50,'seconds':timings}
        if args.tunnel:
            tunnel_log=(logs/'tunnel.out').open('w',encoding='utf-8')
            binary=ROOT/'tools/cloudflared-verified.exe'
            if not binary.is_file():binary=ROOT/'tools/cloudflared.exe'
            tunnel=subprocess.Popen([str(binary),'tunnel','--url',url,'--protocol','http2'],cwd=ROOT,stdout=tunnel_log,stderr=subprocess.STDOUT)
            public=None
            for _ in range(120):
                if tunnel.poll() is not None:raise RuntimeError('Tunnel failed: see logs/tunnel.out')
                text=(logs/'tunnel.out').read_text(encoding='utf-8',errors='replace')
                match=re.search(r'https://[a-z0-9-]+\.trycloudflare\.com',text)
                if match:
                    public=match.group()
                    try:
                        if requests.get(public+'/health',timeout=5).status_code==200:break
                    except requests.RequestException:pass
                time.sleep(1)
            else:raise RuntimeError('Public tunnel readiness timeout')
            check_auth(public)
            local_result=(logs/'public_sample_results.json').read_text(encoding='utf-8')
            try:
                subprocess.run([sys.executable,'-m','scripts.eval_sample','--url',public],cwd=ROOT,env=env,check=True)
                (logs/'tunnel_sample_results.json').write_text((logs/'public_sample_results.json').read_text(encoding='utf-8'),encoding='utf-8')
            finally:
                (logs/'public_sample_results.json').write_text(local_result,encoding='utf-8')
            summary['public_url_tested']=public
            summary['public_tunnel_note']='Temporary test tunnel; stopped after verification. Not the instructor dry run.'
        (logs/'service_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(summary,indent=2))
    finally:
        for process in [tunnel,server]:
            if process and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        server_log.close()
        if tunnel_log:tunnel_log.close()

if __name__=='__main__':main()
