"""Independent native YAML regression runner; no builder imports."""
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p','test_workflows.py','-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
print(result.stdout+result.stderr)
if result.returncode:raise SystemExit(result.returncode)
report=json.loads((ROOT/'tests/workflow_verification.json').read_text(encoding='utf-8'))
print(json.dumps({k:report[k] for k in ['checks','passed','failed','live_import','live_models','real_retrieval']},ensure_ascii=False))
