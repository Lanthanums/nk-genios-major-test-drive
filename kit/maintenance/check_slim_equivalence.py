"""v4 slim equivalence check: every compressed YAML code node must behave
identically to the full platform_runtime for its fixed op, and no node may
carry empty-string constant inputs (platform validation rule)."""
from pathlib import Path
import importlib.util
import json
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location('rt', ROOT / 'code/platform_runtime.py')
RT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RT)

failures = []


def load_node_handlers(path):
    doc = yaml.safe_load(path.read_text(encoding='utf-8'))
    handlers = {}
    for node in doc['Nodes']:
        if node['Type'] != 'Code':
            continue
        cfg = node['Configs']['Code']
        for iv in cfg.get('InputVariables', []):
            if iv.get('RefType') == 'value' and iv.get('JsonValue') in ('""', "''"):
                failures.append('empty constant input: %s/%s' % (node['Name'], iv['Name']))
        code = cfg.get('Code') or ''
        if not code.startswith('import base64 as _rt_b64'):
            continue
        ns = {}
        exec(compile(code, node['Name'], 'exec'), ns)
        op = next((json.loads(iv['JsonValue']) for iv in cfg['InputVariables']
                   if iv.get('Name') == 'op' and iv.get('RefType') == 'value'), None)
        if op is not None:
            handlers.setdefault(op, []).append((node['Name'], ns['handler']))
    return doc, handlers


def compare(op, params, handlers):
    expected = RT.handler(json.loads(json.dumps(params)))
    got = [h(json.loads(json.dumps(params))) for _, h in handlers.get(op, [])]
    for (name, _), result in zip(handlers.get(op, []), got):
        if result != expected:
            failures.append('MISMATCH op=%s node=%s\n  full=%r\n  node=%r' % (op, name, expected, result))
    return expected


doc, handlers = load_node_handlers(ROOT / 'platform_import/WF_Explore_One_v4.yaml')
print('compressed engine nodes by op:', {k: len(v) for k, v in sorted(handlers.items())})

# --- selection chain (bank ops) ---
r = compare('init_selection', {'op': 'init_selection', 'reported_group_text': '不清楚', 'task_id': 'auto',
                               'session_seed': 'smoke1', 'exclude_case_ids': ''}, handlers)
assert r['action'] in ('need_group', 'known_group'), r
sel = json.loads(r['selection_json'])
assert sel['group_id'] == 'unknown'
r = compare('set_group', {'op': 'set_group', 'selection_json': json.dumps(sel), 'group_id': 'information'}, handlers)
sel = json.loads(r['selection_json'])
r = compare('prepare_cases', {'op': 'prepare_cases', 'selection_json': json.dumps(sel)}, handlers)
assert r['action'] == 'need_activity' and r['group_id'] == 'information'
r = compare('set_activity', {'op': 'set_activity', 'selection_json': json.dumps(sel), 'task_id': 'random'}, handlers)
assert r['action'] == 'menu'
sel2 = json.loads(r['selection_json'])
r = compare('set_activity', {'op': 'set_activity', 'selection_json': json.dumps(sel), 'task_id': 'story'}, handlers)
sel = json.loads(r['selection_json'])
r = compare('select_case', {'op': 'select_case', 'selection_json': json.dumps(sel), 'case_index': -1}, handlers)
state = json.loads(r['state_json'])
assert 'case_snapshot' in state and 'family_snapshot' in state, 'snapshots missing'

# --- in-conversation chain (lean ops) ---
r = compare('hint', {'op': 'hint', 'state_json': json.dumps(state), 'user_text': ''}, handlers)
r = compare('finish', {'op': 'finish', 'state_json': json.dumps(state), 'user_text': ''}, handlers)
assert r['action'] == 'report_gate', r['action']
r = compare('report_cancel', {'op': 'report_cancel', 'state_json': r['state_json'], 'user_text': ''}, handlers)
st = json.loads(r['state_json'])
assert st.get('report_gate') is False
r = compare('report_final', {'op': 'report_final', 'state_json': r['state_json'], 'user_text': '这次体验让我看到自己在意什么', 'skip_reflection': False}, handlers)
assert r['action'] == 'report_ready' and r['report']
r = compare('confirm_record', {'op': 'confirm_record', 'state_json': r['state_json'], 'user_text': '确认记录'}, handlers)
assert r['action'] == 'completed'
r = compare('selection_finish', {'op': 'selection_finish', 'selection_json': json.dumps(sel)}, handlers)
assert r['action'] == 'stopped'

# --- one full evaluated flow per new mode via direct start (full runtime only drives, nodes follow) ---
for cid, task, kind in [('values_research_day', 'values', 'order'),
                        ('hearing_gpu_quota', 'hearing', 'allocation'),
                        ('failure_modeling', 'failure', 'compose')]:
    start = RT.handler({'op': 'start', 'task_id': task, 'case_id': cid, 'group_id': 'unknown',
                        'group_confirmed': False, 'seed': 'smoke2'})
    assert start['ok'] and start['state_json'], start.get('error')
    st = json.loads(start['state_json'])
    case = st['case_snapshot']
    data = case['data']
    if kind == 'order':
        items = case['surface_variants'][st['variant_index']].get('item_ids') or [it['id'] for it in data['items']]
        plan = {'order': items, 'reason': ''}
    elif kind == 'allocation':
        total = data['budget'][0] if isinstance(data['budget'], list) else data['budget']
        step = data.get('min_step', 1)
        ids = [it['id'] for it in data['items']]
        share = total // len(ids) // step * step
        alloc = {i: share for i in ids}
        alloc[ids[0]] += total - sum(alloc.values())
        plan = {'allocation': alloc, 'reason': ''}
    else:
        plan = {'response': '我把那次搞砸的展示重新讲了一遍，先承认准备不足，再说明改进。标题：重来的一次', 'title': '', 'reason': ''}
    prop = compare('propose', {'op': 'propose', 'state_json': json.dumps(st),
                               'candidate_json': json.dumps({'action': 'submit', 'plan': plan, 'quote': 'x'}),
                               'user_text': 'x'}, handlers)
    if not prop['ok']:
        failures.append('propose failed for %s: %s' % (task, prop.get('error')))
        continue
    conf = compare('confirm', {'op': 'confirm', 'state_json': prop['state_json'], 'user_text': '确认'}, handlers)
    if conf['action'] != 'evaluated':
        failures.append('confirm not evaluated for %s: %s' % (task, conf['action']))
        continue
    adv = compare('advance', {'op': 'advance', 'state_json': conf['state_json'], 'user_text': ''}, handlers)
    fin = compare('report', {'op': 'report', 'state_json': adv['state_json'], 'user_text': ''}, handlers)
    assert fin['report']

# --- submit_button on a choice case (display->original mapping must match) ---
start = RT.handler({'op': 'start', 'task_id': 'story', 'case_id': 'story_lab_deadline', 'group_id': 'unknown',
                    'group_confirmed': False, 'seed': 'smoke3'})
st = json.loads(start['state_json'])
btn = compare('submit_button', {'op': 'submit_button', 'state_json': json.dumps(st), 'choice': 'A'}, handlers)
assert btn['ok'], btn
conf = compare('confirm', {'op': 'confirm', 'state_json': btn['state_json'], 'user_text': '确认'}, handlers)
assert conf['action'] == 'evaluated', conf['action']

print('checks run: init/set_group/prepare/set_activityx2/select_case/hint/finish/report_cancel/'
      'report_final/confirm_record/selection_finish + 3 new-mode flows + submit_button flow')
if failures:
    print('FAILURES:', len(failures))
    for f in failures[:10]:
        print(' -', f[:400])
    sys.exit(1)
print('ALL EQUIVALENCE CHECKS PASSED')
