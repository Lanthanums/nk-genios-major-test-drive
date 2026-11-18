"""Meaningful replay, numerical invariants and state/confirmation regression tests."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('runtime_under_test',ROOT.parent/'code'/'engine.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)

class RuntimeTests(unittest.TestCase):
    def start(self,cid='sensor_luggage',group='physics_opto',confirmed=True,**extra):
        r=engine.dispatch(dict(op='start',case_id=cid,group_id=group,group_confirmed=confirmed,**extra))
        self.assertTrue(r['ok'],r);return r

    def call(self,r,op,**args):
        out=engine.dispatch(dict(op=op,state_json=r['state_json'],**args))
        self.assertTrue(out['ok'],out);return out

    def propose(self,r,plan,text='这是我本轮方案'):
        return self.call(r,'propose',plan_json=engine.dumps(plan),user_text=text)

    def test_catalog_is_9_by_3_and_no_answer_leak(self):
        catalog=json.loads(engine.dispatch({'op':'catalog'})['catalog_json'])
        self.assertEqual(len(catalog['families']),9)
        self.assertEqual(len(catalog['cases']),27)
        for family in catalog['families']:
            self.assertEqual(sum(c['task_id']==family for c in catalog['cases']),3)
        for cid in engine.BANK['cases']:
            r=self.start(cid)
            self.assertNotIn('outcomes',r['normalizer_context'])
            self.assertTrue(r['knowledge_query'])

    def test_27_case_complete_two_phase_and_record_replay(self):
        count=0
        for cid,c in engine.BANK['cases'].items():
            with self.subTest(cid=cid):
                r=self.start(cid)
                task=c['task_id']
                if task=='route':plan={'path':['S','A','T']}
                elif task=='sensor':plan={'threshold':40}
                elif task=='control':plan={'k':0.6}
                else:plan={'choice':'B'}
                r=self.propose(r,plan)
                self.assertEqual(r['action'],'awaiting_confirmation')
                self.assertEqual(r['result_json'],'')
                r=self.call(r,'confirm',user_text='确认')
                self.assertEqual(r['action'],'evaluated')
                phase0=json.loads(r['result_json'])
                r=self.call(r,'advance')
                self.assertEqual(r['phase'],1)
                self.assertEqual(r['case_id'],cid)
                if engine.BANK['families'][task]['mode']=='choice':
                    self.assertEqual(r['result_json'],'')
                    events=json.loads(r['state_json'])['events']
                    self.assertNotIn('recomputed',[e['kind'] for e in events])
                    self.assertIn(engine.quoted(c['data']['options'][0][plan['choice']]),r['feedback'])
                else:self.assertEqual(json.loads(r['result_json'])['phase'],1)
                r=self.propose(r,plan)
                r=self.call(r,'confirm',user_text='确认试算')
                self.assertEqual(json.loads(r['result_json'])['phase'],1)
                raw='比较条件很有意思，但我还不确定是否想长期学习。'
                r=self.call(r,'reflect',user_text=raw,majors=['电子信息科学与技术','自动化'])
                self.assertIn(raw,r['report'])
                self.assertIn('草稿',r['report'])
                r=self.call(r,'confirm_record',user_text='确认记录')
                self.assertEqual(r['action'],'completed')
                self.assertIn('本人已确认',r['report'])
                state=json.loads(r['state_json'])
                self.assertEqual(state['reflection_raw'],raw)
                self.assertEqual(len([e for e in state['events'] if e['kind']=='evaluated']),2)
                self.assertEqual(state['events'][2]['result'],phase0)
                count+=1
        self.assertEqual(count,27)

    def test_choice_all_options_phases_use_reviewed_outcomes(self):
        labels=dict(A=0,B=0,C=0)
        for cid,c in engine.BANK['cases'].items():
            if engine.BANK['families'][c['task_id']]['mode']!='choice':continue
            for phase in (0,1):
                self.assertEqual(set(c['data']['options'][phase]),{'A','B','C'})
                self.assertEqual(set(c['data']['outcomes'][phase]),{'A','B','C'})
                self.assertTrue(any(x['supported_by_stated_criteria'] for x in c['data']['outcomes'][phase].values()))
                for k,v in c['data']['outcomes'][phase].items():
                    if v['supported_by_stated_criteria']:labels[k]+=1
                for choice in 'ABC':
                    result=engine.evaluate(cid,{'choice':choice},phase)
                    self.assertEqual(result['feedback'],c['data']['outcomes'][phase][choice]['feedback'])
        self.assertEqual(labels,dict(A=12,B=12,C=12))

    def test_original_numeric_fixture_results(self):
        self.assertEqual(engine.evaluate('route_campus',{'path':['S','A','B','C','T']},0)['minutes'],8)
        self.assertFalse(engine.evaluate('route_campus',{'path':['S','A','B','C','T']},1)['valid'])
        self.assertEqual(engine.evaluate('route_campus',{'path':['S','A','C','T']},1)['minutes'],9)
        self.assertEqual(engine.evaluate('sensor_luggage',{'threshold':40},0)['loss'],2)
        self.assertEqual(engine.evaluate('sensor_luggage',{'threshold':40},1)['loss'],10)
        self.assertEqual(engine.evaluate('sensor_luggage',{'threshold':65},1)['loss'],3)
        self.assertEqual(engine.evaluate('control_cart',{'k':0.6},0)['trajectory'][-1],0.986159)

    def test_route_constraints_are_not_silently_repaired(self):
        r=engine.evaluate('route_coldchain',{'path':['S','A','C','T']},0)
        self.assertTrue(r['meets_deadline']);self.assertEqual(r['minutes'],9)
        r=engine.evaluate('route_coldchain',{'path':['S','A','C','T']},1)
        self.assertEqual(r['minutes'],12);self.assertFalse(r['meets_deadline']);self.assertFalse(r['any_path_meets_deadline'])
        r=engine.evaluate('route_relay',{'path':['S','A','T']},1)
        self.assertFalse(r['valid']);self.assertIsNone(r['minutes'])
        self.assertEqual(r['reference_min_minutes'],7)

    def test_sensor_counts_partition_and_loss_arithmetic(self):
        for cid,c in engine.BANK['cases'].items():
            if c['task_id']!='sensor':continue
            for phase in (0,1):
                for t in [0,31,40,65,100]:
                    r=engine.evaluate(cid,{'threshold':t},phase)
                    self.assertEqual(sum(r[x] for x in ['tp','fp','fn','tn']),len(c['data']['samples']))
                    self.assertEqual(r['loss'],r['fp']*r['false_alarm_weight']+r['fn']*r['miss_weight'])
        # Equality must be positive rather than an accidental > comparison.
        r=engine.evaluate('sensor_luggage',{'threshold':42},0)
        self.assertEqual(r['fn'],0)

    def test_control_trajectory_obeys_recurrence_and_limit(self):
        for cid,c in engine.BANK['cases'].items():
            if c['task_id']!='control':continue
            for phase in (0,1):
                for k in [0,0.6,2]:
                    r=engine.evaluate(cid,{'k':k},phase)
                    xs=r['trajectory'];us=r['controls']
                    self.assertEqual(len(xs),c['data']['steps']+1)
                    for i,u in enumerate(us):
                        self.assertLessEqual(abs(u),r['actuator_limit']+1e-9)
                        self.assertAlmostEqual(xs[i+1],xs[i]+r['gain']*u-r['disturbance'],places=5)
        self.assertEqual(engine.evaluate('control_storage',{'k':2},1)['actuator_limit'],0.1)

    def test_ambiguous_confirmation_keeps_pending_and_recovers(self):
        r=self.propose(self.start(),{'threshold':40})
        before=json.loads(r['state_json'])
        for text in ['可能吧','随便','你替我选','确认65还是40','好的？']:
            r=self.call(r,'confirm',user_text=text)
            self.assertEqual(r['action'],'need_confirmation')
            self.assertEqual(r['result_json'],'')
            self.assertIn('40',r['preview'])
            self.assertIn('还没有开始试算',r['preview'])
            self.assertEqual(json.loads(r['state_json'])['pending_plan'],before['pending_plan'])
        r=self.call(r,'confirm',user_text='那65吧')
        self.assertEqual(r['action'],'awaiting_confirmation')
        self.assertEqual(json.loads(r['state_json'])['pending_plan']['threshold'],65)
        r=self.call(r,'confirm',user_text='保持方案')
        self.assertEqual(json.loads(r['result_json'])['plan']['threshold'],65)

    def test_explicit_replacement_confirmation(self):
        for text in ['试算65','试算 65','更正并确认：65']:
            r=self.start()
            r=self.call(r,'confirm',user_text=text)
            self.assertEqual(r['action'],'evaluated')
            self.assertEqual(json.loads(r['result_json'])['plan']['threshold'],65)
        r=self.propose(self.start(),{'threshold':40},text='我先试40')
        r=self.call(r,'confirm',user_text='试算65')
        r=self.call(r,'report')
        self.assertIn('你当时说的是：\n\n> 试算65',r['report'])
        self.assertNotIn('> 我先试40',r['report'])

    def test_hint_and_stop_retained_no_inference(self):
        r=self.start('experiment_growth')
        r=self.call(r,'propose',user_text='不确定')
        self.assertEqual(r['action'],'hint')
        self.assertNotIn('适合',r['feedback'])
        r=self.call(r,'propose',user_text='结束体验')
        self.assertEqual(r['action'],'stopped')
        self.assertIn('你还没有填写感受',r['report'])
        retry=engine.dispatch({'op':'advance','state_json':r['state_json']})
        self.assertTrue(retry['ok']);self.assertEqual(retry['action'],'report');self.assertEqual(json.loads(retry['state_json']),json.loads(r['state_json']))

    def test_model_clarification_and_bad_quote_cannot_execute(self):
        r=self.start('experiment_growth')
        out=self.call(r,'propose',user_text='A或者B吧',candidate_json=engine.dumps({'action':'clarify','plan':{},'quote':'A或者B','question':'你希望先选择A还是B？'}))
        self.assertEqual(out['action'],'clarify')
        self.assertIsNone(json.loads(out['state_json'])['pending_plan'])
        out=engine.dispatch({'op':'propose','state_json':r['state_json'],'user_text':'我选A','candidate_json':engine.dumps({'action':'submit','plan':{'choice':'B'},'quote':'我选B'})})
        self.assertFalse(out['ok'])
        out=engine.dispatch({'op':'propose','state_json':r['state_json'],'user_text':'我选A','plan_json':engine.dumps({'choice':'A','reason':'我热爱研究'})})
        self.assertFalse(out['ok'])

    def test_scope_group_unknown_and_same_name_special_class(self):
        r=self.start(group='future')
        out=self.call(r,'scope',majors=['材料化学','材料化学（新材料特色班）','自动化','不存在的专业'])
        s=json.loads(out['scope_json'])
        self.assertEqual(s['within_group'],['材料化学（新材料特色班）'])
        self.assertEqual(s['cross_group'],['材料化学','自动化'])
        self.assertEqual(s['unverified'],['不存在的专业'])
        r=self.start(group='unknown',confirmed=False)
        out=self.call(r,'scope',majors=['材料化学'])
        self.assertEqual(json.loads(out['scope_json'])['unverified'],['材料化学'])
        r=self.start(group='future',confirmed=False)
        out=self.call(r,'scope',majors=['材料化学（新材料特色班）'])
        self.assertEqual(json.loads(out['scope_json'])['within_group'],[])

    def test_record_correction_preserves_facts(self):
        r=self.propose(self.start(),{'threshold':40})
        r=self.call(r,'confirm',user_text='确认')
        result=copy.deepcopy(json.loads(r['state_json'])['last_result'])
        r=self.call(r,'reflect',user_text='原来的反思')
        r=self.call(r,'confirm_record',user_text='更正并确认： 这是新的本人原话，不代表已经喜欢某个专业。')
        state=json.loads(r['state_json'])
        self.assertEqual(state['reflection_raw'],' 这是新的本人原话，不代表已经喜欢某个专业。')
        self.assertEqual(state['last_result'],result)
        self.assertTrue(state['record_confirmed'])

    def test_choice_report_preserves_each_phase_option_and_student_reason(self):
        cid='experiment_catalyst';case=engine.BANK['cases'][cid]
        r=self.start(cid)
        original0='我选A，因为先固定温度'
        original1='我选A，因为新问题还要比较温度'
        r=self.propose(r,{'choice':'A','reason':'先固定温度'},text=original0)
        r=self.call(r,'confirm',user_text='确认')
        r=self.call(r,'advance')
        r=self.propose(r,{'choice':'A','reason':'新问题还要比较温度'},text=original1)
        r=self.call(r,'confirm',user_text='确认')
        r=self.call(r,'report')
        self.assertNotEqual(case['data']['options'][0]['A'],case['data']['options'][1]['A'])
        first=engine.preview_plan({'choice':'A','reason':'先固定温度'},case,0)
        second=engine.preview_plan({'choice':'A','reason':'新问题还要比较温度'},case,1)
        self.assertIn(first,r['report']);self.assertIn(second,r['report'])
        self.assertIn(original0,r['report']);self.assertIn(original1,r['report'])

    def test_invalid_numeric_inputs_and_state_are_rejected(self):
        for task,key in [('sensor_luggage','threshold'),('control_cart','k')]:
            for value in [True,float('nan'),float('inf'),-1,101,'0.6',10**400]:
                with self.assertRaises(ValueError):engine.evaluate(task,{key:value},0)
        with self.assertRaises(ValueError):engine.evaluate('sensor_luggage',{'threshold':40},True)
        for value in ['[]','{"x":NaN}','{"x":Infinity}']:
            self.assertFalse(engine.dispatch(value)['ok'])
        r=self.start();s=json.loads(r['state_json']);s['case_version']='stale'
        self.assertFalse(engine.dispatch({'op':'report','state_json':engine.dumps(s)})['ok'])

    def test_deterministic_auto_selection_exclusion_and_legacy_alias(self):
        args=dict(op='start',task_id='auto',group_id='digital_finance',group_confirmed=True,seed='student-7')
        r=engine.dispatch(args);self.assertTrue(r['ok'])
        self.assertEqual(r['case_id'],engine.dispatch(args)['case_id'])
        self.assertIn(r['task_id'],engine.GROUP_FAMILIES['digital_finance'])
        new=engine.dispatch(dict(args,exclude_case_ids=[r['case_id']]))
        self.assertNotEqual(new['case_id'],r['case_id'])
        for task,cid in [('route','route_campus'),('sensor','sensor_luggage'),('senor','sensor_luggage'),('control','control_cart')]:
            self.assertEqual(engine.dispatch({'op':'start','task_id':task})['case_id'],cid)
        legacy=engine.dispatch({'op':'start','task_id':'route','exclude_case_ids':['route_campus']})
        self.assertTrue(legacy['ok']);self.assertNotEqual(legacy['case_id'],'route_campus')
        self.assertFalse(engine.dispatch(dict(args,exclude_case_ids=list(engine.BANK['cases'])))['ok'])
        self.assertFalse(engine.dispatch({'op':'start','task_id':'route','case_id':'sensor_water'})['ok'])

    def test_out_of_order_and_duplicate_calculation_blocked(self):
        r=self.start()
        self.assertFalse(engine.dispatch({'op':'advance','state_json':r['state_json']})['ok'])
        self.assertFalse(engine.dispatch({'op':'reflect','state_json':r['state_json'],'user_text':'猜测'})['ok'])
        r=self.propose(r,{'threshold':40});r=self.call(r,'confirm',user_text='确认')
        self.assertFalse(engine.dispatch({'op':'confirm','state_json':r['state_json'],'user_text':'确认'})['ok'])
        r=self.call(r,'advance')
        self.assertFalse(engine.dispatch({'op':'advance','state_json':r['state_json']})['ok'])

    def test_failed_mutation_returns_exact_original_state(self):
        r=self.propose(self.start(),{'threshold':40})
        r=self.call(r,'confirm',user_text='确认')
        before=json.loads(r['state_json'])
        failed=engine.dispatch({'op':'reflect','state_json':r['state_json'],'user_text':'不能写入的反思','majors':'自动化'})
        self.assertFalse(failed['ok'])
        self.assertEqual(json.loads(failed['state_json']),before)
        self.assertEqual(json.loads(failed['state_json'])['reflection_raw'],'')

    def test_independently_reviewed_case_arithmetic(self):
        def correct(cid,phase):
            case=engine.BANK['cases'][cid]
            choice=next(k for k,v in case['data']['outcomes'][phase].items() if v['supported_by_stated_criteria'])
            return engine.evaluate(cid,{'choice':choice},phase)
        self.assertEqual(correct('materials_adsorption',1)['checks']['A_cumulative'],27)
        self.assertIn('含首次在内共可使用3次',engine.BANK['cases']['materials_adsorption']['phases'][1])
        self.assertIn('共新增4份',''.join(engine.BANK['cases']['resource_samples']['data']['options'][1].values()))
        self.assertEqual(correct('finance_fraud',1)['checks']['loss'],80)
        self.assertEqual(correct('finance_publicdata',1)['checks']['net_minutes_saved'],-400)

if __name__=='__main__':unittest.main(verbosity=2)
