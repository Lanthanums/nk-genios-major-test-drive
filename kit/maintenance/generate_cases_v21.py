"""Generate full expected conversations; all runtime text/results are executed.

The student/Agent lines and entry/button choices are explicitly simulated.
No LLM or knowledge retrieval is claimed. Usage:
python maintenance/generate_cases_v21.py [--runtime PATH_TO_EMBEDDED_ENGINE]
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(runtime_path):
    spec=importlib.util.spec_from_file_location('case_engine_v21',runtime_path)
    engine=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    case_dir=ROOT/'cases'
    case_dir.mkdir(exist_ok=True)
    evidence=[]

    def case(slug,title):
        return {'slug':slug,'lines':['# '+title,'*预期对话：双方发言、入口信息和选择为模拟。题面、方案预览、反馈与最终报告由当前运行代码实际产生；没有登录平台，没有模拟成真实知识检索。此处不插入未经实际检索的专业解释。*'],'trace':[]}

    def say(c,role,text):
        c['lines']+=['### '+role,text]

    def step(c,previous=None,**params):
        request=dict(params)
        if previous is not None:request['state_json']=previous['state_json']
        out=engine.dispatch(request)
        assert out['ok'],out
        c['trace'].append({'input':request,'output':out})
        return out

    def show(c,r):
        say(c,'系统',r['display_text'])

    def save(c,r):
        state=json.loads(r['state_json'])
        assert state['cohort']=='未知'
        assert '年级为本人填写' not in r['report']
        assert not state['record_confirmed']
        c['lines']+=['---','*案例核对：以上报告只包含真实执行的试算；学生没有填写反思，也没有确认整份记录。结束后没有自动开启下一次体验。后台请求和完整输出另见同名trace文件。*']
        md=case_dir/(c['slug']+'.md')
        md.write_text('\n\n'.join(c['lines'])+'\n',encoding='utf-8')
        trace_path=case_dir/(c['slug']+'_trace.json')
        trace_path.write_text(json.dumps(c['trace'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (case_dir/(c['slug']+'_state.json')).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        evidence.append({'case':c['slug'],'operations':len(c['trace']),'evaluated':sum(e['kind']=='evaluated' for e in state['events']),'action':r['action'],'record_confirmed':state['record_confirmed'],'markdown_sha256':hashlib.sha256(md.read_bytes()).hexdigest(),'trace_sha256':hashlib.sha256(trace_path.read_bytes()).hexdigest()})

    c=case('expected_first_round_exit_v21','第一次试算后就结束：完整预期案例')
    say(c,'学生','我是信息科学与技术大类的。最近听大家说计算机要学算法，但我没写过程序。先试试找路线这种活动吧。')
    say(c,'智能体','好，我们从一个具体的小问题开始。过程中可以随时结束，已经做过的部分会写进记录。')
    c['lines'].append('*入口复用本人已经明确的大类，不再次提问；本例选定路线情境。未收集年级或经历，不把“没写过程序”解释成能力。*')
    say(c,'学生（情境选择）','选择校园路线这个情境。')
    r=step(c,op='start',task_id='route',case_id='route_campus',group_id='information',group_confirmed=True,cohort='未知')
    show(c,r)
    raw='从S出发，经过A、B、C，再到T。我先选这条，单段时间看起来都不长。'
    say(c,'学生',raw)
    r=step(c,r,op='propose',user_text=raw,plan_json=engine.dumps({'path':['S','A','B','C','T'],'reason':'单段时间看起来都不长'}))
    show(c,r)
    say(c,'学生（点击按钮）','就按这个试')
    r=step(c,r,op='confirm',user_text='确认')
    assert json.loads(r['result_json'])['minutes']==8
    show(c,r)
    say(c,'系统','## 还想继续看看吗？\n\n接下来会改变一个条件，看看原来的做法还是否合适。也可以就到这里，查看已经完成的记录。\n\n可选：**换个条件，再试一次** / **到这里，查看记录**')
    say(c,'学生（点击按钮）','到这里，查看记录')
    r=step(c,r,op='finish',user_text='')
    show(c,r)
    assert len([e for e in json.loads(r['state_json'])['events'] if e['kind']=='evaluated'])==1
    assert '条件变化后：本人确认的新方案' not in r['report']
    save(c,r)

    c=case('expected_two_rounds_report_v21','两次试算后直接拿报告：完整预期案例')
    say(c,'学生','我想体验一下，我对设备怎么判断有没有东西挺好奇的。')
    say(c,'智能体','好，我们从一个具体的小问题开始。过程中可以随时结束，已经做过的部分会写进记录。')
    c['lines'].append('*本例入口尚未收到本人所属大类，工作流显示一次大类按钮。大类和情境界面为预期入口说明；实际按钮效果仍需平台验收。*')
    say(c,'系统','## 先记一下你当前的大类\n\n你现在属于下面哪一个大类？这只用于区分类内选择和跨类兴趣。\n\n*不清楚也能继续体验，不会据此判断你适合什么。*\n\n可选：未来产业精英；信息科学与技术；物理与光电信息技术工程；物质科学；数智经济金融；卓越拔尖计划伯芩班（计算机、智能科学、光电组）；数学与大数据；卓越拔尖计划伯芩班（物理、量子信息、化学、生物组）；不清楚，或者暂不提供；先不做了。')
    say(c,'学生（大类选择）','选择“物理与光电信息技术工程”。')
    say(c,'系统','## 想从哪种小问题开始？\n\n选一个你愿意试试的就好。它只是这次活动的内容，不是在替你选专业。\n\n可选：安排一条合适的路线；让设备少一些误报和漏报；让运动或温度更稳一点；设计一次公平的对比实验；看看一份数据能说明什么；资源有限时怎样分配；找出一个系统为什么出了错；比较材料性能和使用条件；分析一次经济选择和它的证据；先不做了。')
    say(c,'学生（活动选择）','让设备少一些误报和漏报')
    say(c,'学生（情境选择）','选择行李检测的情境。')
    r=step(c,op='start',task_id='sensor',case_id='sensor_luggage',group_id='physics_opto',group_confirmed=True,cohort='未知')
    show(c,r)
    raw='我先设40分。42分已经有行李了，我更担心漏掉，所以想把分界线放低一点。'
    say(c,'学生',raw)
    r=step(c,r,op='propose',user_text=raw,plan_json=engine.dumps({'threshold':40,'reason':'我更担心漏掉'}))
    show(c,r)
    say(c,'学生（点击按钮）','就按这个试')
    r=step(c,r,op='confirm',user_text='确认')
    assert json.loads(r['result_json'])['loss']==2
    show(c,r)
    say(c,'系统','## 还想继续看看吗？\n\n接下来会改变一个条件，看看原来的做法还是否合适。也可以就到这里，查看已经完成的记录。\n\n可选：**换个条件，再试一次** / **到这里，查看记录**')
    say(c,'学生（点击按钮）','换个条件，再试一次')
    r=step(c,r,op='advance')
    assert json.loads(r['result_json'])['loss']==10
    show(c,r)
    raw='那就改成65分吧。\n误报现在代价更高，我愿意先少报一点，再看看漏掉了哪些。'
    say(c,'学生',raw)
    r=step(c,r,op='propose',user_text=raw,plan_json=engine.dumps({'threshold':65,'reason':'误报现在代价更高'}))
    show(c,r)
    say(c,'学生（点击按钮）','就按这个试')
    r=step(c,r,op='confirm',user_text='确认')
    assert json.loads(r['result_json'])['loss']==3
    show(c,r)
    say(c,'系统','## 两次尝试已经完成\n\n你可以补一句自己的感受，也可以直接查看记录。没有感受或还不确定，都没关系。\n\n可选：**说说这次的感受** / **直接查看记录**')
    say(c,'学生（点击按钮）','直接查看记录')
    r=step(c,r,op='finish',user_text='')
    assert r['action']=='stopped'
    show(c,r)
    assert len([e for e in json.loads(r['state_json'])['events'] if e['kind']=='evaluated'])==2
    assert json.loads(r['state_json'])['reflection_raw']==''
    save(c,r)

    summary={'kind':'expected_dialogues_with_executed_runtime','engine_version':engine.ENGINE_VERSION,'runtime_sha256':hashlib.sha256(Path(runtime_path).read_bytes()).hexdigest(),'cases':evidence,'boundary':'Student and Agent lines and entry/button choices are simulated; task, preview, calculations and reports are real local runtime outputs; no platform import, live model or actual retrieval.'}
    (case_dir/'expected_v21_replay_results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',type=Path,default=ROOT/'code'/'engine.py')
    args=parser.parse_args()
    print(json.dumps(run(args.runtime),ensure_ascii=False,indent=2))
