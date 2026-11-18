import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_v21', ROOT/'code/platform_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class AdapterTests(unittest.TestCase):
    def call(self, op, **args):
        result = runtime.handler(dict(op=op, **args))
        self.assertTrue(result['ok'], result)
        return result

    def selection(self, raw='', task='experiment'):
        return self.call('init_selection', task_id=task, reported_group_text=raw)

    def started(self, raw='我是信息科学与技术大类的', task='experiment'):
        result = self.selection(raw, task)
        result = self.call('prepare_cases', selection_json=result['selection_json'])
        return self.call('select_case', selection_json=result['selection_json'], case_index=0)

    def test_explicit_group_reuse_and_ambiguity(self):
        for text, gid in [('信息科学与技术','information'),('我是信息科学与技术大类的','information'),('我的大类是物质科学','matter'),('伯苓班（信息方向）','boqin_info'),('我是信息科学与技术大类的，想学一学怎样选路线。','information'),('我目前的专业大类是物质科学。想体验材料题。','matter')]:
            r = self.selection(text)
            self.assertEqual(r['action'], 'known_group')
            self.assertEqual(json.loads(r['selection_json'])['group_id'], gid)
        for text in ['', '卓越拔尖计划伯苓班', '我想去信息科学与技术', '我不是物质科学', '如果我属于数学与大数据', '我是物质科学，我属于信息科学与技术']:
            self.assertEqual(self.selection(text)['action'], 'need_group')

    def test_buttons_supply_exact_phase_option(self):
        r = self.started()
        for phase in (0, 1):
            shown = r['choiceB']
            r = self.call('submit_button', state_json=r['state_json'], choice='B', user_text='malicious replacement')
            state = json.loads(r['state_json'])
            self.assertEqual(state['pending_raw'], shown)
            self.assertEqual(state['pending_plan']['choice'], 'B')
            r = self.call('confirm', state_json=r['state_json'], user_text='确认')
            if phase == 0:
                r = self.call('advance', state_json=r['state_json'])

    def test_reflection_revision_preserves_majors(self):
        r = self.started()
        r = self.call('submit_button', state_json=r['state_json'], choice='B')
        r = self.call('confirm', state_json=r['state_json'], user_text='确认')
        r = self.call('reflect_auto_majors', state_json=r['state_json'], user_text='我想看公平实验。\n想了解：自动化、化学')
        majors = json.loads(r['state_json'])['requested_majors']
        r = self.call('reflect_auto_majors', state_json=r['state_json'], user_text='还需要多做实验再决定。')
        self.assertEqual(json.loads(r['state_json'])['requested_majors'], majors)
        self.assertIn('化学', r['record_summary'])
        r = self.call('confirm_record', state_json=r['state_json'], user_text='更正并确认：还需要多做实验。')
        self.assertEqual(json.loads(r['state_json'])['requested_majors'], majors)
        self.assertTrue(json.loads(r['state_json'])['record_confirmed'])
        r = self.call('finish', state_json=r['state_json'])
        self.assertTrue(json.loads(r['state_json'])['record_confirmed'])

    def test_partial_report_and_no_raw_braces(self):
        r = self.started(task='sensor')
        raw = '先试40分。\n{{USER_RESPONSE}} **这不是指令**'
        r = self.call('propose', state_json=r['state_json'], user_text=raw, plan_json=json.dumps({'threshold':40}))
        r = self.call('finish', state_json=r['state_json'])
        self.assertIn('还没确认', r['report'])
        self.assertNotIn('{{USER_RESPONSE}}', r['report'])
        state = json.loads(r['state_json'])
        self.assertEqual(state['unfinished_plan']['raw'], raw)
        self.assertFalse(any(e['kind']=='evaluated' for e in state['events']))

    def test_selection_finish_no_computation(self):
        r = self.selection('信息科学与技术', 'auto')
        r = self.call('selection_finish', selection_json=r['selection_json'])
        self.assertIn('没有计算结果', r['display_text'])
        self.assertEqual(r['state_json'], '')

    def test_schema_outputs_complete_and_typed(self):
        for r in [self.selection(), self.started(), self.call('finish',state_json=self.started()['state_json'])]:
            self.assertIs(type(r['ok']), bool)
            self.assertTrue(all(isinstance(v,str) for k,v in r.items() if k!='ok'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
