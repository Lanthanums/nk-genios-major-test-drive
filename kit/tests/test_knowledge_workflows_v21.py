"""Execute the actual two knowledge graphs with explicit retrieval/model fixtures."""
from pathlib import Path
import unittest
from native_replay import Workflow, Replay

ROOT=Path(__file__).resolve().parents[1]
URL='https://example.edu.cn/fixture'
QUOTE='比较观察结果需要说明数据来自哪些对象'
HITS=[{'output':QUOTE+'。来源：'+URL,'metadata':{'document_url':URL,'score':0.9,'document_name':'本地夹具'}}]


class KnowledgeGraphs(unittest.TestCase):
    def test_actual_knowledge_graph_validated_answer_and_empty(self):
        w=Workflow(ROOT/'platform_import/WF_Major_Knowledge_v2.yaml');w.check()
        model={'answer':'先说明观察对象和条件。','citations':[{'quote':QUOTE,'source_url':URL}],'missing':'没有实际课程信息。'}
        r=Replay(w,{}, {'query':'数据分析在做什么'},knowledge=HITS,models={'AnswerLLM':lambda p,r:model}).run()
        self.assertIn(URL,r.final);self.assertIn('##',r.final)
        r=Replay(w,{}, {'query':'未知问题'},models={'AnswerLLM':lambda p,r:'malformed'}).run()
        self.assertIn('还没有找到',r.final)

    def test_actual_draft_graph_checked_and_rejected(self):
        w=Workflow(ROOT/'platform_import/WF_KB_Practice_Draft_v2.yaml');w.check()
        draft=dict(title='比较两份观察',scenario='教学合成数据来自两个班级。',question='需要先了解什么？',options={'A':'只比平均值','B':'核对样本对象','C':'删除较小值'},reason_prompt='说明理由。',changed_condition='现在有了收集时间。',concept='证据可比性',source_evidence=[{'quote':QUOTE,'why_relevant':'支持核对对象。'}],limits='模型草拟，尚未学科审核，不评分。')
        r=Replay(w,{}, {'query':'证据练习'},knowledge=HITS,models={'DraftLLM':lambda p,r:draft}).run()
        self.assertIn('尚未学科审核',r.final)
        self.assertTrue(r.result('DraftCheck')['ok'])
        r=Replay(w,{}, {'query':'未知练习'},models={'DraftLLM':lambda p,r:draft}).run()
        self.assertFalse(r.result('DraftCheck')['ok'])
        self.assertIn('没有',r.final)
