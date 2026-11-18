"""Source acceptance rules and Markdown presentation regression tests."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('support_v21',ROOT/'code/platform_support.py')
support=importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)

URL='https://example.edu.cn/source'
QUOTE='传感系统需要比较误报和漏报的代价'
HITS=[{'output':'领域说明。'+QUOTE+'。资料仅支持教学概念。','metadata':{'document_name':'教学概念来源','document_url':URL,'score':0.82}}]
ANSWER={'answer':'**核心区别：** 需要比较不同错误的代价。','citations':[{'quote':QUOTE,'source_url':URL}],'missing':'缺少真实设备验证。'}


class SupportFormatting(unittest.TestCase):
    def answer(self,value,hits=None):
        return support.validate_answer({'hits':HITS if hits is None else hits,'answer_json':json.dumps(value,ensure_ascii=False)})

    def test_valid_answer_formatted_without_quote_punctuation(self):
        r=self.answer(ANSWER)
        self.assertTrue(r['ok'])
        self.assertIn('### 这次参考的原文\n\n',r['final_text'])
        self.assertIn('> '+QUOTE+'\n\n',r['final_text'])
        self.assertNotIn(QUOTE+'；',r['final_text'])
        self.assertIn('### 目前还缺少什么',r['final_text'])

    def test_made_up_quote_still_rejected(self):
        a=copy.deepcopy(ANSWER)
        a['citations'][0]['quote']='这是并不存在的来源原文'
        r=self.answer(a)
        self.assertFalse(r['ok'])
        self.assertNotIn('引用片段不在',r['final_text'])
        self.assertIn('diagnostic',r)

    def test_mismatched_source_url_still_rejected(self):
        a=copy.deepcopy(ANSWER)
        a['citations'][0]['source_url']='https://other.example.edu.cn/unread'
        self.assertFalse(self.answer(a)['ok'])

    def test_prose_invented_url_still_rejected(self):
        a=copy.deepcopy(ANSWER)
        a['answer']+=' https://other.example.edu.cn/unread'
        self.assertFalse(self.answer(a)['ok'])

    def test_no_hits_do_not_synthesize_answer(self):
        r=self.answer(ANSWER,[])
        self.assertTrue(r['ok'])
        self.assertIn('还没有找到',r['final_text'])
        self.assertNotIn(ANSWER['answer'],r['final_text'])

    def test_valid_practice_is_marked_draft(self):
        draft={'title':'选一条检测分界线','scenario':'使用合成数据比较误报和漏报。','question':'你会先比较什么？','options':{'A':'只看误报','B':'比较两种错误与代价','C':'只看漏报'},'reason_prompt':'说一个你最关心的因素即可。','changed_condition':'误报的代价提高。','concept':'错误代价','source_evidence':[{'quote':QUOTE,'why_relevant':'说明应比较两种错误。'}],'limits':'模型草拟，尚未学科审核，不进入客观评分题库。'}
        r=support.validate_practice_draft({'hits':HITS,'draft':json.dumps(draft,ensure_ascii=False)})
        self.assertTrue(r['ok'])
        self.assertIn('还没有经过学科审核',r['final_text'])
        self.assertIn('- **方案 A：**',r['final_text'])
        self.assertIn('> '+QUOTE+'\n\n',r['final_text'])

    def test_invalid_practice_source_still_rejected(self):
        r=support.validate_practice_draft({'hits':HITS,'draft':'{"title":"不完整"}'})
        self.assertFalse(r['ok'])
        self.assertEqual(r['draft_json'],'')
        self.assertIn('还需要检查',r['final_text'])

    def test_quote_escapes_student_markup(self):
        rendered=support._literal_quote('# 标题\n**强调**\n{{USER_RESPONSE}}。')
        self.assertTrue(rendered.startswith('> \\#'))
        self.assertNotIn('{{USER_RESPONSE}}',rendered)
        self.assertNotIn('。。',rendered)


if __name__=='__main__':
    unittest.main(verbosity=2)
