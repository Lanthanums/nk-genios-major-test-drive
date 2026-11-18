"""Offline native graph QA. Models, retrieval and user replies are explicit fixtures."""
from pathlib import Path
import base64
import copy
import importlib.util
import json
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT
sys.path.insert(0,str(ROOT.parent/'.workflow_deps'))
import yaml


def refs(value):
    if isinstance(value,dict):
        if value.get('RefType')=='node_field':yield value
        for child in value.values():yield from refs(child)
    elif isinstance(value,list):
        for child in value:yield from refs(child)


def fields(node):
    kind=node['Type'];c=node['Configs'][kind]
    if kind=='InformationGathering':return {'USER_RESPONSE'}|{x['Name'] for x in c['ExtractSchema']}
    if kind=='VariableMerge':return {x['Name'] for x in c['Groups']}
    if kind in {'Message','Condition'}:return set()
    if kind=='End':return {x['Name'] for x in c['InputVariables']}
    return {x['Name'] for x in c['OutputSchema']}


class Workflow:
    def __init__(self,path):
        self.path=Path(path);self.data=yaml.safe_load(self.path.read_text(encoding='utf-8'))
        self.nodes={n['Code']:n for n in self.data['Nodes']};self.named={n['Name']:n for n in self.nodes.values()}
        assert len(self.nodes)==len(self.data['Nodes'])==len(self.named)
        pending=dict(self.nodes);self.order=[];seen=set();self.ancestors={}
        while pending:
            ready=[n for n in pending.values() if all(d['NodeCode'] in seen for d in n.get('Depends',[]))]
            assert ready,'Cycle or unknown dependency'
            for n in ready:
                self.order.append(n);seen.add(n['Code']);pending.pop(n['Code'])
                ancestors=set()
                for dep in n.get('Depends',[]):ancestors|={dep['NodeCode']}|self.ancestors[dep['NodeCode']]
                self.ancestors[n['Code']]=ancestors
        self.functions={}
        for node in self.nodes.values():
            if node['Type']=='Code':
                namespace={'__name__':'native_node_test'}
                exec(compile(node['Configs']['Code']['Code'],node['Name'],'exec'),namespace)
                self.functions[node['Code']]=namespace['handler']

    def check(self):
        assert self.data['DLVersion']=='v2'
        assert sum(n['Type']=='Start' for n in self.nodes.values())==1
        assert sum(n['Type']=='End' for n in self.nodes.values())==1
        successors={code:set() for code in self.nodes}
        for n in self.nodes.values():
            assert n['ID']==n['Code']
            assert len(base64.b32hexdecode(n['Code'].upper()+'===='))==12
            kind=n['Type'];c=n['Configs'][kind]
            for d in n.get('Depends',[]):
                successors[d['NodeCode']].add(n['Code'])
                if d.get('PortID'):
                    cond=self.nodes[d['NodeCode']]['Configs']['Condition']
                    assert d['PortID'] in {b['ID'] for b in cond['IfBranches']}|{cond['ElseBranch']['ID']}
            for var in refs(c):
                assert var.get('NodeCode') in self.nodes,(n['Name'],var)
                assert var['NodeCode'] in self.ancestors[n['Code']],(n['Name'],'not upstream',var)
                assert var.get('Path') in fields(self.nodes[var['NodeCode']]),(n['Name'],'bad path',var)
                if self.nodes[var['NodeCode']]['Type']=='InformationGathering':assert var['Path']=='USER_RESPONSE'
            pairs=[]
            if kind=='InformationGathering':
                assert c['ExtractParameters'] and c['ExtractSchema']
                pairs=[(c['QuestionTemplate'],c['TemplateVars'])]
            if kind=='LLM':pairs=[(c['SystemPrompt']+c['Prompt'],c['InputVariables'])]
            if kind=='Message':pairs=[(c['Content'],c['InputVariables'])]
            for text,variables in pairs:
                assert set(re.findall(r'{{\s*([\w]+)\s*}}',text))=={v['Name'] for v in variables},n['Name']
            if kind=='Knowledge':
                actual=set(self.data['Depends']['KnowledgeMap'])
                assert set(c['KnowledgeRange'])==actual
                assert {x['ID'] for x in c['DatabaseInfos']}==actual
                assert {json.loads(x['JsonValue']) for x in c['DatasetParamsVariable']}==actual
                assert c['QueryVariable']['RefType']=='node_field'
                assert next(x for x in c['OutputSchema'] if x['Name']=='outputList')['Type']==9
            if kind=='Code':
                assert 'def handler(params)' in c['Code']
        for code in self.nodes:
            seen=set();queue=[code]
            while queue:
                cur=queue.pop()
                if cur not in seen:seen.add(cur);queue+=list(successors[cur])
            assert self.named['End']['Code'] in seen,(self.nodes[code]['Name'],'cannot reach End')


class Replay:
    def __init__(self,workflow,answers,start,knowledge=None,llm_override=None):
        self.workflow=workflow;self.answers=answers;self.start=start;self.knowledge=knowledge or [];self.llm_override=llm_override or {}
        self.values={};self.ports={};self.trace=[]

    def resolve(self,v):
        return json.loads(v['JsonValue']) if v['RefType']=='value' else self.values[v['NodeCode']][v['Path']]

    def params(self,variables):return {v['Name']:self.resolve(v) for v in variables}

    def render(self,text,variables):
        values=self.params(variables)
        return re.sub(r'{{\s*(\w+)\s*}}',lambda m:str(values[m[1]]),text)

    def model(self,name,c):
        if name in self.llm_override:return self.llm_override[name]
        p=self.params(c['InputVariables'])
        if name in {'BExtract','VExtract'}:
            schema=json.loads(p['schema']);mode=schema['mode'];raw=p['raw']
            # Fixture parsing is explicitly not a real model accuracy test.
            if raw=='不确定':return json.dumps({'action':'hint','plan':{},'quote':raw,'question':''},ensure_ascii=False)
            if raw=='结束体验':return json.dumps({'action':'stop','plan':{},'quote':raw,'question':''},ensure_ascii=False)
            plan={'choice':raw} if mode=='choice' else ({'path':raw.split('-')} if mode=='route' else {'threshold' if mode=='sensor' else 'k':float(raw)})
            return json.dumps({'action':'submit','plan':plan,'quote':raw,'question':''},ensure_ascii=False)
        if name in {'BridgeLLM','AnswerLLM'}:
            rows=json.loads(p['context'])
            if not rows:return json.dumps({'answer':'当前资料不足。','citations':[],'missing':'没有相关命中'},ensure_ascii=False)
            row=rows[0];quote=row['content'][:18]
            url=re.search(r'https?://[^\s]+',row['content'])
            return json.dumps({'answer':'活动呈现的是一小段工作方法，可结合材料继续了解，不据此判断专业适配。',
                               'citations':[{'quote':quote,'source_url':url.group(0) if url else ''}],
                               'missing':'当前材料没有个人分流资格确认。'},ensure_ascii=False)
        if name=='DraftLLM':
            rows=json.loads(p['context']);quote=rows[0]['content'][:18] if rows else '没有相关资料'
            return json.dumps({'title':'如何排除替代解释','scenario':'原创合成情境：两组表现不同，但光照和材料都变了。',
                'question':'为了比较材料因素，你先做什么？','options':{'A':'原样重复','B':'固定光照比较材料','C':'只挑最大值'},
                'reason_prompt':'说明你想排除什么解释。','changed_condition':'新增批次差异，重新考虑比较方式。','concept':'控制变量',
                'source_evidence':[{'quote':quote,'why_relevant':'卡片解释比较条件与证据边界。'}],
                'limits':'模型草稿、合成情境，尚未学科审核，不进入固定评分题库。'},ensure_ascii=False)
        raise AssertionError(name)

    def run(self):
        for n in self.workflow.order:
            code,name,kind=n['Code'],n['Name'],n['Type'];deps=n.get('Depends',[])
            active=[d for d in deps if d['NodeCode'] in self.values and ('PortID' not in d or self.ports.get(d['NodeCode'])==d['PortID'])]
            if kind!='Start' and not (bool(active) if kind=='VariableMerge' else len(active)==len(deps)):continue
            c=n['Configs'][kind];detail={}
            if kind=='Start':out=dict(self.start)
            elif kind=='InformationGathering':
                detail['question']=self.render(c['QuestionTemplate'],c['TemplateVars'])
                out={'USER_RESPONSE':self.answers[name],'unused_ack':'intentionally unrelated value'}
            elif kind=='LLM':
                detail['prompt']=self.render(c['Prompt'],c['InputVariables']);out={'raw_output':self.model(name,c)}
            elif kind=='Knowledge':out={'outputList':copy.deepcopy(self.knowledge),'filter':''}
            elif kind=='Code':
                inputs=self.params(c['InputVariables']);detail['input']=inputs;out=self.workflow.functions[code](inputs)
                for field in c['OutputSchema']:
                    assert field['Name'] in out,(name,'missing declared output',field['Name'])
                    value=out[field['Name']];typ=field['Type']
                    assert (type(value) is bool if typ==2 else isinstance(value,str) if typ==0 else type(value) is int if typ==1 else True),(name,field,value)
            elif kind=='Message':detail['message']=self.render(c['Content'],c['InputVariables']);out={}
            elif kind=='Condition':
                port=c['ElseBranch']['ID']
                for branch in c['IfBranches']:
                    checks=[]
                    for t in branch['Conditions']:
                        assert t['Operator']=='EQ';checks.append(self.resolve(t['Left'])==self.resolve(t['Right']))
                    if all(checks) if branch['ConditionLogic']=='AND' else any(checks):port=branch['ID'];break
                self.ports[code]=port;detail['selected_port']=port;out={}
            elif kind=='VariableMerge':
                out={}
                for g in c['Groups']:
                    available=[v for v in g['Variables'] if v['NodeCode'] in self.values]
                    assert len(available)==1,(name,g['Name'],len(available))
                    out[g['Name']]=self.resolve(available[0])
            elif kind=='End':out=self.params(c['InputVariables'])
            else:raise AssertionError(kind)
            self.values[code]=out;self.trace.append({'node':name,**detail,'output':copy.deepcopy(out)})
        end=self.values[self.workflow.named['End']['Code']]
        self.final=end['final_text'];assert isinstance(self.final,str) and self.final.strip()
        return self

    def result(self,name):return self.values[self.workflow.named[name]['Code']]


def plans(case):
    mode=BANK['families'][case['task_id']]['mode']
    if mode=='choice':return tuple(next(k for k,v in case['data']['outcomes'][p].items() if v['supported_by_stated_criteria']) for p in [0,1])
    if mode=='route':return ('S-A-B-C-T','S-A-C-T') if case['case_id']=='route_campus' else ('S-A-C-T','S-B-C-T') if case['case_id']=='route_coldchain' else ('S-A-T','S-B-C-T')
    return ('40','65') if mode=='sensor' else ('1.6','0.6')


def answers(case,group='3'):
    p1,p2=plans(case)
    return {'Group':group,'Profile':'2026级，没做过这类活动。','CaseSelect':case['case_id'],'BAsk':p1,'BConfirm':'确认',
            'VAsk':p2,'VConfirm':'确认','Reflection':'我愿意继续比较条件，但还不知道是否喜欢完整专业。\n想了解：通信工程、自动化',
            'RecordConfirm':'确认记录','BRetry':'确认','VRetry':'确认','RecordRetry':'确认记录'}


BANK=json.loads((PKG/'config/case_bank.json').read_text(encoding='utf-8'))
FILES={p.stem:Workflow(p) for p in (PKG/'platform_import').glob('*.yaml')}
HITS=[{'output':'实验比较需要先说明对象和条件，再讨论证据能支持什么。此为编者概念卡。\n来源：https://chem.nankai.edu.cn/example',
       'metadata':{'document_name':'测试检索夹具（不是线上命中）','document_url':'','score':0.9}}]


class NativeWorkflowTests(unittest.TestCase):
    def test_all_four_native_graphs(self):
        self.assertEqual(len(FILES),4)
        for workflow in FILES.values():workflow.check()

    def test_all_27_cases_offline_full_paths(self):
        workflow=FILES['WF_Explore_One_v2_Offline']
        for i,case in enumerate(BANK['cases'].values()):
            with self.subTest(case=case['case_id']):
                r=Replay(workflow,answers(case,str(i%8+1)),{'task_id':case['task_id']}).run()
                self.assertIn('本人已确认',r.final)
                self.assertIn(case['title'],r.final)
                self.assertEqual(r.result('Finalize')['action'],'completed')

    def test_kb_bridge_present_and_no_hit_fallback(self):
        case=BANK['cases']['experiment_catalyst'];w=FILES['WF_Explore_One_v2']
        for hits in [HITS,[]]:
            r=Replay(w,answers(case),{'task_id':'experiment'},hits).run()
            self.assertIn('本人已确认',r.final)
            self.assertEqual(r.result('KBBridgeContext')['hit_count'],len(hits))
            if not hits:self.assertIn('没有命中',r.result('BridgeCheck')['final_text'])

    def test_all_eight_group_profiles_and_unknown(self):
        case=BANK['cases']['materials_shell'];w=FILES['WF_Explore_One_v2_Offline']
        for group in map(str,range(1,10)):
            r=Replay(w,answers(case,group),{'task_id':'materials'}).run()
            state=json.loads(r.result('Finalize')['state_json'])
            self.assertEqual(state['group_confirmed'],group!='9')
        r=Replay(w,answers(case,'卓越拔尖计划伯苓班'),{'task_id':'materials'}).run()
        self.assertNotIn(w.named['BAsk']['Code'],r.values)

    def test_stop_before_and_during_confirmation(self):
        case=BANK['cases']['sensor_luggage'];w=FILES['WF_Explore_One_v2_Offline']
        for node in ['BAsk','BConfirm','VAsk','VConfirm']:
            a=answers(case);a[node]='结束体验';r=Replay(w,a,{'task_id':'sensor'}).run()
            self.assertNotIn(w.named['Draft']['Code'],r.values)

    def test_stop_during_reflection_and_report_confirmation(self):
        case=BANK['cases']['sensor_luggage'];w=FILES['WF_Explore_One_v2_Offline']
        for node,next_node in [('Reflection','RecordConfirm'),('RecordConfirm','RecordRetry')]:
            a=answers(case);a[node]='结束体验';r=Replay(w,a,{'task_id':'sensor'}).run()
            self.assertNotIn(w.named[next_node]['Code'],r.values)
            self.assertIn('结束',r.final)
            self.assertNotIn('记录状态：本人已确认',r.final)

    def test_ambiguous_input_specific_clarification_and_short_correction(self):
        case=BANK['cases']['sensor_luggage'];a=answers(case);a.update(VAsk='60或65',VConfirm='那65吧',VRetry='确认')
        override={'VExtract':json.dumps({'action':'clarify','plan':{},'quote':'60或65','question':'60与65，你先试哪一个？'},ensure_ascii=False)}
        r=Replay(FILES['WF_Explore_One_v2_Offline'],a,{'task_id':'sensor'},llm_override=override).run()
        question=next(t['question'] for t in r.trace if t['node']=='VConfirm')
        self.assertIn('你先试哪一个',question)
        self.assertNotIn('路线：',question)
        self.assertEqual(r.result('VCompute')['action'],'awaiting_confirmation')
        self.assertEqual(r.result('VRetryCompute')['action'],'evaluated')
        self.assertIn('本人已确认',r.final)

    def test_failed_model_json_can_be_corrected(self):
        case=BANK['cases']['sensor_luggage'];a=answers(case);a['BConfirm']='试算40'
        r=Replay(FILES['WF_Explore_One_v2_Offline'],a,{'task_id':'sensor'},llm_override={'BExtract':'not json'}).run()
        self.assertIn('本人已确认',r.final)

    def test_vague_twice_stops_without_calculation(self):
        case=BANK['cases']['sensor_luggage'];a=answers(case);a.update(BConfirm='可能吧',BRetry='随便')
        r=Replay(FILES['WF_Explore_One_v2_Offline'],a,{'task_id':'sensor'}).run()
        self.assertNotIn(FILES['WF_Explore_One_v2_Offline'].named['Advance']['Code'],r.values)
        self.assertNotIn('本人已确认',r.final)

    def test_record_decline_and_revised_intent(self):
        case=BANK['cases']['finance_promotion'];w=FILES['WF_Explore_One_v2_Offline']
        a=answers(case);a['RecordConfirm']='先不确认';r=Replay(w,a,{'task_id':'finance'}).run()
        self.assertIn('草稿',r.final)
        a=answers(case);a['RecordConfirm']='更正并确认：我需要继续了解。\n想了解：电子信息科学与技术'
        r=Replay(w,a,{'task_id':'finance'}).run();state=json.loads(r.result('Finalize')['state_json'])
        self.assertEqual(state['requested_majors'],['电子信息科学与技术'])

    def test_negative_mention_does_not_become_intent(self):
        case=BANK['cases']['route_campus'];a=answers(case);a['Reflection']='我不想学计算机科学与技术，今天只是想试试。'
        r=Replay(FILES['WF_Explore_One_v2_Offline'],a,{'task_id':'route'}).run()
        self.assertEqual(json.loads(r.result('Finalize')['state_json'])['requested_majors'],[])

    def test_two_knowledge_workflows_and_empty_context(self):
        for name in ['WF_Major_Knowledge_v2','WF_KB_Practice_Draft_v2']:
            for hits in [HITS,[]]:
                r=Replay(FILES[name],{}, {'query':'比较实验设计与专业日常'},hits).run()
                self.assertTrue(r.final)
                if name.endswith('Draft_v2') and hits:self.assertIn('草稿',r.final)

    def test_explicit_case_selection_rejects_wrong_family(self):
        case=BANK['cases']['sensor_luggage'];a=answers(case);a['CaseSelect']='materials_shell'
        r=Replay(FILES['WF_Explore_One_v2_Offline'],a,{'task_id':'sensor'}).run()
        self.assertNotIn(FILES['WF_Explore_One_v2_Offline'].named['BAsk']['Code'],r.values)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(NativeWorkflowTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'fixed_case_full_replays':27,'workflows':[{ 'file':w.path.name,'nodes':len(w.nodes),'ends':sum(n['Type']=='End' for n in w.nodes.values()),'bytes':w.path.stat().st_size} for w in FILES.values()],
            'live_platform_import':False,'live_models':False,'real_retrieval':False}
    (PKG/'tests/workflow_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
