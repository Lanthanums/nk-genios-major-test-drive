"""Regenerate embedded runtime/YAML from the editable versioned configuration."""
from pathlib import Path
import json
import runpy
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'code/engine_source.py').read_text(encoding='utf-8')
bank=json.loads((ROOT/'config/case_bank.json').read_text(encoding='utf-8'))
catalog=json.loads((ROOT/'config/major_groups.json').read_text(encoding='utf-8'))
source=source.replace('BANK = {}  # Standalone builder embeds case_bank.json here.','BANK = '+repr(bank))
source=source.replace('CATALOG = {}  # Standalone builder embeds user-provided major_groups.json here.','CATALOG = '+repr(catalog))
source=source.replace('CASE_VERSION = ""  # Builder embeds case_bank.json case_version; works without full BANK.','CASE_VERSION = '+repr(bank['case_version']))
source=source.replace('FAMILY_NAMES = {}  # Builder embeds {family_id: display name}; works without full BANK.','FAMILY_NAMES = '+repr({k:v['name'] for k,v in bank['families'].items()}))
(ROOT/'code/engine.py').write_text(source,encoding='utf-8')
runpy.run_path(str(ROOT/'maintenance/build_workflows.py'),run_name='__main__')
(ROOT/'code/hiagent_node.py').write_text((ROOT/'code/platform_runtime.py').read_text(encoding='utf-8'),encoding='utf-8')
print('Rebuilt runtime and 4 native YAML files; rerun tests and refresh the release manifest after edits.')
