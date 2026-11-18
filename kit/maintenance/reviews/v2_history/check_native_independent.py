"""Independent review of emitted YAML. No imports from the builder or its tests."""
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'.workflow_deps'))
import yaml

ROOT=Path(__file__).resolve().parents[1]
FILES=sorted((ROOT/'platform_import').glob('*.yaml'))
SAMPLE=yaml.safe_load((ROOT/'maintenance/templates/knowledge_example.yaml').read_text(encoding='utf-8'))
KT=next(n['Configs']['Knowledge'] for n in SAMPLE['Nodes'] if n['Type']=='Knowledge')
CODE_CACHE={}
OBSERVED={}
HITS=[{'output':'统计学需要理解数据和不确定性。通俗练习仅帮助理解样本证据范围。\n原始来源：https://stat.nankai.edu.cn/example.htm','metadata':{'score':.9,'document_name':'检查夹具，非真实检索','document_url':'https://stat.nankai.edu.cn/example.htm','dataset_id':'fixture','segment_id':'fixture'}}]

def references(x):
    if isinstance(x,dict):
        if x.get('RefType')=='node_field':yield x
        for v in x.values():yield from references(v)
    elif isinstance(x,list):
        for v in x:yield from references(v)

def output_names(n):
    c=n['Configs'][n['Type']]
    if n['Type']=='InformationGathering':return {'USER_RESPONSE'}|{s['Name'] for s in c['ExtractSchema']}
    if n['Type']=='VariableMerge':return {g['Name'] for g in c['Groups']}
    return {s['Name'] for s in c.get('OutputSchema',[])}

def handler(n):
    src=n['Configs']['Code']['Code'];key=hashlib.sha256(src.encode()).hexdigest()
    if key not in CODE_CACHE:
        ns={'__name__':'independent_review'};exec(compile(src,n['Name'],'exec'),ns);CODE_CACHE[key]=ns['handler']
    return CODE_CACHE[key]

def graph(path):
    data=yaml.safe_load(path.read_text(encoding='utf-8'));nodes={n['Code']:n for n in data['Nodes']};named={n['Name']:n for n in nodes.values()}
    assert len(nodes)==len(data['Nodes'])==len(named)
    assert sum(n['Type']=='Start' for n in nodes.values())==sum(n['Type']=='End' for n in nodes.values())==1
    pending=dict(nodes);ordered=[];ancestry={}
    while pending:
        ready=[n for n in pending.values() if all(x['NodeCode'] in ancestry for x in n.get('Depends',[]))]
        assert ready,'cycle, missing dependency or disconnected Start'
        for n in ready:
            ancestry[n['Code']]=set().union(*(ancestry[x['NodeCode']]|{x['NodeCode']} for x in n.get('Depends',[])))
            ordered.append(n);del pending[n['Code']]
    for n in nodes.values():
        assert n['ID']==n['Code'];config=n['Configs'][n['Type']]
        for d in n.get('Depends',[]):
            if 'PortID' in d:
                source=nodes[d['NodeCode']];assert source['Type']=='Condition'
                cond=source['Configs']['Condition'];assert d['PortID'] in {b['ID'] for b in cond['IfBranches']}|{cond['ElseBranch']['ID']}
        for r in references(config):
            assert r['NodeCode'] in ancestry[n['Code']],(path.name,n['Name'],'not upstream',r)
            assert r['Path'] in output_names(nodes[r['NodeCode']]),(path.name,n['Name'],'undeclared output',r)
            if nodes[r['NodeCode']]['Type']=='InformationGathering':assert r['Path']=='USER_RESPONSE'
        if n['Type']=='Knowledge':
            for key in KT:
                if key not in {'QueryVariable','TopK'}:assert config[key]==KT[key],('Knowledge schema differs',key)
            ids=set(data['Depends']['KnowledgeMap'])
            assert ids==set(config['KnowledgeRange'])=={x['ID'] for x in config['DatabaseInfos']}=={json.loads(x['JsonValue']) for x in config['DatasetParamsVariable']}
        if n['Type']=='InformationGathering':assert config['ExtractParameters'] and config['ExtractSchema']
        if n['Type']=='Code':handler(n)
    assert len(ancestry[named['End']['Code']])==len(nodes)-1,'some node cannot lead to End'
    return data,nodes,named,ordered

def run(path,overrides=None,empty_hits=False):
    data,nodes,named,order=graph(path);overrides=overrides or {}
    replies={'Group':'3','Profile':'2026级，没试过','CaseSelect':'sensor_luggage','BAsk':'40','BConfirm':'确认','BRetry':'确认','VAsk':'65','VConfirm':'确认','VRetry':'确认','Reflection':'我愿意比较不同条件。\n想了解：通信工程、自动化','RecordConfirm':'确认记录','RecordRetry':'确认记录'}
    replies.update(overrides)
    results={};ports={};trace=[];hits=[] if empty_hits else copy.deepcopy(HITS)
    def resolve(v):return json.loads(v['JsonValue']) if v['RefType']=='value' else results[v['NodeCode']][v['Path']]
    def inputs(vs):return {v['Name']:resolve(v) for v in vs}
    for n in order:
        name,code,kind=n['Name'],n['Code'],n['Type'];ds=n.get('Depends',[])
        active=[d for d in ds if d['NodeCode'] in results and ('PortID' not in d or ports[d['NodeCode']]==d['PortID'])]
        if kind!='Start' and (not active if kind=='VariableMerge' else len(active)!=len(ds)):continue
        c=n['Configs'][kind]
        if kind=='Start':out={'task_id':'sensor','query':'统计学与证据'}
        elif kind=='InformationGathering':out={'USER_RESPONSE':replies[name],'unused_ack':'irrelevant'}
        elif kind=='Knowledge':out={'outputList':hits,'filter':''}
        elif kind=='Code':
            out=handler(n)(inputs(c['InputVariables']))
            for field in c['OutputSchema']:
                assert field['Name'] in out,(name,'missing output',field['Name'])
                val=out[field['Name']];typ=field['Type']
                assert type(val) is ({0:str,1:int,2:bool}.get(typ,type(val))),(name,'wrong type',field,val)
            OBSERVED.setdefault(path.name,set()).add(name)
        elif kind=='LLM':
            p=inputs(c['InputVariables'])
            if name in {'BExtract','VExtract'}:
                raw=p['raw']
                if raw=='BROKEN':text='not json'
                elif raw in {'结束体验','不确定'}:text=json.dumps({'action':'stop' if raw=='结束体验' else 'hint','plan':{},'quote':raw,'question':''},ensure_ascii=False)
                else:text=json.dumps({'action':'submit','plan':{'threshold':float(raw)},'quote':raw,'question':''},ensure_ascii=False)
            elif name=='DraftLLM':
                text=json.dumps({'title':'抽样练习','scenario':'原创合成排队情境；原始资料 https://stat.nankai.edu.cn/example.htm','question':'你选什么采样方法','options':{'A':'只问同班','B':'不同时段','C':'只问朋友'},'reason_prompt':'说明取舍','changed_condition':'时间减少','concept':'抽样','source_evidence':[{'quote':'统计学需要理解数据和不确定性','why_relevant':'证据范围'}],'limits':'模型草拟，待学科审核，不计分。'},ensure_ascii=False)
            else:
                text=json.dumps({'answer':'统计学涉及数据与不确定性。','citations':[{'quote':'统计学需要理解数据和不确定性','source_url':'https://stat.nankai.edu.cn/example.htm'}] if hits else [],'missing':''},ensure_ascii=False)
            out={'raw_output':text}
        elif kind=='Condition':
            port=c['ElseBranch']['ID']
            for b in c['IfBranches']:
                conds=[resolve(t['Left'])==resolve(t['Right']) for t in b['Conditions']]
                if all(conds):port=b['ID'];break
            ports[code]=port;out={}
        elif kind=='VariableMerge':
            out={}
            for g in c['Groups']:
                available=[v for v in g['Variables'] if v['NodeCode'] in results]
                assert len(available)==1,(name,'non-exclusive merge',len(available))
                out[g['Name']]=resolve(available[0])
        elif kind=='Message':out={}
        elif kind=='End':out=inputs(c['InputVariables'])
        else:raise AssertionError(kind)
        results[code]=out;trace.append(name)
    assert named['End']['Code'] in results,'End did not execute'
    return {'trace':trace,'final':results[named['End']['Code']]['final_text'],'nodes':named,'results':results}

if __name__=='__main__':
    report={'independent_graphs':[],'scenarios':[],'known_failures':[]}
    for path in FILES:
        d,ns,named,order=graph(path)
        report['independent_graphs'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'nodes':len(ns),'code_nodes':sum(n['Type']=='Code' for n in ns.values()),'single_end':True,'upstream_refs':True,'knowledge_matches_sample':True})
        if 'Explore' not in path.name:
            for empty in [False,True]:
                r=run(path,empty_hits=empty);report['scenarios'].append({'file':path.name,'scenario':'knowledge_empty' if empty else 'knowledge_hit','end':bool(r['final'])})
            continue
        scenarios=[('normal',{}),('base_stop',{'BAsk':'结束体验'}),('base_confirm_stop',{'BConfirm':'结束体验'}),('base_retry_stop',{'BConfirm':'可能吧','BRetry':'结束体验'}),('base_retry_success',{'BConfirm':'65','BRetry':'确认'}),('base_retry_fail',{'BConfirm':'可能吧','BRetry':'随便'}),('revise_stop',{'VAsk':'结束体验'}),('revise_confirm_stop',{'VConfirm':'结束体验'}),('revise_retry_stop',{'VConfirm':'可能吧','VRetry':'结束体验'}),('revise_retry_success',{'VConfirm':'60','VRetry':'确认'}),('revise_retry_fail',{'VConfirm':'可能吧','VRetry':'随便'}),('model_invalid_recovery',{'BAsk':'BROKEN','BConfirm':'试算40'}),('menu_error',{'Group':'同名伯苓班'}),('selection_error',{'CaseSelect':'materials_shell'}),('record_decline',{'RecordConfirm':'先不确认'}),('record_retry',{'RecordConfirm':'可能吧','RecordRetry':'确认记录'}),('record_retry_fail',{'RecordConfirm':'可能吧','RecordRetry':'随便'}),('reflection_stop',{'Reflection':'结束体验'}),('record_stop',{'RecordConfirm':'结束体验'}),('record_retry_stop',{'RecordConfirm':'可能吧','RecordRetry':'结束体验'})]
        for label,ov in scenarios:
            r=run(path,ov)
            report['scenarios'].append({'file':path.name,'scenario':label,'end':bool(r['final']),'executed_nodes':len(r['trace'])})
            if label=='reflection_stop' and 'RecordConfirm' in r['trace']:report['known_failures'].append({'file':path.name,'scenario':label,'issue':'explicit stop asks record confirmation'})
            if label=='record_stop' and 'RecordRetry' in r['trace']:report['known_failures'].append({'file':path.name,'scenario':label,'issue':'explicit stop asks record retry'})
        r=run(path,empty_hits=True);report['scenarios'].append({'file':path.name,'scenario':'explore_no_hits','end':bool(r['final'])})
    report['code_coverage']=[{'file':path.name,'covered':len(OBSERVED.get(path.name,set())),'total':sum(n['Type']=='Code' for n in graph(path)[1].values()),'uncovered':sorted({n['Name'] for n in graph(path)[1].values() if n['Type']=='Code'}-OBSERVED.get(path.name,set()))} for path in FILES]
    report['direct_schema_checks']=[]
    for path in FILES:
        for n in graph(path)[1].values():
            if n['Name'] in {'XAdvanceError','XDraftError'}:
                result=handler(n)({'text':'','fallback':'审查退出反馈'})
                assert all(x['Name'] in result and isinstance(result[x['Name']],str) for x in n['Configs']['Code']['OutputSchema'])
                report['direct_schema_checks'].append({'file':path.name,'node':n['Name'],'all_declared_fields_returned':True})
    package=ROOT
    profiles=json.loads((package/'config/major_profiles.json').read_text(encoding='utf-8'))['profiles']
    sources=json.loads((package/'references/source_register.json').read_text(encoding='utf-8'))['sources']
    ids={s['id'] for s in sources};cards=sorted((package/'knowledge_base').glob('10_major_*.md'))
    assert len(profiles)==len(cards)==33 and len(sources)==36
    assert all(sid in ids for profile in profiles for sid in profile['source_ids'])
    for card in cards:
        text=card.read_text(encoding='utf-8')
        assert not re.search(r'日期[：:]\s*(None|null)',text)
        body=text.split('\n解释边界',1)[1].split('\n资料适用范围',1)[0]
        assert not any(len(line.removeprefix('- ').strip())==1 for line in body.splitlines() if line.startswith('- '))
    all_text='\n'.join(p.read_text(encoding='utf-8') for p in (package/'knowledge_base').glob('*.md'))
    used=set(re.findall(r'(?:STEM-S\d\d|LE-[A-Z0-9-]+|NK-(?:POLICY|CHOICE)-\d{8}|CONCEPT-NIM-[A-Z-]+)',all_text))
    assert used <= ids,used-ids
    report['knowledge_checks']={'professional_profiles':33,'professional_cards':33,'source_records':36,'all_profile_refs_exist':True,'all_knowledge_card_source_ids_exist':True,'no_none_dates':True,'no_single_character_limits':True,'new_metrology_sources':sorted(s for s in ids if s.startswith('CONCEPT-NIM'))}
    out=Path(__file__).with_name('native_independent_results.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'graphs':len(report['independent_graphs']),'scenarios':len(report['scenarios']),'known_failures':report['known_failures'],'code_coverage':report['code_coverage']},ensure_ascii=False,indent=2))
