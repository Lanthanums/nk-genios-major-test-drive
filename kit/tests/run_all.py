"""Run all local checks; no live model, platform, or retrieval calls."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
commands=[[sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p','test_*.py','-v'],
          [sys.executable,'-X','utf8','tests/check_legacy.py','--golden','cases/golden_results.json','--output','tests/legacy_compat_results.json']]
logs=[]
for command in commands:
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    logs.append(result.stdout+result.stderr)
    if result.returncode:
        print(logs[-1]);raise SystemExit(result.returncode)
(ROOT/'tests/local_test_result.txt').write_text('\n'.join(logs),encoding='utf-8')
print(''.join(logs))
