"""Replays of actual lifecycle/exit/rendering concerns; not platform execution."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runtime_v21',ROOT.parent/'code/engine.py')
engine=importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def call(previous,op,**kwargs):
    r=engine.dispatch(dict(op=op,state_json=previous['state_json'],**kwargs))
    assert r['ok'],r
    return r


def start(cid='sensor_luggage'):
    result=engine.dispatch(dict(op='start',case_id=cid,group_id='physics_opto',group_confirmed=True,cohort='2026级'))
    assert result['ok'],result
    return result


def plan_for(cid):
    task=engine.BANK['cases'][cid]['task_id']
    return {'route':{'path':['S','A','T']},'sensor':{'threshold':40},'control':{'k':0.6}}.get(task,{'choice':'B'})


def stages(cid='sensor_luggage'):
    p=plan_for(cid)
    current=start(cid)
    states=[current]
    current=call(current,'propose',plan_json=engine.dumps(p),user_text='先试这个方案。')
    states.append(current)
    current=call(current,'confirm',user_text='按这个方案试一试')
    states.append(current)
    current=call(current,'advance')
    states.append(current)
    current=call(current,'propose',plan_json=engine.dumps(p),user_text='我还是想试这个方案。')
    states.append(current)
    current=call(current,'confirm',user_text='确认')
    states.append(current)
    current=call(current,'reflect',user_text='我还没有想好。',majors=[])
    states.append(current)
    current=call(current,'confirm_record',user_text='确认记录')
    states.append(current)
    return states


class RuntimeRepairs(unittest.TestCase):
    def test_exit_at_every_stage_all_27_cases(self):
        for cid in engine.BANK['cases']:
            for r in stages(cid):
                before=json.loads(r['state_json'])
                for op in ['finish','stop','propose','confirm','reflect','confirm_record','advance']:
                    with self.subTest(cid=cid,stage=before['status'],op=op):
                        out=call(r,op,user_text='我做完两次了，想结束，直接拿到报告')
                        after=json.loads(out['state_json'])
                        self.assertEqual(out['action'],'stopped')
                        self.assertTrue(out['report'].startswith('# '))
                        self.assertEqual([x for x in before['events'] if x['kind']=='evaluated'],[x for x in after['events'] if x['kind']=='evaluated'])
                        self.assertEqual(after['record_confirmed'],before['record_confirmed'])
                        self.assertEqual(out['result_json'],'')

    def test_stop_preserves_unconfirmed_proposal(self):
        r=call(start(),'propose',user_text='我想用40分。',plan_json='{"threshold":40}')
        r=call(r,'finish',user_text='结束并给我报告')
        self.assertIn('已提出、还没确认',r['report'])
        self.assertIn('没有试算',r['report'])
        self.assertNotIn('总代价',r['report'])
        self.assertEqual(json.loads(r['state_json'])['unfinished_plan']['raw'],'我想用40分。')

    def test_explicit_finish_natural_variants(self):
        yes=['结束','退出','结束并给我报告','直接拿到报告','不想继续了，生成报告','不想继续做了，给我报告吧','做完两次了想结束','已经试了两次，我想直接拿报告','先到这里','我不想继续了','给我一份报告','我做了两次了，直接出报告吧']
        no=['不想结束','不要结束，我还要继续','不用生成报告，继续做','我不是要结束','我还不想退出','如果结束了会怎样','结束后会有报告吗','你说的“结束并给我报告”是什么意思','刚才想结束，现在想继续','我认为“退出”按钮有问题','不结束','不要生成报告','我不想继续了吗','我看到了结束按钮','我认为退出按钮有问题','这个实验以反应结束时间为指标']
        for text in yes:self.assertTrue(engine.wants_finish(text),text)
        for text in no:self.assertFalse(engine.wants_finish(text),text)

    def test_model_alone_cannot_invent_end_intent(self):
        r=call(start(),'propose',user_text='我还没想好分数',candidate_json='{"action":"stop"}')
        self.assertEqual(r['action'],'clarify')
        self.assertNotEqual(json.loads(r['state_json'])['status'],'stopped')

    def test_markdown_quote_does_not_append_punctuation(self):
        raw='这次比较有意思。\n# 不要把这行变标题\n**这不是强调**\n[链接](https://example.com)\n{{USER_RESPONSE}}。'
        r=stages()[5]
        r=call(r,'reflect',user_text=raw)
        state=json.loads(r['state_json'])
        self.assertEqual(state['reflection_raw'],raw)
        self.assertEqual(state['events'][-1]['raw_text'],raw)
        self.assertIn('> 这次比较有意思。\n> \\#',r['report'])
        self.assertNotIn('\n# 不要',r['report'])
        self.assertNotIn('{{USER_RESPONSE}}',r['report'])
        self.assertNotIn('。。',r['report'])

    def test_finished_twice_has_no_duplicate_events(self):
        r=call(stages()[5],'finish',user_text='结束并给我报告')
        r2=call(r,'finish',user_text='再给我看看报告')
        self.assertEqual(r['state_json'],r2['state_json'])
        r3=call(r2,'confirm',user_text='确认')
        self.assertEqual(r3['action'],'report')
        self.assertEqual(r2['state_json'],r3['state_json'])

    def test_27_reports_have_no_backend_identifiers(self):
        for cid in engine.BANK['cases']:
            r=call(stages(cid)[5],'finish',user_text='结束')
            for forbidden in ['case_id','state_json','awaiting_plan','auto','phase','plan_json',cid]:
                self.assertNotIn(forbidden,r['display_text'])
            self.assertIn('##',r['report'])
            self.assertIn('**',r['report'])
            self.assertIn('*资料边界',r['report'])

    def test_failed_input_retains_report_and_valid_state(self):
        r=stages()[2]
        out=engine.dispatch(dict(op='propose',state_json=r['state_json'],user_text='再选40',plan_json='{"threshold":40}'))
        self.assertFalse(out['ok'])
        self.assertEqual(out['state_json'],r['state_json'])
        self.assertIn('总代价',out['report'])
        self.assertNotIn('advance',out['display_text'])
        self.assertNotIn('ValueError',out['display_text'])
        self.assertIn('直接结束',out['display_text'])

    def test_skip_uncertain_reflection_logs_without_invented_interest(self):
        r=call(stages()[5],'reflect',user_text='不确定')
        state=json.loads(r['state_json'])
        self.assertEqual(state['reflection_raw'],'')
        self.assertEqual(state['events'][-1]['raw_text'],'不确定')
        self.assertFalse(state['record_confirmed'])
        r=call(r,'finish',user_text='结束并给我报告')
        self.assertIn('还没有填写感受',r['report'])

    def test_natural_reflection_revision_does_not_auto_confirm(self):
        r=stages()[6]
        r=call(r,'confirm_record',user_text='我想改一下：其实还需要试试电路。')
        self.assertEqual(r['action'],'need_record_confirmation')
        self.assertFalse(json.loads(r['state_json'])['record_confirmed'])
        self.assertEqual(json.loads(r['state_json'])['reflection_raw'],'我想改一下：其实还需要试试电路。')
        r=call(r,'confirm_record',user_text='确认记录')
        self.assertEqual(r['action'],'completed')

    def test_numeric_core_matches_9_golden_snapshots(self):
        golden=json.loads((ROOT.parent/'cases/golden_results.json').read_text(encoding='utf-8-sig'))
        fields={'route':['valid','minutes','reference_min_minutes'],'sensor':['tp','fp','fn','tn','loss','false_alarm_weight','miss_weight'],'control':['trajectory','controls','final_abs_error','max_overshoot','within_observation_settled_step','meets_teaching_target']}
        count=0
        for entry in golden:
            for result_key,plan_key,phase in [('base_result','base_plan',0),('challenge_result','base_plan',1),('revision_result','revision_plan',1)]:
                actual=engine.evaluate(engine.DEFAULTS[entry['task_id']],entry[plan_key],phase)
                for field in fields[entry['task_id']]:self.assertEqual(actual[field],entry[result_key][field])
                count+=1
        self.assertEqual(count,9)

    def test_control_prompt_shows_all_update_inputs(self):
        for cid,case in engine.BANK['cases'].items():
            if case['task_id']!='control':continue
            for phase in [0,1]:
                data=case['data']
                prompt=engine.task_text(case,phase)
                for required in [str(data['initial']),str(data['target']),str(data['steps']),str(data['gains'][phase]),str(data.get('disturbances',[0,0])[phase]),str(data.get('limits',[data.get('limit',2)]*2)[phase])]:
                    self.assertIn(required,prompt)
                self.assertIn('下一步的位置',prompt)
                self.assertIn('实际调整量',prompt)


if __name__=='__main__':
    unittest.main(verbosity=2)
