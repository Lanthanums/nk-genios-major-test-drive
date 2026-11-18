"""Reproduce student-visible conversations from the emitted offline YAML itself."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from native_replay import Workflow, Replay, Button
from test_workflows import answers, model, final_state

w=Workflow(ROOT/'platform_import/WF_Explore_One_v2_Offline.yaml')
w.check()
header=['# 按新版工作流生成的完整对话案例',
        '*双方回答与按钮选择为虚构示例。下面的题面、按钮文字、反馈和报告由交付的离线版 YAML 本地执行产生；没有登录平台。路线、分数和调整力度的文本提取使用明确测试夹具。带知识库版会额外检索并解释方法；这里没有模拟真实召回。*']
documents=[];evidence=[]
for cid,group,reflection in [
    ('materials_optics','物质科学','我原来以为透光高就够了，现在发现使用寿命也会改变选择。我还想看看真正的材料测试。\n想了解：材料物理、材料化学、光电信息科学与工程'),
    ('finance_promotion','数智经济金融','我更想追问增长是不是活动造成的，还不确定自己是否喜欢金融里的其他工作。\n想了解：数字经济、金融科技、统计学'),
    ('sensor_luggage','物理与光电信息技术工程','')]:
    a=answers(cid)
    a['Reflection']=reflection
    if cid=='sensor_luggage':
        a['VAsk']='65'
        a['AfterSecond']=Button(option_id='finish')
    r=Replay(w,a,{'task_id':cid.split('_')[0],'reported_group_text':group},
             models={name:model for name in ['BExtract','VExtract','BEditExtract','VEditExtract']}).run()
    state=final_state(r)
    assert 'Group' not in [row['node'] for row in r.trace]
    assert sum(e['kind']=='evaluated' for e in state['events'])==2
    case=w.functions[w.named['StartCase']['Code']].__globals__['BANK']['cases'][cid]
    lines=['## '+case['title'], '**学生：** 我是'+group+'大类的，想试试这个情境。']
    for row in r.trace:
        if 'question' in row:
            lines += ['**助手：**',row['question']]
            if 'buttons' in row:
                lines += ['*页面上的按钮：*','\n'.join('- '+b['OptionContent'] for b in row['buttons']),
                          '**学生点击：** '+row['user_action']['raw']]
            else:
                lines += ['**学生：**',a[row['node']]]
        if 'message' in row:
            lines += ['**助手：**',row['message']]
    lines += ['**助手给出的最终记录：**',r.final]
    documents.append('\n\n'.join(lines))
    (ROOT/'cases'/('example_'+cid+'_report.md')).write_text(r.final+'\n',encoding='utf-8')
    (ROOT/'cases'/('example_'+cid+'_trace.json')).write_text(json.dumps(r.trace,ensure_ascii=False,indent=2),encoding='utf-8')
    if cid=='materials_optics':
        (ROOT/'cases/state_example.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    evidence.append({'case_id':cid,'yaml_sha256':hashlib.sha256(w.path.read_bytes()).hexdigest(),
                     'evaluated':2,'record_confirmed':state['record_confirmed'],'group_asked':False})
(ROOT/'cases/expected_usage_v2.md').write_text('\n\n'.join(header+documents)+'\n',encoding='utf-8')
(ROOT/'tests/example_replay_results.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print('Regenerated three native conversations, reports, traces and one valid current state.')
