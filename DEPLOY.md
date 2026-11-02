# Deployment on Windows

## Local service

Use Python 3.12 and `setup.ps1`. Train with `train.ps1`, or copy the **entire**
trained `artifacts/roberta-squad2/` directory from this laptop. It must include
the tokenizer, safetensors, model config and training provenance. Do not commit
weights. The service does not fetch a missing model from the Internet.

Set `QA_API_TOKEN` in the current PowerShell session to the agreed token;
then run `run.ps1`. The environment variable is the only token source. An `.env`
file is not loaded automatically. Use one worker to avoid duplicating memory.

## Backup tunnel: Cloudflare Quick Tunnel

Install cloudflared from Cloudflare's official distribution, then run:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Use the HTTPS address printed by cloudflared. It changes after restart. The
model still runs on this laptop. Keep service and tunnel processes running.

## Primary tunnel: ngrok (fixed domain)

Install ngrok from its official distribution. Configure your account privately
with `ngrok config add-authtoken`; do not put the ngrok credential in Git.
The free account has a fixed domain, so the URL does not change on restart:

```powershell
ngrok http 8000   # -> https://boil-confiding-default.ngrok-free.dev
```

A backup is only verified after making real requests through its public URL.
Installing the executable alone does not prove that the backup works.

## Verify locally and through the tunnel

Run the same checks against each public URL. Missing/wrong bearer tokens must
return 401 for both protected endpoints. A valid token must return `/info` and
predictions. Health is public and must return 200 only after the model loads.

```powershell
curl.exe -i http://127.0.0.1:8000/health
curl.exe -i http://127.0.0.1:8000/info
.\.venv\Scripts\python.exe -m scripts.eval_sample --url https://YOUR-TUNNEL-HOST
```

The evaluation script reads QA_API_TOKEN from the environment. It sends only
id/context/question, checks spans and records latency and scores. The official
limits are **5 seconds per request** and **150 seconds for 50 requests**.
Repeat the tunnel checks from a phone on mobile data or another network before
the dry run. Keep the laptop plugged in and awake during the presentation.

Send the verified URL to the instructor yourself. Update it after tunnel restart.
Only create/push the `submission` tag after the report, training evidence and
dry run are complete. Preserve the original history and work on the feature
branch; do not overwrite main or squash the history.
