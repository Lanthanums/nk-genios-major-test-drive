"""Compare v2 legacy fixtures with the existing kit's golden numeric results.

Usage: python legacy_compat_test.py --golden PATH --output evidence.json
No business rules are imported from legacy code, only recorded expected results.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def runtime():
    spec=importlib.util.spec_from_file_location('v2_legacy_test_runtime',ROOT.parent/'code'/'engine.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIELDS={
    'route':['valid','minutes','reference_min_minutes'],
    'sensor':['valid','tp','fp','fn','tn','sample_count','false_alarm_weight','miss_weight','loss'],
    'control':['valid','gain','target','trajectory','controls','final_abs_error','max_overshoot','within_observation_settled_step','meets_teaching_target'],
}


def equal(actual,expected,path='result'):
    if isinstance(expected,list):
        if not isinstance(actual,list) or len(actual)!=len(expected):
            raise AssertionError(path+' array length differs')
        for index,(a,e) in enumerate(zip(actual,expected)):
            equal(a,e,path+'['+str(index)+']')
    elif isinstance(expected,bool) or expected is None:
        if actual is not expected:raise AssertionError('%s: %r != %r'%(path,actual,expected))
    elif isinstance(expected,(int,float)):
        if isinstance(actual,bool) or not isinstance(actual,(int,float)) or not math.isclose(actual,expected,rel_tol=0,abs_tol=1e-6):
            raise AssertionError('%s: %r != %r'%(path,actual,expected))
    elif actual!=expected:raise AssertionError('%s: %r != %r'%(path,actual,expected))


def run(golden_path):
    golden_path=Path(golden_path)
    encoded=golden_path.read_bytes()
    cases=json.loads(encoded.decode('utf-8-sig'))
    engine=runtime();records=[]
    if {c['task_id'] for c in cases}!={'route','sensor','control'}:
        raise AssertionError('Golden fixtures must contain the original three tasks')
    for case in cases:
        task=case['task_id'];cid=engine.DEFAULTS[task]
        stages=[('base_result','base_plan',0),('challenge_result','base_plan',1),('revision_result','revision_plan',1)]
        for result_key,plan_key,phase in stages:
            expected=case[result_key];actual=engine.evaluate(cid,case[plan_key],phase)
            checked=[]
            for field in FIELDS[task]:
                if field not in expected:raise AssertionError('Golden snapshot missing '+task+'.'+field)
                equal(actual[field],expected[field],task+'.'+result_key+'.'+field)
                checked.append(field)
            records.append({'task_id':task,'case_id':cid,'snapshot':result_key,'phase':phase,'passed':True,'checked_fields':checked})
    if len(records)!=9:raise AssertionError('Expected exactly nine original snapshots')
    return {'kind':'local_legacy_numeric_comparison','golden_file':golden_path.name,'golden_sha256':hashlib.sha256(encoded).hexdigest(),'engine_version':engine.ENGINE_VERSION,'snapshots_passed':len(records),'snapshots_total':9,'absolute_numeric_tolerance':1e-6,'records':records,'boundary':'Only core numeric/feasibility results compared; schema, wording and case_version intentionally differ. Not a platform integration test.'}


def default_golden():
    candidates=[ROOT.parent/'cases'/'golden_results.json',ROOT.parent.parent/'cases'/'golden_results.json',ROOT.parent/'cases'/'golden_results.json']
    return next((p for p in candidates if p.is_file()),candidates[0])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--golden',type=Path,default=default_golden())
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    evidence=run(args.golden)
    if args.output:args.output.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: 9/9 original snapshots; numeric/feasibility fields match within 1e-6')
