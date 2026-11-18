"""Independent native-YAML regression checks. No generator imports."""
from pathlib import Path
import hashlib
import json
import re
import sys
import traceback
from native_replay import Workflow, Replay, Button, FreeText
import unittest

HERE=Path(__file__).resolve().parent
ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT if (ROOT/'config').is_dir() else ROOT/'package'
BANK=json.loads((PKG/'config/case_bank.json').read_text(encoding='utf-8'))
GROUPS=json.loads((PKG/'config/major_groups.json').read_text(encoding='utf-8'))['groups']
WORKFLOWS={name:Workflow(PKG/'platform_import'/name) for name in ['WF_Explore_One_v2.yaml','WF_Explore_One_v2_Offline.yaml']}
EVIDENCE=[]
FAILURES=[]
STOP='我已经做了两次，想结束直接拿报告'

def model(p, replay):
    # Fixture extraction is deliberately simple and declared, not a live model.
    raw=p['raw']; mode=json.loads(p['schema'])['mode']
    if '结束' in raw or '拿报告' in raw:
        return {'action':'stop','plan':{},'quote':raw,'question':''}
    if raw=='不确定':
        return {'action':'hint','plan':{},'quote':raw,'question':''}
    if mode=='choice':
        matched=re.search('[ABC]',raw)
        plan={'choice':matched[0] if matched else 'A'}
    elif mode=='route':plan={'path':raw.split('-')}
    else:plan={'threshold' if mode=='sensor' else 'k':float(raw)}
    return {'action':'submit','plan':plan,'quote':raw,'question':''}

def bridge(p,replay):
    return {'answer':'当前资料不足。','citations':[],'missing':'本地空检索夹具，没有命中资料。'}

def answers(cid='experiment_catalyst'):
    case=BANK['cases'][cid]; task=case['task_id']; mode=BANK['families'][task]['mode']
    raw='S-A-T' if mode=='route' else '40' if mode=='sensor' else '0.6' if mode=='control' else 'A'
    variants=[c['case_id'] for c in BANK['cases'].values() if c['task_id']==task]
    a={
        'Group':Button(option_id='physics_opto'),'Activity':Button(option_id=task),
        'CaseSelect':Button(option_id='case'+str(variants.index(cid)+1)),
        'BChoice':Button(option_id='A'),'BAsk':raw,'BConfirm':Button(option_id='confirm'),
        'BEdit':raw,'BRetryConfirm':Button(option_id='confirm'),'AfterFirst':Button(option_id='continue'),
        'VChoice':Button(option_id='B'),'VAsk':raw,'VConfirm':Button(option_id='confirm'),
        'VEdit':raw,'VRetryConfirm':Button(option_id='confirm'),'AfterSecond':Button(option_id='reflect'),
        'Reflection':'我愿意继续比较两种错误，还不确定是否喜欢完整专业。\n想了解：通信工程、自动化',
        'RecordConfirm':Button(option_id='confirm'),'ReflectionEdit':'我更想试一下真实电路，再比较自己的感受。',
        'RecordReconfirm':Button(option_id='confirm')}
    return a

def replay(name,cid='experiment_catalyst',changes=None,start=None,workflow=None,check=None):
    w=workflow or WORKFLOWS['WF_Explore_One_v2_Offline.yaml']; a=answers(cid); a.update(changes or {})
    row={'name':name,'workflow':w.path.name,'case_id':cid}
    try:
        r=Replay(w,a,start or {'task_id':BANK['cases'][cid]['task_id'],'reported_group_text':''},models={n:model for n in ['BExtract','VExtract','BEditExtract','VEditExtract']}|{'BridgeLLM':bridge}).run()
        assert sum(x['type']=='End' for x in r.trace)==1
        # Strict refs/merge checks happen in the interpreter itself.
        rendered='\n\n'.join(r.rendered_texts())
        for forbidden in ['{{','USER_RESPONSE','state_json','normalizer_context','case_id','awaiting_plan','auto']:
            assert forbidden not in rendered, ('leaked internal/literal template',forbidden)
        if check:check(r)
        row.update(status='passed',trace_nodes=[x['node'] for x in r.trace],final=r.final,
                   actions={x['node']:x['output']['action'] for x in r.trace if 'action' in x.get('output',{})},
                   buttons=[{'node':x['node'],'selected':x.get('user_action'), 'buttons':x['buttons']} for x in r.trace if 'buttons' in x])
    except Exception as exc:
        row.update(status='failed',error=str(exc),traceback=traceback.format_exc())
        FAILURES.append(row)
    EVIDENCE.append(row)
    return row

def final_state(r):
    for x in reversed(r.trace):
        if x['output'].get('state_json'):
            return json.loads(x['output']['state_json'])
    return None

def evaluated(r):return [e for e in final_state(r)['events'] if e['kind']=='evaluated']

def full_check(r):
    s=final_state(r)
    assert len(evaluated(r))==2
    assert s['record_confirmed'] is True
    assert '本人已确认' in r.final



class NativeWorkflowV21Tests(unittest.TestCase):
    def test_structure_and_27_cases_per_yaml(self):
        before=len(FAILURES)
        for name,w in WORKFLOWS.items():
            try:w.check();EVIDENCE.append({'name':'structure_'+name,'status':'passed','nodes':len(w.nodes),'sha256':hashlib.sha256(w.path.read_bytes()).hexdigest()})
            except Exception as exc:
                row={'name':'structure_'+name,'status':'failed','error':str(exc)};EVIDENCE.append(row);FAILURES.append(row)
            for cid in BANK['cases']:
                replay('all27_'+cid,cid,workflow=w,check=full_check)
        self.assertEqual(FAILURES[before:], [], '\n'.join(x['name']+': '+x['error'] for x in FAILURES[before:]))

    def test_known_and_selected_groups(self):
        before=len(FAILURES)
        for gid,group in GROUPS.items():
            def known(r,gid=gid):
                assert 'Group' not in [x['node'] for x in r.trace]
                assert final_state(r)['group_id']==gid
            replay('known_group_'+gid,start={'task_id':'experiment','reported_group_text':group['display_name']},check=known)
            def picked(r,gid=gid):
                assert [x['node'] for x in r.trace].count('Group')==1
                assert final_state(r)['group_id']==gid
            replay('picked_group_'+gid,changes={'Group':Button(option_id=gid)},check=picked)

        replay('ambiguous_boqin',start={'task_id':'experiment','reported_group_text':'卓越拔尖计划伯苓班'},
               check=lambda r: (_ for _ in ()).throw(AssertionError('ambiguous same-name class bypassed')) if 'Group' not in [x['node'] for x in r.trace] else None)
        replay('unknown_group',changes={'Group':Button(option_id='unknown')},check=lambda r: (_ for _ in ()).throw(AssertionError('unknown marked confirmed')) if final_state(r)['group_confirmed'] else None)
        self.assertEqual(FAILURES[before:], [], '\n'.join(x['name']+': '+x['error'] for x in FAILURES[before:]))

    def test_every_native_button_and_other(self):
        before=len(FAILURES)
        # Visit every native option button and the hidden Other branch. Each replay
        # starts from the beginning, reaches its target via actual native dependencies.
        w=WORKFLOWS['WF_Explore_One_v2_Offline.yaml']
        for n in w.order:
            if n['Type']!='InformationGathering':continue
            c=n['Configs']['InformationGathering']
            if c['AnswerType']!='option':continue
            node=n['Name']; cid='experiment_catalyst'
            prefix={}
            if node=='Activity':start={'task_id':'auto','reported_group_text':''}
            else:start=None
            if node.startswith('BRetry') or node=='BRetryConfirm':prefix['BConfirm']=Button(option_id='edit')
            if node.startswith('VRetry') or node=='VRetryConfirm':prefix['VConfirm']=Button(option_id='edit')
            if node=='RecordReconfirm':prefix['RecordConfirm']=Button(option_id='edit')
            for opt in c['OptionConfig']['Options']:
                run_cid=cid
                if node=='Activity' and opt['OptionID'] in BANK['families']:
                    run_cid=next(c['case_id'] for c in BANK['cases'].values() if c['task_id']==opt['OptionID'])
                action=FreeText('我有点不知道该选哪个。') if opt['CondID']=='class_other' else Button(cond_id=opt['CondID'])
                def target(r,node=node,opt=opt):
                    x=next(x for x in r.trace if x['node']==node)
                    assert x['selected_port']==opt['CondID']
                    if opt['CondID']!='class_other':
                        assert x['output']['optionId']==opt['OptionID']
                        assert x['output']['optionContent']==next(o['OptionContent'] for o in x['buttons'] if o['OptionID']==opt['OptionID'])
                    if opt['OptionID'] in {'finish','Others'}:
                        assert '记录' in r.final
                replay('button_'+node+'_'+opt['OptionID'],run_cid,prefix|{node:action},start,check=target)
        self.assertEqual(FAILURES[before:], [], '\n'.join(x['name']+': '+x['error'] for x in FAILURES[before:]))

    def test_natural_finish_at_free_reply_nodes(self):
        before=len(FAILURES)
        # Number/route free-reply stages, exact user complaint and punctuation cases.
        for node in ['BAsk','BEdit','VAsk','VEdit','Reflection','ReflectionEdit']:
            changes={node:STOP}
            if node=='BEdit':changes['BConfirm']=Button(option_id='edit')
            if node=='VEdit':changes['VConfirm']=Button(option_id='edit')
            if node=='ReflectionEdit':changes['RecordConfirm']=Button(option_id='edit')
            def stopped(r,node=node):
                assert final_state(r)['status']=='stopped'
                assert final_state(r)['reflection_raw']!=STOP
                expected=0 if node.startswith('B') else 1 if node.startswith('V') else 2
                assert len(evaluated(r))==expected
                assert final_state(r)['record_confirmed'] is False
            replay('long_stop_'+node,'sensor_luggage',changes,check=stopped)
        self.assertEqual(FAILURES[before:], [], '\n'.join(x['name']+': '+x['error'] for x in FAILURES[before:]))

    def test_direct_reports_after_each_attempt(self):
        before=len(FAILURES)
        for node,count in [('AfterFirst',1),('AfterSecond',2)]:
            def direct(r,count=count):
                assert len(evaluated(r))==count
                assert 'Reflection' not in [x['node'] for x in r.trace]
                assert 'RecordConfirm' not in [x['node'] for x in r.trace]
                assert final_state(r)['record_confirmed'] is False
            replay('direct_report_'+node,'sensor_luggage',{node:Button(option_id='finish')},check=direct)
        self.assertEqual(FAILURES[before:], [], '\n'.join(x['name']+': '+x['error'] for x in FAILURES[before:]))

    def test_quotes_and_reflection_revision(self):
        before=len(FAILURES)
        raw='我说“这里有句号。”\n还有 **加粗**、_斜体_、`代码`。\n{{USER_RESPONSE}}\nA不是我下一阶段的选择。'
        def raw_check(r):
            assert final_state(r)['reflection_raw']==raw
            assert '\n> ' in r.final
            assert '**加粗**' not in r.final
            assert '{{USER_RESPONSE}}' not in r.final
        replay('safe_raw_quote','sensor_luggage',{'Reflection':raw},check=raw_check)

        def revise(r):
            s=final_state(r)
            assert s['reflection_raw']=='我更想试一下真实电路，再比较自己的感受。'
            assert s['requested_majors']==['通信工程','自动化']
            assert s['record_confirmed']
            assert len(evaluated(r))==2
        replay('reflection_revision_retains_intents','sensor_luggage',{'RecordConfirm':Button(option_id='edit')},check=revise)
        self.assertEqual(FAILURES[before:], [], '\n'.join(x['name']+': '+x['error'] for x in FAILURES[before:]))

    @classmethod
    def tearDownClass(cls):
        report={'checks':len(EVIDENCE),'passed':sum(r['status']=='passed' for r in EVIDENCE),
                'failed':len(FAILURES),'live_import':False,'live_models':False,'real_retrieval':False,
                'fixture_note':'Explicit extraction fixtures for route/sensor/control; native buttons for choice tasks; empty knowledge fixture.',
                'evidence':EVIDENCE}
        (HERE/'workflow_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    unittest.main(verbosity=2)
