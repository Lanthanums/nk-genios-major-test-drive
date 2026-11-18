from pathlib import Path
import importlib.util
import json
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('support_under_test',ROOT/'code/platform_support.py')
support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)

class KnowledgeTests(unittest.TestCase):
    def hit(self):
        return [{'output':'比较测量结果需要说明参考与测试条件，不能只看一个数值。原URL：https://www.nim.ac.cn/node/213','metadata':{'score':0.9,'document_name':'测试夹具','document_url':'https://www.nim.ac.cn/node/213'}}]
    def answer(self):
        return {'answer':'先说明参考与测量条件。','citations':[{'quote':'比较测量结果需要说明参考与测试条件','source_url':'https://www.nim.ac.cn/node/213'}],'missing':'当前资料不提供具体设备参数。'}
    def draft(self):
        return {'title':'两次测量怎样比较','scenario':'合成对象两次读数不同，尚未记录测试条件。','question':'先收集什么证据？','options':{'A':'只选较大值','B':'记录参考和条件','C':'删掉一个值'},'reason_prompt':'说明你的考虑。','changed_condition':'新增一次参考测量。','concept':'可比性','source_evidence':[{'quote':'比较测量结果需要说明参考与测试条件','why_relevant':'说明比较需要明确条件。'}],'limits':'模型草稿，尚未学科审核，不作评分。'}
    def test_every_group_member_profile_has_valid_sources(self):
        groups=json.loads((ROOT/'config/major_groups.json').read_text(encoding='utf-8'))['groups']
        profiles=json.loads((ROOT/'config/major_profiles.json').read_text(encoding='utf-8'))['profiles']
        sources=json.loads((ROOT/'references/source_register.json').read_text(encoding='utf-8'))['sources']
        names={p['major'] for p in profiles};ids={s['id'] for s in sources}
        self.assertEqual(len(profiles),33);self.assertEqual(len(sources),36)
        for g in groups.values():self.assertTrue(set(g['majors'])<=names)
        for p in profiles:self.assertTrue(p['source_ids'] and set(p['source_ids'])<=ids)
    def test_knowledge_cards_and_case_provenance(self):
        cards=list((ROOT/'knowledge_base').glob('*.md'));self.assertEqual(len(cards),65)
        for p in cards:
            text=p.read_text(encoding='utf-8');self.assertIn('文档ID：',text);self.assertIn('2.2.0' if p.name in {'00_scope.md','05_faq.md','09_how_to_choose.md'} or p.name.startswith('10_major_') else '2.0.0',text);self.assertNotIn('日期：None',text)
        registry=json.loads((ROOT/'references/source_register.json').read_text(encoding='utf-8'));ids={s['id'] for s in registry['sources']}
        self.assertGreaterEqual(len(registry['excluded_sources']),3)
        bank=json.loads((ROOT/'config/case_bank.json').read_text(encoding='utf-8'))
        for c in bank['cases'].values():self.assertTrue(c['source_ids'] and set(c['source_ids'])<=ids)
    def test_grounded_answer_and_empty_retrieval(self):
        self.assertTrue(support.validate_answer({'hits':self.hit(),'answer_json':json.dumps(self.answer(),ensure_ascii=False)})['ok'])
        empty=support.validate_answer({'hits':[],'answer_json':'malformed'})
        self.assertIn('还没有找到',empty['final_text']);self.assertNotIn('https://',empty['final_text'])
    def test_unsupported_quote_and_hidden_missing_link_rejected(self):
        a=self.answer();a['citations'][0]['quote']='这段依据不在原始资料里面'
        self.assertFalse(support.validate_answer({'hits':self.hit(),'answer_json':json.dumps(a,ensure_ascii=False)})['ok'])
        a=self.answer();a['missing']='请参阅 https://invented.invalid/policy'
        self.assertFalse(support.validate_answer({'hits':self.hit(),'answer_json':json.dumps(a,ensure_ascii=False)})['ok'])
    def test_bad_score_or_bad_hit_does_not_crash(self):
        hit=self.hit();hit[0]['metadata']['score']=float('nan')
        result=support.retrieval_context({'hits':hit});self.assertEqual(result['hit_count'],1)
        self.assertIsNone(json.loads(result['context'])[0]['score'])
        self.assertEqual(support.retrieval_context({'hits':{'wrong':'type'}})['hit_count'],0)
    def test_draft_provenance_and_real_url_pass(self):
        draft=self.draft();draft['scenario']+=' 参考 https://www.nim.ac.cn/node/213'
        self.assertTrue(support.validate_practice_draft({'hits':self.hit(),'draft':json.dumps(draft,ensure_ascii=False)})['ok'])
        draft['source_evidence'][0]['quote']='不存在的原文依据片段'
        self.assertFalse(support.validate_practice_draft({'hits':self.hit(),'draft':json.dumps(draft,ensure_ascii=False)})['ok'])
