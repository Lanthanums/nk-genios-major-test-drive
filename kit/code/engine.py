"""Deterministic activity exploration runtime v4, Python standard library only.

All teaching data are original synthetic fixtures, not university assignments.
BANK/CATALOG are embedded by standalone generation. No model or network calls.

v4 additions over v2.x:
- New non-arithmetic modes: rank (价值排序), allocation (优先级听证/一天拼图),
  compose (失败复盘). Model still only extracts; code validates and records.
- Surface variants: seeded deterministic re-skinning of names/framing/card
  subsets/option order. No seed -> variant 0, fully reproducible.
- Report gate: finish/stop (or explicit natural-language finish) first returns
  action "report_gate" WITHOUT any report. Only report_final (button or clear
  natural consent after the gate) renders the record, and the thoughts entrance
  is an explicit prominent question at the gate, never a hidden postscript.
"""
import copy
import hashlib
import heapq
import json
import math
import re
import html

ENGINE_VERSION = "4.0.0"
BANK = {'schema_version': '2.0.0', 'case_version': '2026-10-17.v4.0', 'origin': '原创合成教学案例；不是大学真实作业、设备数据、医疗或投资建议', 'families': {'route': {'name': '网络与路径', 'mode': 'route', 'concept_tags': ['图', '约束', '最短路'], 'related_majors': ['计算机科学与技术', '软件工程', '信息与计算科学'], 'boundary': '未体验真实编程、复杂度证明或系统工程；找路表现不能判断专业适配。'}, 'sensor': {'name': '阈值与误判', 'mode': 'sensor', 'concept_tags': ['阈值', '混淆矩阵', '误判代价'], 'related_majors': ['电子信息科学与技术', '智能科学与技术', '统计学', '数据科学'], 'boundary': '只在给定小样本计算，没有真实器件标定、泛化评估或临床验证。'}, 'control': {'name': '反馈与动态', 'mode': 'control', 'concept_tags': ['反馈', '增益', '超调'], 'related_majors': ['自动化', '物联网工程', '新能源科学与工程（数智能源特色班）'], 'boundary': '归一化离散玩具模型，无真实设备、稳定性证明、时延与安全验证。'}, 'experiment': {'name': '实验对照', 'mode': 'choice', 'concept_tags': ['控制变量', '重复', '混杂'], 'related_majors': ['化学', '应用化学', '生物科学', '生物技术（生物智造特色班）'], 'boundary': '只比较合成实验方案，不提供真实实验操作步骤，也不代表大学实验完整过程。'}, 'evidence': {'name': '数据与证据', 'mode': 'choice', 'concept_tags': ['抽样', '数据泄漏', '不确定性'], 'related_majors': ['统计学', '数据科学', '数学与应用数学', '量子信息科学'], 'boundary': '练习证据边界，未进行统计推断证明、真实量子实验或专业适配测量。'}, 'resource': {'name': '资源与权衡', 'mode': 'choice', 'concept_tags': ['约束优化', '资源调度', '公平'], 'related_majors': ['新能源科学与工程（数智能源特色班）', '信息与计算科学', '通信工程', '数字经济'], 'boundary': '只比较离散合成方案，不模拟真实电网、网络或实验室全部约束。'}, 'debug': {'name': '排错与系统', 'mode': 'choice', 'concept_tags': ['边界测试', '标定', '协议'], 'related_majors': ['软件工程', '计算机科学与技术', '信息安全', '物联网工程', '通信工程'], 'boundary': '日志和现象是人工设计的最小例子，没有对真实系统做安全测试或工程诊断。'}, 'materials': {'name': '材料与性能', 'mode': 'choice', 'concept_tags': ['性能约束', '多目标取舍', '测量条件'], 'related_majors': ['材料化学', '材料物理', '应用物理学', '光电信息科学与工程', '微电子科学与工程', '电子科学与技术'], 'boundary': '所有性能为合成数值，没有真实材料配方、寿命或制造可行性结论。'}, 'finance': {'name': '经济与决策', 'mode': 'choice', 'concept_tags': ['因果识别', '基准率', '成本收益'], 'related_majors': ['数字经济', '金融科技', '统计学'], 'boundary': '不是投资建议、金融产品推荐或风控部署方案；只体验给定假设下的计算与证据判断。'}, 'story': {'name': '叙事两难', 'mode': 'choice'}, 'values': {'name': '价值排序', 'mode': 'rank'}, 'hearing': {'name': '优先级听证', 'mode': 'allocation'}, 'daylife': {'name': '一天拼图', 'mode': 'allocation'}, 'failure': {'name': '失败复盘', 'mode': 'compose'}}, 'cases': {'route_campus': {'case_id': 'route_campus', 'task_id': 'route', 'variant_id': 'campus', 'title': '雨天行李转运', 'context': '从S到T选择较省时路线；图为双向，未列边不存在。', 'phases': ['正常通行。', 'B-C双向封闭，其余边不变。'], 'data': {'edges': [['S', 'A', 2], ['S', 'B', 4], ['A', 'B', 1], ['A', 'C', 4], ['B', 'C', 2], ['B', 'T', 7], ['C', 'T', 3], ['A', 'T', 9]], 'blocked': [[], [['B', 'C']]], 'start': 'S', 'end': 'T', 'unit': '分钟'}, 'hint': '先列完整路径，再逐段检查是否有边。封闭边仍可提交，系统会指出不可行。', 'reflection': '你比较路线时最先检查了什么条件？条件变化后保留或修改了哪一步？', 'knowledge_tags': ['图', '约束', '最短路'], 'related_majors': ['计算机科学与技术', '信息与计算科学'], 'boundary': '未体验真实编程、复杂度证明或系统工程；找路表现不能判断专业适配。', 'source_concepts': ['图', '约束', '最短路'], 'source_ids': ['STEM-S01', 'STEM-S02', 'STEM-S13', 'STEM-S14'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'route_coldchain': {'case_id': 'route_coldchain', 'task_id': 'route', 'variant_id': 'coldchain', 'title': '冷链包裹赶时限', 'context': '合成冷链包裹从S到T，第一阶段必须12分钟内到达。第二阶段交接时限收紧到9分钟。先检查能否按时，再比较耗时。', 'phases': ['到达时限12分钟。', '到达时限9分钟，A-C新增3分钟等待。'], 'data': {'edges': [['S', 'A', 3], ['S', 'B', 2], ['A', 'C', 2], ['B', 'C', 5], ['A', 'T', 9], ['C', 'T', 4], ['B', 'T', 10]], 'blocked': [[], []], 'edge_additions': [[], [['A', 'C', 3]]], 'deadlines': [12, 9], 'start': 'S', 'end': 'T', 'unit': '分钟'}, 'hint': '注意最短路线与满足时限是两个问题；约束可能使所有路线都无法按时。', 'reflection': '没有路线能按时的时候，你会报告什么，而不是偷偷更改数据？', 'knowledge_tags': ['图', '约束', '最短路'], 'related_majors': ['计算机科学与技术', '数学与应用数学', '数字经济'], 'boundary': '未体验真实编程、复杂度证明或系统工程；找路表现不能判断专业适配。', 'source_concepts': ['图', '约束', '最短路'], 'source_ids': ['STEM-S01', 'STEM-S02', 'STEM-S13', 'LE-DIGITAL'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'route_relay': {'case_id': 'route_relay', 'task_id': 'route', 'variant_id': 'relay', 'title': '中继网络延迟', 'context': '合成数据包从S经中继到T；边权为毫秒，第一阶段无额外限制。', 'phases': ['各链路正常。', 'A-T掉线，B-T增加4毫秒排队。'], 'data': {'edges': [['S', 'A', 2], ['S', 'B', 3], ['A', 'B', 2], ['A', 'T', 4], ['B', 'C', 1], ['C', 'T', 3], ['B', 'T', 5]], 'blocked': [[], [['A', 'T']]], 'edge_additions': [[], [['B', 'T', 4]]], 'start': 'S', 'end': 'T', 'unit': '毫秒'}, 'hint': '把网络看作带权图，延迟相加。模型没有模拟丢包、吞吐量和协议。', 'reflection': '低延迟与可靠性是一回事吗？本题的数据支持回答哪一部分？', 'knowledge_tags': ['图', '约束', '最短路'], 'related_majors': ['通信工程', '物联网工程', '计算机科学与技术'], 'boundary': '未体验真实编程、复杂度证明或系统工程；找路表现不能判断专业适配。', 'source_concepts': ['图', '约束', '最短路'], 'source_ids': ['STEM-S12', 'STEM-S18', 'STEM-S03', 'STEM-S02', 'STEM-S01'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'sensor_luggage': {'case_id': 'sensor_luggage', 'task_id': 'sensor', 'variant_id': 'luggage', 'title': '行李检测的两种错误', 'context': '选择0至100阈值t，分数>=t判为有行李；1确有、0没有。', 'phases': ['误报代价1，漏报代价3。', '误报代价5，漏报代价1。'], 'data': {'samples': [[10, 0], [20, 0], [35, 0], [42, 1], [48, 0], [52, 1], [58, 1], [60, 0], [65, 1], [72, 1], [80, 1], [90, 1]], 'weights': [[1, 3], [5, 1]], 'positive_label': '有行李'}, 'hint': '误报是实际没有却判有，漏报是实际有却判没有；代价要分别乘数量。', 'reflection': '代价改变后，你愿意用什么换取更少的另一类错误？', 'knowledge_tags': ['阈值', '混淆矩阵', '误判代价'], 'related_majors': ['电子信息科学与技术', '统计学', '智能科学与技术'], 'boundary': '只在给定小样本计算，没有真实器件标定、泛化评估或临床验证。', 'source_concepts': ['阈值', '混淆矩阵', '误判代价'], 'source_ids': ['STEM-S09', 'STEM-S18', 'STEM-S15', 'STEM-S05'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'sensor_water': {'case_id': 'sensor_water', 'task_id': 'sensor', 'variant_id': 'water', 'title': '水质异常的提醒规则', 'context': '这是虚构水质指数，不对应真实检测限。指数>=t触发复核，标签1仅表示合成样本已知异常。', 'phases': ['复核误报代价2，漏掉异常代价6。', '复核资源紧张：误报代价7，漏报代价6；样本不变。'], 'data': {'samples': [[12, 0], [24, 0], [31, 1], [40, 0], [44, 1], [52, 0], [57, 1], [68, 1], [73, 0], [84, 1]], 'weights': [[2, 6], [7, 6]], 'positive_label': '需复核的异常'}, 'hint': '这不是饮用水安全判定，只比较教学规则；阈值不能从这个例子直接用于真实环境。', 'reflection': '复核资源改变能否让异常本身消失？模型里的代价代表什么？', 'knowledge_tags': ['阈值', '混淆矩阵', '误判代价'], 'related_majors': ['应用化学', '统计学', '电子信息科学与技术'], 'boundary': '只在给定小样本计算，没有真实器件标定、泛化评估或临床验证。', 'source_concepts': ['阈值', '混淆矩阵', '误判代价'], 'source_ids': ['LE-APPLIED', 'STEM-S15', 'STEM-S09', 'STEM-S18', 'CONCEPT-NIM-REFERENCE'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'sensor_artifact': {'case_id': 'sensor_artifact', 'task_id': 'sensor', 'variant_id': 'artifact', 'title': '脑电伪迹标记', 'context': '虚构伪迹分数>=t标为待人工复查；1=人工合成标签为伪迹。不是脑机设备或医学数据。', 'phases': ['误标正常片段代价3，漏标伪迹代价2。', '分析目标更重视干净信号：误标代价1，漏标代价6。'], 'data': {'samples': [[8, 0], [18, 0], [29, 0], [37, 1], [45, 0], [51, 1], [63, 0], [70, 1], [79, 1], [94, 1]], 'weights': [[3, 2], [1, 6]], 'positive_label': '伪迹'}, 'hint': '代价反映当前分析任务的假设，不是对人的诊断。没有一个阈值能保证无错误。', 'reflection': '为什么同一批信号换了分析目标以后，可能要换标记规则？', 'knowledge_tags': ['阈值', '混淆矩阵', '误判代价'], 'related_majors': ['智能医学工程（脑机接口特色班）', '智能科学与技术（具身与行为智能特色班）', '统计学'], 'boundary': '只在给定小样本计算，没有真实器件标定、泛化评估或临床验证。', 'source_concepts': ['阈值', '混淆矩阵', '误判代价'], 'source_ids': ['LE-MED', 'LE-FUTURE-2026', 'LE-POLICY-2026', 'LE-FUTURE-PROGRESS', 'STEM-S05', 'STEM-S15'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'control_cart': {'case_id': 'control_cart', 'task_id': 'control', 'variant_id': 'cart', 'title': '转运小车纠偏', 'context': '归一化小车目标1，初始0。每步u=clip(k*(target-x),-2,2)，x_next=x+g*u，共12步；k范围0至2。', 'phases': ['响应系数g=0.5。', '响应系数g=1.5。'], 'data': {'initial': 0, 'target': 1, 'gains': [0.5, 1.5], 'steps': 12, 'limit': 2, 'error_target': 0.05, 'overshoot_limit': 0.25}, 'hint': '增益k越大纠正越猛，但可能超过目标。有限12步的现象不是稳定性证明。', 'reflection': '接近目标的速度与超过目标的幅度之间，你观察到什么取舍？', 'knowledge_tags': ['反馈', '增益', '超调'], 'related_majors': ['自动化', '智能科学与技术', '物联网工程'], 'boundary': '归一化离散玩具模型，无真实设备、稳定性证明、时延与安全验证。', 'source_concepts': ['反馈', '增益', '超调'], 'source_ids': ['STEM-S05', 'STEM-S03', 'STEM-S02'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'control_greenhouse': {'case_id': 'control_greenhouse', 'task_id': 'control', 'variant_id': 'greenhouse', 'title': '温室的简化调节', 'context': '归一化温室状态目标1，初始0.2；每步u=clip(k*(1-x),-0.8,0.8)，x_next=x+g*u-d，共15步。不是实际温度或种植建议。', 'phases': ['g=0.7，持续扰动d=0.04。', 'g=0.7，持续扰动d=0.16。'], 'data': {'initial': 0.2, 'target': 1, 'gains': [0.7, 0.7], 'disturbances': [0.04, 0.16], 'steps': 15, 'limit': 0.8, 'error_target': 0.05, 'overshoot_limit': 0.25}, 'hint': '即使有反馈，持续扰动也可能留下稳态偏差；检查末端误差而非只看最初几步。', 'reflection': '提高k能完全消除持续扰动吗？这个简单控制器还缺少什么信息？', 'knowledge_tags': ['反馈', '增益', '超调'], 'related_majors': ['自动化', '物联网工程'], 'boundary': '归一化离散玩具模型，无真实设备、稳定性证明、时延与安全验证。', 'source_concepts': ['反馈', '增益', '超调'], 'source_ids': ['STEM-S05', 'STEM-S03', 'STEM-S02'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'control_storage': {'case_id': 'control_storage', 'task_id': 'control', 'variant_id': 'storage', 'title': '储能功率平滑', 'context': '归一化储能输出目标0.8，初始0；u=clip(k*(0.8-x),-0.4,0.4)，x_next=x+g*u，共10步。', 'phases': ['g=0.6。', '功率调整限幅由0.4收紧为0.1；g不变。'], 'data': {'initial': 0, 'target': 0.8, 'gains': [0.6, 0.6], 'steps': 10, 'limits': [0.4, 0.1], 'error_target': 0.05, 'overshoot_limit': 0.2}, 'hint': '限幅后，大k不一定能继续提升前几步的速度。先观察u是否总被截到上限。新条件下每步状态最多增0.06，10步最多到0.6，允许结论是只改k无法达到目标，不要勉强凑参数。', 'reflection': '当执行器有限额时，只改控制参数还能解决所有速度问题吗？', 'knowledge_tags': ['反馈', '增益', '超调'], 'related_majors': ['新能源科学与工程（数智能源特色班）', '自动化'], 'boundary': '归一化离散玩具模型，无真实设备、稳定性证明、时延与安全验证。', 'source_concepts': ['反馈', '增益', '超调'], 'source_ids': ['LE-ENERGY', 'LE-FUTURE-2026', 'LE-POLICY-2026', 'LE-FUTURE-PROGRESS', 'STEM-S05'], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'experiment_growth': {'case_id': 'experiment_growth', 'task_id': 'experiment', 'variant_id': 'growth', 'title': '生长差异是谁造成的', 'context': '某教学培养物A组平均高度12，B组9，想知道是否因营养液不同。都是合成数据。', 'phases': ['A组营养液甲且光照强，B组营养液乙且光照弱；下一批选哪个方案？', '补充：培养盒也有批次差异；仍比较营养液效应。'], 'data': {'options': [{'A': '同一批次培养盒中，随机分甲/乙营养液，两组用相同光照，做重复。', 'B': '继续比较原A/B两组，重复测高度。', 'C': '甲组加强光照，乙组减少光照，放大差异。'}, {'A': '甲/乙各只用一个培养盒，所有盒相同光照。', 'B': '在每个培养盒批次内随机分甲/乙，同光照并做重复。', 'C': '只报告最高的一个培养盒。'}], 'outcomes': [{'A': {'feedback': '减少光照混杂，并通过随机分配和重复减少偶然差异；仍不保证必然发现效应。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '重复测量原来混在一起的因素，仍不能区分营养液与光照。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '同时改变两个因素，差异更大也不能说明营养液效应。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '单盒结果仍容易与盒本身差异混在一起。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '把批次纳入分组，批次内比较营养液更符合当前问题。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '只留最高值会选择性报告，不能代表总体。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '先问除营养液之外，哪些条件也一起变了。', 'reflection': '你最想排除哪个替代解释？为什么不能只看差值大小？', 'knowledge_tags': ['控制变量', '重复', '混杂'], 'related_majors': ['生物科学', '生物技术（生物智造特色班）', '统计学'], 'boundary': '只比较合成实验方案，不提供真实实验操作步骤，也不代表大学实验完整过程。', 'source_concepts': ['控制变量', '重复', '混杂'], 'source_ids': ['LE-BIO', 'LE-FUTURE-2026', 'LE-POLICY-2026', 'LE-FUTURE-PROGRESS', 'STEM-S15'], 'display_permutation': [{'A': 'B', 'B': 'A', 'C': 'C'}, {'B': 'B', 'A': 'A', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'experiment_catalyst': {'case_id': 'experiment_catalyst', 'task_id': 'experiment', 'variant_id': 'catalyst', 'title': '催化剂还是温度', 'context': '合成反应记录：甲催化剂40℃产率80%，乙20℃产率60%；只能规划教学比较，不涉及真实配方。', 'phases': ['想比较催化剂，选择后续方案。', '新问题：还想知道催化剂效果是否随温度变化。'], 'data': {'options': [{'A': '继续甲40℃、乙20℃，测量更多位小数。', 'B': '甲加倍用量、升温，再与乙比较。', 'C': '甲乙都固定30℃，同原料批次，随机顺序重复。'}, {'A': '比较甲乙×20/40℃四个组合，其他条件相同并重复。', 'B': '只测甲30℃。', 'C': '把所有温度的数据混为一组平均。'}], 'outcomes': [{'A': {'feedback': '精度增加不能消除温度混杂。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '用量和温度也改变了，无法把差异归因于催化剂。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '固定温度后更能比较催化剂；重复仍有必要。', 'supported_by_stated_criteria': True, 'checks': {}}}, {'A': {'feedback': '四组合能观察各温度下的甲乙差异，并检查效果是否随温度变化。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '缺少乙及其他温度，不能回答变化问题。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '合并会遮蔽温度条件差异。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '比较催化剂要先固定温度；研究温度影响则要有对应的多组组合。', 'reflection': '新的研究问题改变后，为什么原来合理的设计仍可能不够？', 'knowledge_tags': ['控制变量', '重复', '混杂'], 'related_majors': ['化学', '应用化学', '材料化学'], 'boundary': '只比较合成实验方案，不提供真实实验操作步骤，也不代表大学实验完整过程。', 'source_concepts': ['控制变量', '重复', '混杂'], 'source_ids': ['LE-CHEM', 'LE-APPLIED', 'LE-MATERIAL'], 'display_permutation': [{'C': 'A', 'A': 'B', 'B': 'C'}, {'A': 'B', 'B': 'A', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'experiment_fluorescence': {'case_id': 'experiment_fluorescence', 'task_id': 'experiment', 'variant_id': 'fluorescence', 'title': '荧光更亮说明什么', 'context': '合成细胞图像中，处理组总荧光200，对照组100；不涉及药物或诊断。', 'phases': ['想知道每个细胞是否更亮。', '补充：两个批次曝光时间不同。'], 'data': {'options': [{'A': '直接声称每个细胞亮度翻倍。', 'B': '先核对细胞数和曝光，计算同条件单细胞指标。', 'C': '把图片对比度调高后肉眼判断。'}, {'A': '把两个批次总亮度直接相加。', 'B': '只保留最好看的图。', 'C': '统一曝光重测，按细胞归一化，并报告重复与背景。'}], 'outcomes': [{'A': {'feedback': '总荧光同时受细胞数、曝光和背景影响，现有信息不足。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '先核对测量条件与分母，比直接从总量推断更有根据。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '显示调整不能提供可靠定量依据。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '不同曝光下数值不能直接当作同一尺度合并。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '选择性展示不支持可靠比较。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '统一测量条件并保留重复，可减少明显混杂；仍需评估测量误差。', 'supported_by_stated_criteria': True, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '总量增加可能是个体数量增加，而非每个个体增强。', 'reflection': '总量、平均值、测量条件分别改变了什么？', 'knowledge_tags': ['控制变量', '重复', '混杂'], 'related_majors': ['生物科学', '智能医学工程（脑机接口特色班）', '生物技术（生物智造特色班）'], 'boundary': '只比较合成实验方案，不提供真实实验操作步骤，也不代表大学实验完整过程。', 'source_concepts': ['控制变量', '重复', '混杂'], 'source_ids': ['LE-BIO', 'LE-MED', 'LE-FUTURE-2026', 'LE-POLICY-2026', 'LE-FUTURE-PROGRESS', 'CONCEPT-NIM-AUDIT'], 'display_permutation': [{'B': 'B', 'A': 'A', 'C': 'C'}, {'C': 'A', 'A': 'B', 'B': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'evidence_survey': {'case_id': 'evidence_survey', 'task_id': 'evidence', 'variant_id': 'survey', 'title': '食堂满意度能代表谁', 'context': '午饭时在同一家食堂收集100份自愿问卷，80人满意。', 'phases': ['你要向学生会描述结果。', '补充：现在想比较改造前后；改造前样本来自全校随机抽样，改造后仍是这100份自愿问卷。'], 'data': {'options': [{'A': '这100位自愿受访者中80%满意，不能直接代表全校。', 'B': '全校80%的人都满意。', 'C': '样本达到100，自动消除选择偏差。'}, {'A': '把两个比例直接作差就是改造效果。', 'B': '承认抽样方法不同，先用一致且覆盖相应人群的方案收集可比数据。', 'C': '只报告更高的那个比例。'}], 'outcomes': [{'A': {'feedback': '区分样本描述与总体推断，符合已知信息。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '把方便样本推广到全校，超出了证据范围。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '样本量不自动消除选择偏差。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '人群与抽样变化也可造成比例差异，不能直接当因果效果。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '先改善可比性，再讨论改造可能的影响。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '隐藏比较条件不支持可靠结论。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '先说清楚谁被调查、谁没有进入样本。', 'reflection': '你愿意为更有代表性的数据付出什么采集成本？', 'knowledge_tags': ['抽样', '数据泄漏', '不确定性'], 'related_majors': ['统计学', '数据科学', '数字经济'], 'boundary': '练习证据边界，未进行统计推断证明、真实量子实验或专业适配测量。', 'source_concepts': ['抽样', '数据泄漏', '不确定性'], 'source_ids': ['STEM-S15', 'STEM-S16', 'LE-DIGITAL'], 'display_permutation': [{'A': 'B', 'B': 'A', 'C': 'C'}, {'B': 'B', 'A': 'A', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'evidence_leakage': {'case_id': 'evidence_leakage', 'task_id': 'evidence', 'variant_id': 'leakage', 'title': '模型98%准确率靠谱吗', 'context': '合成图片分类测试准确率98%，目标是估计对新拍摄对象的表现。', 'phases': ['发现同一张原图的裁剪图随机分到训练和测试中。', '新数据来自另一台相机，测试准确率降到70%。'], 'data': {'options': [{'A': '继续随机分裁剪图，多训练几轮。', 'B': '把测试标签加入训练，确保预测正确。', 'C': '按原图来源分组划分训练/测试，再评价。'}, {'A': '分相机报告误差，调查分布变化，保留独立新数据验证。', 'B': '删掉新相机照片，仍只报98%。', 'C': '把70%解释为学生能力不足。'}], 'outcomes': [{'A': {'feedback': '训练更久不能修复训练测试不独立。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '把测试信息用于训练会破坏独立评估。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '按原图分组减少近重复泄漏，更贴近新对象目标。', 'supported_by_stated_criteria': True, 'checks': {}}}, {'A': {'feedback': '区分环境表现并核查分布变化，符合当前证据。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '选择性删数据隐瞒了部署环境变化。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '模型结果不能用于推断个人专业能力。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '测试集应尽量模拟真正没见过的新对象。', 'reflection': '高分数和可信的评估设计，哪一部分在本题更值得先核查？', 'knowledge_tags': ['抽样', '数据泄漏', '不确定性'], 'related_majors': ['智能科学与技术', '数据科学', '软件工程'], 'boundary': '练习证据边界，未进行统计推断证明、真实量子实验或专业适配测量。', 'source_concepts': ['抽样', '数据泄漏', '不确定性'], 'source_ids': ['STEM-S05', 'STEM-S16', 'STEM-S04', 'STEM-S02'], 'display_permutation': [{'C': 'A', 'A': 'B', 'B': 'C'}, {'A': 'B', 'B': 'A', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'evidence_quantum': {'case_id': 'evidence_quantum', 'task_id': 'evidence', 'variant_id': 'quantum', 'title': '一次测量能下什么结论', 'context': '教学黑箱每次输出0或1；这不是实际量子装置，但用于体会重复测量与统计不确定性。', 'phases': ['只测一次得到1，能说什么？', '同条件独立重复100次，有54次为1；未给检测误差或理论模型。'], 'data': {'options': [{'A': '该黑箱必定永远输出1。', 'B': '只知道本次输出1，无法凭一次确定输出概率。', 'C': '概率精确为50%，无需更多信息。'}, {'A': '54次为1证明黑箱坏了。', 'B': '54次为1证明一种特定量子态。', 'C': '可描述本次频率0.54，但不能把真实概率断言为精确0.54。'}], 'outcomes': [{'A': {'feedback': '一次观察不支持永远如此的概率结论。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '明确观察与未知概率的区别。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '没有给出等概率假设，不能自动取50%。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '未给正常工作时的预期输出概率、测量误差与故障标准，不能据此诊断。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '单一输出频率不足以唯一识别量子态。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '样本频率为54/100=0.54，仍有抽样不确定性，模型信息也不足。', 'supported_by_stated_criteria': True, 'checks': {'frequency': 0.54}}}], 'evidence': ['', '']}, 'hint': '不要把单次结果、样本频率和真实概率混为一谈。', 'reflection': '这个活动接触了统计思想，离真正理解量子态还缺哪些模型或实验？', 'knowledge_tags': ['抽样', '数据泄漏', '不确定性'], 'related_majors': ['量子信息科学', '物理学', '数学与应用数学'], 'boundary': '练习证据边界，未进行统计推断证明、真实量子实验或专业适配测量。', 'source_concepts': ['抽样', '数据泄漏', '不确定性'], 'source_ids': ['STEM-S17', 'STEM-S06', 'STEM-S13'], 'display_permutation': [{'B': 'B', 'A': 'A', 'C': 'C'}, {'C': 'A', 'A': 'B', 'B': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'resource_energy': {'case_id': 'resource_energy', 'task_id': 'resource', 'variant_id': 'energy', 'title': '一小时教学微电网', 'context': '三种整套调度方案都是合成离散选项；不用于真实电网。负荷10单位。', 'phases': ['成本越低越好；须供电>=10，排放<=5。', '设备检修导致原供10、成本11、排放4的方案只能供8；排放上限收紧至3。'], 'data': {'options': [{'A': '供10，成本11，排放4。', 'B': '供10，成本9，排放6。', 'C': '供12，成本14，排放2。'}, {'A': '供10，成本9，排放6。', 'B': '供12，成本14，排放2。', 'C': '供8，成本11，排放4。'}], 'outcomes': [{'A': {'feedback': '供电10>=10、排放4<=5；当前满足约束选项中成本最低。', 'supported_by_stated_criteria': True, 'checks': {'supply_ok': True, 'emission_ok': True, 'cost': 11}}, 'B': {'feedback': '满足供电但排放6>5，不满足约束。', 'supported_by_stated_criteria': False, 'checks': {'supply_ok': True, 'emission_ok': False, 'cost': 9}}, 'C': {'feedback': '满足约束，但成本14高于另一可行方案的11；有更低排放的取舍。', 'supported_by_stated_criteria': False, 'checks': {'supply_ok': True, 'emission_ok': True, 'cost': 14}}}, {'A': {'feedback': '排放6>3，不满足新约束。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '供12>=10且排放2<=3，三个给定方案中只有它满足约束。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '供8<10且排放4>3，两项不满足。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '先筛掉不满足硬条件的，再比较目标成本。', 'reflection': '最便宜方案为什么未必可选？如果预算也不足该如何诚实报告？', 'knowledge_tags': ['约束优化', '资源调度', '公平'], 'related_majors': ['新能源科学与工程（数智能源特色班）', '数字经济', '信息与计算科学'], 'boundary': '只比较离散合成方案，不模拟真实电网、网络或实验室全部约束。', 'source_concepts': ['约束优化', '资源调度', '公平'], 'source_ids': ['LE-ENERGY', 'LE-FUTURE-2026', 'LE-POLICY-2026', 'LE-FUTURE-PROGRESS', 'LE-DIGITAL', 'STEM-S13', 'STEM-S14'], 'display_permutation': [{'A': 'B', 'B': 'A', 'C': 'C'}, {'B': 'C', 'A': 'A', 'C': 'B'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'resource_samples': {'case_id': 'resource_samples', 'task_id': 'resource', 'variant_id': 'samples', 'title': '有限经费怎样补样本', 'context': '合成生物研究要比较甲乙两条件；已有甲8份、乙2份。每补一份成本相同，预算只能再收4份。', 'phases': ['目标先使两组样本量更接近。', '重新规划：原有乙2份来自同一批次；撤回第一阶段补样计划，仍只有4份新预算，目标改为减少条件与批次混杂。'], 'data': {'options': [{'A': '再收甲4份，成为12:2。', 'B': '甲乙各2份，成为10:4。', 'C': '再收乙4份，成为8:6。'}, {'A': '在两个新批次中各收甲1份、乙1份，共新增4份；分批次保留对照。', 'B': '乙4份仍全从旧批次来。', 'C': '把旧乙2份复制成6行，节省经费。'}], 'outcomes': [{'A': {'feedback': '样本量差距从6扩大到10。', 'supported_by_stated_criteria': False, 'checks': {'group_gap': 10}}, 'B': {'feedback': '差距仍为6，没有改善均衡目标。', 'supported_by_stated_criteria': False, 'checks': {'group_gap': 6}}, 'C': {'feedback': '差距降为2，是三个给定方案中最接近的。', 'supported_by_stated_criteria': True, 'checks': {'group_gap': 2}}}, {'A': {'feedback': '共新增2甲2乙，没有超过4份预算；每个新批次内都有条件对照，比只加同一批乙更能检查批次解释。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '增加数量仍不能分开条件与批次。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '复制不是独立样本，不能增加真实信息。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '阶段1更关注信息独立性，不再仅比较数字是否均衡。', 'reflection': '样本数量增加和证据质量增加为什么不是同一回事？', 'knowledge_tags': ['约束优化', '资源调度', '公平'], 'related_majors': ['统计学', '生物科学', '材料化学'], 'boundary': '只比较离散合成方案，不模拟真实电网、网络或实验室全部约束。', 'source_concepts': ['约束优化', '资源调度', '公平'], 'source_ids': ['STEM-S15', 'LE-BIO', 'LE-MATERIAL'], 'display_permutation': [{'C': 'B', 'A': 'A', 'B': 'C'}, {'A': 'B', 'B': 'A', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'resource_bandwidth': {'case_id': 'resource_bandwidth', 'task_id': 'resource', 'variant_id': 'bandwidth', 'title': '共享网络怎样分配', 'context': '合成校园网络总带宽10，三个完整分配选项；最低需求为急救演示4、课堂4、下载0。', 'phases': ['先满足最低需求，再让剩余带宽用于下载。', '新增无障碍字幕流最低2；总带宽仍10。'], 'data': {'options': [{'A': '急救3、课堂3、下载4。', 'B': '急救4、课堂4、下载2。', 'C': '急救6、课堂4、下载0。'}, {'A': '急救4、课堂4、下载2、字幕0。', 'B': '急救5、课堂4、下载0、字幕2。', 'C': '急救4、课堂4、下载0、字幕2。'}], 'outcomes': [{'A': {'feedback': '总量虽10，但两个关键服务均低于最低需求。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '总量10，满足两个最低需求，并给下载2。', 'supported_by_stated_criteria': True, 'checks': {'total': 10}}, 'C': {'feedback': '满足最低需求，但按当前目标下载剩余为0，低于另一个满足约束方案的2。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '字幕0<2，不满足新需求。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '5+4+0+2=11，超过总量10。', 'supported_by_stated_criteria': False, 'checks': {'total': 11}}, 'C': {'feedback': '4+4+0+2=10，满足全部最低需求。', 'supported_by_stated_criteria': True, 'checks': {'total': 10}}}], 'evidence': ['', '']}, 'hint': '总量守恒与每项最低需求都要同时检查。', 'reflection': '新增服务后，原来的合理分配为什么需要改变？', 'knowledge_tags': ['约束优化', '资源调度', '公平'], 'related_majors': ['通信工程', '物联网工程', '信息与计算科学'], 'boundary': '只比较离散合成方案，不模拟真实电网、网络或实验室全部约束。', 'source_concepts': ['约束优化', '资源调度', '公平'], 'source_ids': ['STEM-S12', 'STEM-S18', 'STEM-S03', 'STEM-S02', 'STEM-S13', 'STEM-S14'], 'display_permutation': [{'B': 'A', 'A': 'B', 'C': 'C'}, {'C': 'B', 'A': 'A', 'B': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'debug_boundary': {'case_id': 'debug_boundary', 'task_id': 'debug', 'variant_id': 'boundary', 'title': '预约系统少处理了一人', 'context': '合成函数检查座位：若人数n<10则通过。需求写的是“最多10人”。', 'phases': ['n=9通过，n=10拒绝；选择排错行动。', '需求补充：n还必须是1至10的整数，不能接受0、负数、小数。'], 'data': {'options': [{'A': '把条件改为n<=10，并增加9/10/11边界测试。', 'B': '只测n=5，确认能通过就发布。', 'C': '把最大值改为999，避免拒绝。'}, {'A': '只用n<=10，因此-1也通过。', 'B': '验证类型及1<=n<=10，再测0/1/10/11/2.5。', 'C': '把所有数字向下取整再接受。'}], 'outcomes': [{'A': {'feedback': '与“最多10人”一致，边界测试能发现原错误。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '普通值测试不能覆盖出错边界。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '更改需求没有修复实现。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '未满足正整数约束。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '同时检查类型、上下界，覆盖新需求。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '无授权取整改变了用户输入语义。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '把自然语言需求转成可检查的边界条件。', 'reflection': '修复一个反例以后，怎样避免引入另一个错误？', 'knowledge_tags': ['边界测试', '标定', '协议'], 'related_majors': ['软件工程', '计算机科学与技术', '信息安全'], 'boundary': '日志和现象是人工设计的最小例子，没有对真实系统做安全测试或工程诊断。', 'source_concepts': ['边界测试', '标定', '协议'], 'source_ids': ['STEM-S04', 'STEM-S02', 'STEM-S01'], 'display_permutation': [{'A': 'A', 'B': 'B', 'C': 'C'}, {'B': 'B', 'A': 'A', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'debug_calibration': {'case_id': 'debug_calibration', 'task_id': 'debug', 'variant_id': 'calibration', 'title': '两个传感器总差3', 'context': '两只合成温度传感器测同一稳定参考：参考20，A读20，B读23；参考30，A读30，B读33。', 'phases': ['只针对现有两点，下一步怎么做？', '新测参考40时B读46；同一点重复读数稳定。'], 'data': {'options': [{'A': '宣布所有温度下减3都绝对准确。', 'B': '把B扔掉，因为两个读数不同。', 'C': '暂把B视作约+3偏置候选，增加参考点检查，而非立刻宣布全范围校准完成。'}, {'A': '发现偏差不是恒定3，考虑非线性或量程效应并增测参考点。', 'B': '继续宣称固定减3即可。', 'C': '删除40点，以保留漂亮直线。'}], 'outcomes': [{'A': {'feedback': '超出了两点数据覆盖范围。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '现有信息不足以断言不可修复。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '两点支持一个待验证偏置假设，但不能证明全范围。', 'supported_by_stated_criteria': True, 'checks': {}}}, {'A': {'feedback': '用新反例修正模型，符合当前数据。', 'supported_by_stated_criteria': True, 'checks': {'new_bias': 6}}, 'B': {'feedback': '40点偏差6，与固定偏置模型冲突。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '删去不利证据无法验证模型。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '现有模型能解释新点吗？重复稳定不等于数值准确。', 'reflection': '发现模型不再适用时，你更愿意重新测量还是修正模型，为什么？', 'knowledge_tags': ['边界测试', '标定', '协议'], 'related_majors': ['电子信息科学与技术', '应用物理学', '自动化'], 'boundary': '日志和现象是人工设计的最小例子，没有对真实系统做安全测试或工程诊断。', 'source_concepts': ['边界测试', '标定', '协议'], 'source_ids': ['STEM-S09', 'STEM-S18', 'STEM-S06', 'STEM-S07', 'STEM-S05', 'CONCEPT-NIM-AUDIT', 'CONCEPT-NIM-REFERENCE'], 'display_permutation': [{'C': 'A', 'A': 'B', 'B': 'C'}, {'A': 'B', 'B': 'A', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'debug_packets': {'case_id': 'debug_packets', 'task_id': 'debug', 'variant_id': 'packets', 'title': '消息为何重复扣次数', 'context': '合成消息记录含包号101、102、102、103；每收到一次就扣一个配额。协议允许重传。', 'phases': ['想避免同一业务被重复计数。', '补充：设备重启后序号会从1重新开始，两个设备也可用相同序号。'], 'data': {'options': [{'A': '所有重复序号都当新业务。', 'B': '按包号识别同一业务，在规定窗口内去重。', 'C': '每隔一条丢弃，无需识别。'}, {'A': '只用裸序号永久去重。', 'B': '把网络重传功能全部取消就必然可靠。', 'C': '联合设备ID、会话ID和序号识别业务，并明确窗口与持久化需求。'}], 'outcomes': [{'A': {'feedback': '重复102会造成同一业务被重复计数。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '显式处理重传，避免记录中102被重复扣费；窗口定义仍需设计。', 'supported_by_stated_criteria': True, 'checks': {'unique_sequences': 3}}, 'C': {'feedback': '无规则丢弃也会丢掉合法业务。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '重启和不同设备会产生冲突，裸序号不足。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '不重传会影响丢包恢复，不能据此保证可靠。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '扩大标识上下文，能区分新旧会话；完整实现仍需考虑并发和故障。', 'supported_by_stated_criteria': True, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '先定义怎样算“同一笔业务”，再谈去重。', 'reflection': '系统边界一扩大，原本足够的标识为什么会不够？', 'knowledge_tags': ['边界测试', '标定', '协议'], 'related_majors': ['物联网工程', '通信工程', '信息安全'], 'boundary': '日志和现象是人工设计的最小例子，没有对真实系统做安全测试或工程诊断。', 'source_concepts': ['边界测试', '标定', '协议'], 'source_ids': ['STEM-S03', 'STEM-S02', 'STEM-S12', 'STEM-S18'], 'display_permutation': [{'B': 'A', 'A': 'B', 'C': 'C'}, {'C': 'B', 'A': 'A', 'B': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'materials_shell': {'case_id': 'materials_shell', 'task_id': 'materials', 'variant_id': 'shell', 'title': '轻量外壳怎么选', 'context': '合成外壳候选：只按给定质量、耐热与成本做选择，不是真实材料牌号。', 'phases': ['耐热>=80，质量<=5；在可行方案中成本最低。', '目标改为耐热>=110、质量<=5；成本仍越低越好。'], 'data': {'options': [{'A': '质量4，耐热90，成本8。', 'B': '质量6，耐热130，成本7。', 'C': '质量5，耐热120，成本12。'}, {'A': '质量4，耐热90，成本8。', 'B': '质量5，耐热120，成本12。', 'C': '质量6，耐热130，成本7。'}], 'outcomes': [{'A': {'feedback': '同时满足质量与耐热，成本8低于另一可行方案的12。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '质量6>5，虽然便宜也不可行。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '满足约束，但当前成本高于成本8的另一可行方案；留有更高耐热余量。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '耐热90<110，不再满足新条件。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '质量5<=5、耐热120>=110，给定方案中只有它可行。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '质量仍超过上限。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '性能名称本身不决定好坏，要和使用要求一起看。', 'reflection': '更高性能是否总值得付出更多成本？哪些未给的性质可能推翻结论？', 'knowledge_tags': ['性能约束', '多目标取舍', '测量条件'], 'related_majors': ['材料物理', '材料化学（新材料特色班）', '应用物理学'], 'boundary': '所有性能为合成数值，没有真实材料配方、寿命或制造可行性结论。', 'source_concepts': ['性能约束', '多目标取舍', '测量条件'], 'source_ids': ['LE-MATERIAL', 'LE-FUTURE-2026', 'LE-POLICY-2026', 'LE-FUTURE-PROGRESS', 'STEM-S06', 'STEM-S07', 'CONCEPT-NIM-MATERIAL-COMPARISON'], 'display_permutation': [{'A': 'A', 'B': 'B', 'C': 'C'}, {'B': 'C', 'A': 'A', 'C': 'B'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'materials_adsorption': {'case_id': 'materials_adsorption', 'task_id': 'materials', 'variant_id': 'adsorption', 'title': '吸附材料比较要除以什么', 'context': '合成测试中甲用2克去除18毫克，乙用1克去除12毫克；都在同浓度、同时间、同溶液体积。', 'phases': ['只比较本次单位质量去除量。', '补充：甲含首次在内共可使用3次，每次去除量仍18毫克；乙只能用一次；比较累计每克去除量，未计再生成本。'], 'data': {'options': [{'A': '甲18>12，所以单位质量一定更强。', 'B': '不考虑用量，只比较颜色深浅。', 'C': '甲9毫克/克、乙12毫克/克，本次乙更高。'}, {'A': '甲累计27毫克/克、乙12毫克/克；按该指标甲更高，但未计再生成本。', 'B': '甲累计54毫克/克，因为忘记除以2克。', 'C': '乙永远最好，不随目标变化。'}], 'outcomes': [{'A': {'feedback': '总量未除以投入质量，不能回答单位质量问题。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '未给颜色与去除量关系，无法替代定量指标。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '18/2=9，12/1=12，比较尺度一致。', 'supported_by_stated_criteria': True, 'checks': {'A_mg_per_g': 9, 'B_mg_per_g': 12}}}, {'A': {'feedback': '甲18×3/2=27，乙12×1/1=12；结论受回用假设和成本边界限制。', 'supported_by_stated_criteria': True, 'checks': {'A_cumulative': 27, 'B_cumulative': 12}}, 'B': {'feedback': '54是累计总去除量，仍需除以2克。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '评价目标从单次变为累计，排序可能改变。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '先明确分母和使用次数，再讨论哪种更好。', 'reflection': '单次性能、生命周期性能与总成本分别对应什么问题？', 'knowledge_tags': ['性能约束', '多目标取舍', '测量条件'], 'related_majors': ['材料化学', '应用化学', '材料化学（新材料特色班）'], 'boundary': '所有性能为合成数值，没有真实材料配方、寿命或制造可行性结论。', 'source_concepts': ['性能约束', '多目标取舍', '测量条件'], 'source_ids': ['LE-MATERIAL', 'LE-APPLIED', 'LE-FUTURE-2026', 'LE-POLICY-2026', 'LE-FUTURE-PROGRESS', 'CONCEPT-NIM-MATERIAL-COMPARISON'], 'display_permutation': [{'C': 'B', 'A': 'A', 'B': 'C'}, {'A': 'A', 'B': 'B', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'materials_optics': {'case_id': 'materials_optics', 'task_id': 'materials', 'variant_id': 'optics', 'title': '透明薄膜的取舍', 'context': '合成光学薄膜记录透过率（通过光的比例）、方阻（薄膜导电阻碍指标，越低越易导电）、弯折后导电性能保持率（越高表示性能保留越多）；不对应实际器件。', 'phases': ['透过率>=85%，方阻<=20；可行方案中优先透过率高。', '产品改为柔性屏，还要求弯折后保持率>=90%。'], 'data': {'options': [{'A': '透过率86%，方阻16，弯折保持95%。', 'B': '透过率90%，方阻18，弯折保持70%。', 'C': '透过率94%，方阻25，弯折保持98%。'}, {'A': '透过率90%，方阻18，弯折保持70%。', 'B': '透过率94%，方阻25，弯折保持98%。', 'C': '透过率86%，方阻16，弯折保持95%。'}], 'outcomes': [{'A': {'feedback': '满足条件，但透过率低于90%的另一可行方案；有更好弯折表现。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '透过率90%与86%的方案均满足约束，按优先透过率90%更高。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '方阻25>20，不满足条件。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '弯折保持70%<90%，不满足新要求。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '弯折很好但方阻仍超限。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '86>=85、16<=20、95>=90，三个条件都满足。', 'supported_by_stated_criteria': True, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '逐项列检查表，不能只盯一项看起来很好的数字。', 'reflection': '应用场景变化如何改变材料选择？本题没告诉你的制造因素有哪些？', 'knowledge_tags': ['性能约束', '多目标取舍', '测量条件'], 'related_majors': ['光电信息科学与工程', '微电子科学与工程', '电子科学与技术', '材料物理'], 'boundary': '所有性能为合成数值，没有真实材料配方、寿命或制造可行性结论。', 'source_concepts': ['性能约束', '多目标取舍', '测量条件'], 'source_ids': ['STEM-S08', 'STEM-S10', 'STEM-S11', 'LE-MATERIAL', 'CONCEPT-NIM-MATERIAL-COMPARISON'], 'display_permutation': [{'B': 'A', 'A': 'B', 'C': 'C'}, {'C': 'B', 'A': 'A', 'B': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'finance_promotion': {'case_id': 'finance_promotion', 'task_id': 'finance', 'variant_id': 'promotion', 'title': '优惠券带来了增长吗', 'context': '合成商店本周发券且销量120，上周未发券销量100。', 'phases': ['要判断增加的20是否由优惠券造成。', '补充：可在同一周随机选一半同类用户发券，另一半不发券，并预先设定指标。'], 'data': {'options': [{'A': '还可能有周末、广告等变化，前后对比不足以单独归因。', 'B': '销量增加20，所以优惠券因果效果就是20。', 'C': '有销售数据就不需要对照。'}, {'A': '只挑领券且购买的人，与所有未领券者比较。', 'B': '比较随机组的同口径平均结果，并检查分组与流失。', 'C': '尝试许多指标，只报告最好看的一个。'}], 'outcomes': [{'A': {'feedback': '区分相关变化与因果作用，没有超出证据。', 'supported_by_stated_criteria': True, 'checks': {}}, 'B': {'feedback': '时间变化与其他促销也可能影响销量。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '有数据不等于有可信的比较设计。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '按购买结果筛人会重新引入选择偏差。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '随机分组和预设口径有助于减少选择与报告偏差；仍需关注执行和外溢。', 'supported_by_stated_criteria': True, 'checks': {}}, 'C': {'feedback': '多试后只报最好值会夸大证据。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '先问没有发券时这些人可能会怎样。', 'reflection': '做决策时，你会怎样表达“暂时没有足够证据”？', 'knowledge_tags': ['因果识别', '基准率', '成本收益'], 'related_majors': ['数字经济', '统计学'], 'boundary': '不是投资建议、金融产品推荐或风控部署方案；只体验给定假设下的计算与证据判断。', 'source_concepts': ['因果识别', '基准率', '成本收益'], 'source_ids': ['LE-DIGITAL', 'STEM-S15'], 'display_permutation': [{'A': 'B', 'B': 'A', 'C': 'C'}, {'B': 'A', 'A': 'B', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'finance_fraud': {'case_id': 'finance_fraud', 'task_id': 'finance', 'variant_id': 'fraud', 'title': '99%准确为何没用', 'context': '合成1000笔交易里10笔异常、990笔正常；仅作基准率教学。', 'phases': ['系统把全部交易判为正常。', '新系统检出8笔异常，同时把20笔正常误报；误报代价1、漏报代价30。'], 'data': {'options': [{'A': '准确率99%，所以已抓住大部分异常。', 'B': '准确率只有1%。', 'C': '准确率990/1000=99%，但检出异常0/10；单看准确率不够。'}, {'A': '总代价20×1+2×30=80，比全判正常的300低；仍需讨论复核负担。', 'B': '检出8，所以不会造成任何误报负担。', 'C': '20+2=22，所以总代价必定22。'}], 'outcomes': [{'A': {'feedback': '99%来自多数正常交易，异常检出率其实为0。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '990个正常判对，准确率是99%而非1%。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '准确率与少数类检出是不同指标。', 'supported_by_stated_criteria': True, 'checks': {'accuracy': 0.99, 'recall': 0}}}, {'A': {'feedback': '漏报10-8=2；新损失80，原方案10×30=300；仅在给定假设下比较。', 'supported_by_stated_criteria': True, 'checks': {'loss': 80, 'baseline_loss': 300}}, 'B': {'feedback': '20笔误报需要复核，不能忽略。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '把次数相加遗漏不同错误的代价权重。', 'supported_by_stated_criteria': False, 'checks': {}}}], 'evidence': ['', '']}, 'hint': '先算漏报数量，再分别乘代价；高准确率可能只是多数类多。', 'reflection': '如果复核容量只有10笔，这个比较还缺什么约束？', 'knowledge_tags': ['因果识别', '基准率', '成本收益'], 'related_majors': ['金融科技', '统计学', '信息安全'], 'boundary': '不是投资建议、金融产品推荐或风控部署方案；只体验给定假设下的计算与证据判断。', 'source_concepts': ['因果识别', '基准率', '成本收益'], 'source_ids': ['LE-FIN-NK', 'LE-FIN-SZU', 'STEM-S15', 'STEM-S02'], 'display_permutation': [{'C': 'B', 'A': 'A', 'B': 'C'}, {'A': 'A', 'B': 'B', 'C': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'finance_publicdata': {'case_id': 'finance_publicdata', 'task_id': 'finance', 'variant_id': 'publicdata', 'title': '数据服务上线值不值', 'context': '合成校园数据查询服务只估算每学期时间：1000次查询，人工每次10分钟，自动后每次2分钟，维护2000分钟。', 'phases': ['以节省总工作时间为唯一教学目标。', '实际需求只有200次；单位时间与维护量不变。'], 'data': {'options': [{'A': '只算自动查询2000分钟，称之为净节省。', 'B': '净节省1000×(10-2)-2000=6000分钟。', 'C': '维护不是查询，因此不应计入总工作量。'}, {'A': '净节省仍为6000，不随需求变化。', 'B': '因为用了数字技术，一定更省时间。', 'C': '净节省200×8-2000=-400分钟；当前假设下未节时，还需评估其他价值。'}], 'outcomes': [{'A': {'feedback': '2000是自动查询工作量，不是扣除维护后的节省。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '人工10000；自动处理2000+维护2000=4000；净节省6000。', 'supported_by_stated_criteria': True, 'checks': {'net_minutes_saved': 6000}}, 'C': {'feedback': '维护消耗真实工作时间，应纳入当前口径。', 'supported_by_stated_criteria': False, 'checks': {}}}, {'A': {'feedback': '查询数量变化，收益也应重新计算。', 'supported_by_stated_criteria': False, 'checks': {}}, 'B': {'feedback': '工具名称不能替代成本收益核算。', 'supported_by_stated_criteria': False, 'checks': {}}, 'C': {'feedback': '原人工2000；新400+2000=2400；多花400分钟，尚未计质量与可及性。', 'supported_by_stated_criteria': True, 'checks': {'net_minutes_saved': -400}}}], 'evidence': ['', '']}, 'hint': '统一时间单位；把固定维护成本和按次成本分开。', 'reflection': '如果它让查询更公平、更及时，单一节时指标又可能漏掉什么？', 'knowledge_tags': ['因果识别', '基准率', '成本收益'], 'related_majors': ['数字经济', '软件工程'], 'boundary': '不是投资建议、金融产品推荐或风控部署方案；只体验给定假设下的计算与证据判断。', 'source_concepts': ['因果识别', '基准率', '成本收益'], 'source_ids': ['LE-DIGITAL', 'STEM-S04', 'STEM-S02'], 'display_permutation': [{'B': 'A', 'A': 'B', 'C': 'C'}, {'C': 'B', 'A': 'A', 'B': 'C'}], 'source_role': '学科背景与方法关联来源；所有题面数值、情境、选项及固定反馈为项目原创，不是来源学校真实作业或实测。'}, 'story_lab_deadline': {'case_id': 'story_lab_deadline', 'task_id': 'story', 'variant_id': 'lab_deadline', 'title': '赛前48小时', 'context': "机器人社团流传一句话：'没有一块主控板能活着见到比赛日。'今年轮到你们队应验了——{event}前 48 小时，主控板烧了，备用板调试至少还要一整夜。而你明天上午，是{course}期中考试。", 'phases': ["队长{actor}在群里@所有人：'今晚谁能留守？'你{course}还剩三章没看。你会怎么做？", "无论你怎么选，第二天到赛场后收到消息：赞助方临时要求当天上午加一场给中学生的公开演示，{actor}急性肠胃炎进了医院，队里只剩你能顶。你必须在'比赛成绩'和'公开演示'之间重新分配自己仅有的精力。你怎么定？"], 'hint': "这里没有正确答案——三个选项往年都有人真选过，后来都干得不错。选那个'换作是你，晚上睡得着'的。", 'reflection': "如果用一句话给今晚起个名字，你会叫它'____的一晚'？这个名字更像你讨厌的经历，还是有点像你佩服的某个人会经历的事？", 'knowledge_tags': ['团队协作', '压力决策', '竞赛文化', '责任边界'], 'related_majors': ['智能科学与技术（具身与行为智能特色班）', '自动化', '电子信息科学与技术'], 'boundary': '不评估领导能力与抗压能力；调试细节虚构，不构成硬件操作指导；人物与赛队均为合成。', 'surface_variants': [{'surface': {'actor': '陈屿', 'event': '机器人大赛', 'course': '高等数学'}}, {'surface': {'actor': '林一舟', 'event': '智能车竞赛', 'course': '大学物理'}}, {'surface': {'actor': '赵满', 'event': '无人机挑战赛', 'course': '英语四级'}}], 'data': {'evidence': ['', '演示观众约三十名中学生；赞助方明年的合作预算还没有定。'], 'options': [{'A': "群里回'我来'，今晚通宵调板子，{course}明天裸考。", 'B': "回'我明早6点到，今晚先把调试步骤写成清单发群里，谁留守照着做。'", 'C': '私聊{actor}说明考试冲突，建议从二队调人，自己负责赛后把全部调试记录整理成文档留给明年。'}, {'A': '比赛交别人，自己全程盯演示。', 'B': '比赛优先，演示压缩成15分钟快闪版。', 'C': '提议演示改放录像加远程连线医院里的{actor}，自己守比赛。'}], 'outcomes': [{'A': {'feedback': "你把自己的整块时间直接押进了团队的燃眉之急。{reason}这体现的是'扛事优先'：把团队的沉没成本当作自己的责任，宁可由自己吸收明天的考试状态。这种工作方式看重在场与担当，愿意用身体时间换团队的确定性。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'B': {'feedback': "你没有押上通宵，而是把个人经验转写成任何人都能接手的清单。{reason}这体现的是'系统优先'：不信任疲劳状态下的产出质量，用交接设计放大所有人的效率。这种工作方式看重可复制的流程，甚于个人英雄式的扑救。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'C': {'feedback': "你先诚实报出自己的约束，再把贡献挪到能兑现的时间点。{reason}这体现的是'边界优先'：清楚自己能承诺什么，用延期但可靠的交付替代当场透支。这种工作方式看重承诺的可兑现性，甚于当场的存在感。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}}, {'A': {'feedback': "你把精力从赛场挪到了演示台。{reason}这体现的是'长期关系优先'：成绩只此一次，口碑却可能明年还在，你选择为关系与声誉的复利放弃当场的名次。这种工作方式愿意让短期结果服务于长期资产。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'B': {'feedback': "你保住了比赛，把演示压成十五分钟快闪版。{reason}这体现的是'主目标优先'：队伍来这里首先是为了成绩，其余事情维持基本体面即可。这种工作方式用明确的排序抵御不断冒出来的新需求。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'C': {'feedback': "你设计了一个谁都不用硬扛的方案：录像加远程连线。{reason}这体现的是'结构优先'：遇到资源冲突先改结构，而不是改某个人的付出。这种工作方式相信多数两难可以被重新设计掉。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}}]}}, 'story_clinic_volunteer': {'case_id': 'story_clinic_volunteer', 'task_id': 'story', 'variant_id': 'clinic_volunteer', 'title': '社区科普翻车', 'context': "你们志愿队把{device}带进{community}做科普，宣传页上写着'脑机接口进社区'。演示刚开始十分钟，头环屏幕上的数据全成了乱码。七八位老人围上来，一位攥着体检报告问：'这仪器测得出我有没有病吗？'", 'phases': ['设备还在乱码，老人还在等回答，后面的居民还在陆续进活动室。你怎么办？', '活动结束了。复盘会上，指导老师问：要不要把这次翻车写进下一届志愿者的培训材料——写不写、写多少、怎么写？'], 'hint': '老人里有一位退休物理老师。想想你最不想让谁失望。', 'reflection': "你选的方案里，'被信任'和'不出错'谁排在前面？", 'knowledge_tags': ['科学沟通', '伦理', '公众信任'], 'related_majors': ['智能医学工程（脑机接口特色班）', '物联网工程', '电子信息科学与技术'], 'boundary': '不构成任何医疗建议；设备、社区与人物均为合成。', 'surface_variants': [{'surface': {'device': '专注度头环', 'community': '颐年社区'}}, {'surface': {'device': '脑电体验环', 'community': '海棠里社区'}}], 'data': {'evidence': ['', '带队老师补充：老人里有一位退休物理老师；社区主任说明年还想请你们来。'], 'options': [{'A': '坦白告诉老人：{device}测的是注意力状态，测不出病；然后改带大家做反应力小游戏，顺手把原理讲清楚。', 'B': "把乱码投屏放大，带老人一起'找茬'——识别仪器什么时候会出错，把这当成今天的第一课。", 'C': '宣布暂停演示，请搭档先带老人看展板，自己修设备，十五分钟后恢复正式演示。'}, {'A': '写，而且全写：设备怎么翻的、老人问了什么、我们怎么答的，一字不落放进培训材料。', 'B': "写，但只写结论：'设备可能现场故障，请准备备用方案'，不还原现场细节。", 'C': "不写进材料，改成培训时口头讲给下一届听，留经验不留'案底'。"}], 'outcomes': [{'A': {'feedback': "你先拆掉了老人对设备的错误期待，再用能做的事补上体验。{reason}这体现的是'诚实优先于形象'：宁可当场缩小自己的专业光环，也不让误解多站一分钟。这种工作方式把公众的准确理解放在展示的完整度前面。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'B': {'feedback': "你把事故直接变成了教材。{reason}这体现的是'把真实当教具'：相信受众有能力也有权利看到仪器不完美的那一面，而且'识别出错'本身就是科学素养。这种工作方式不害怕暴露过程。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'C': {'feedback': "你选择先恢复一个有秩序的正式演示。{reason}这体现的是'秩序优先'：混乱现场里先保住一次可预期、有质量的活动，再谈其他。这种工作方式在意受众带走的是一次完整、可靠的体验。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}}, {'A': {'feedback': "你把翻车全过程写进了培训材料。{reason}这体现的是'组织记忆优先'：后来的志愿者值得知道最真实的现场，哪怕记录里的自己并不好看。这种工作方式愿意为后来人少摔跤而留下自己的尴尬。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'B': {'feedback': "你只把教训提炼成一句可执行的备忘。{reason}这体现的是'摘要优先'：培训材料应该给原则，过多的现场细节反而会淹没重点。这种工作方式区分'经验'和'故事'，只传递前者。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'C': {'feedback': "你选择让经验口头相传。{reason}这体现的是'语境优先'：翻车这类事需要语气、表情和问答才讲得清，写下来容易被误读成事故通报或笑话。这种工作方式在意经验传递时的温度与完整语境。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}}]}}, 'story_model_ethic': {'case_id': 'story_model_ethic', 'task_id': 'story', 'variant_id': 'model_ethic', 'title': '路演前夜的假设', 'context': "{contest}路演前夜。组队时说好的'轮流建模'，执行成了你一次模型都没摸过——你只负责 PPT 和会议记录。核对数据时你发现：核心模型用了一个没人跟你提过的假设，评委面前一戳就破。", 'phases': ['现在离路演还有十个小时。你怎么办？', "路演拿了二等奖。评委果然问了那个假设，被队长含糊过去了。庆功宴上队长举杯说：'结果说明一切。'你怎么接？"], 'hint': '想想毕业后你还愿不愿意和这个人再组队。', 'reflection': '给这晚起个标题；它像不像你敬佩的某个人会做的事？', 'knowledge_tags': ['学术诚信', '团队政治', '风险沟通'], 'related_majors': ['金融科技', '数字经济', '数据科学'], 'boundary': '不构成竞赛或投资建议；企业、赛事与人物均为合成。', 'surface_variants': [{'surface': {'contest': '金融科技大赛', 'actor': '负责建模的阿哲'}}, {'surface': {'contest': '量化策略挑战赛', 'actor': '负责建模的晓雯'}}, {'surface': {'contest': '校园金融科技邀请赛', 'actor': '负责建模的老宋'}}], 'data': {'evidence': ['', '队长与{actor}是室友；明年你们还可能再组队。'], 'options': [{'A': '在群里直接指出这个假设的问题，附上你的验证过程，建议连夜改。', 'B': '先私聊{actor}核实——万一错的是你，全队要陪你白熬一夜。', 'C': "写成一页风险备忘录发给队长，注明'改不改你定，我留痕'。"}, {'A': "举杯，但补一句：'结果是好，下次那个假设我们还是有底气地回答比较好。'", 'B': '举杯，什么都不说——奖是真的，纠结那个假设已经没有意义。', 'C': '私下找队长说：奖我领得开心，但评委那个问题让我不舒服，下次赛前我要亲自过一遍模型假设。'}], 'outcomes': [{'A': {'feedback': "你把问题直接摆到全组台面上并附上了证据。{reason}这体现的是'对事优先'：问题属于全队，修正也需要全队时间，越早公开越少浪费。这种工作方式把信息透明看得比当面情面重。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'B': {'feedback': "你先私下核实再决定行动。{reason}这体现的是'验证优先'：在拉响全组警报之前，先确认自己不是那个错误来源。这种工作方式在意行动的成本，不愿用全队的通宵为自己的不确定买单。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'C': {'feedback': "你用书面留痕的方式把决定权交给了队长。{reason}这体现的是'程序优先'：把风险写清楚、把决策留在该做决定的人手里，自己尽到告知义务。这种工作方式重视职责边界与可追溯。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}}, {'A': {'feedback': "你在庆功的场合仍把那个洞点了出来。{reason}这体现的是'问题不过夜'：庆祝归庆祝，没解决的技术风险不会因为拿了奖就消失。这种工作方式难以接受'结果好等于过程对'。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'B': {'feedback': "你选择让这一刻只属于庆祝。{reason}这体现的是'场合意识优先'：庆功宴的功能是凝聚团队，技术复盘有它自己的时间和场合。这种工作方式区分场合的功能，不愿让扫兴稀释团队应得的快乐。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}, 'C': {'feedback': "你把不舒服换成了一条具体的下次约定。{reason}这体现的是'机制优先'：不纠结这次谁含糊了过去，而是改分工规则，让自己下次握有核查的位置。这种工作方式把情绪兑换成制度改进。这是一种倾向线索，不是能力判断，也不是专业匹配结论。"}}]}}, 'values_research_day': {'case_id': 'values_research_day', 'task_id': 'values', 'variant_id': 'research_day', 'title': '教授的走廊', 'context': "一位做了三十年科研的教授被学生问'您这行到底图什么'，他想了很久：'我说不清。但我能告诉你哪几天我下班是哼着歌的。'下面这几张卡片，都来自他'哼着歌的日子'。", 'phases': ["把这些卡片从'最不能少'排到'最无所谓'。直接说出你的顺序就好，也可以说说为什么。", "教授追加了一个条件：'假如你入行的头五年，排在最后两名的东西你都拿不到。排序变不变？'请重新排一次，说说变了哪里、为什么。"], 'hint': "别按'哪个听起来高尚'排，按'哪个被拿走你会真难受'排。", 'reflection': "看你排第一的那张——它更接近'这件事本身让我爽'，还是'它能带我去想去的地方'？", 'knowledge_tags': ['科研动机', '价值澄清', '内在动机'], 'related_majors': ['物理学', '化学', '数学与应用数学'], 'boundary': '不评估价值观优劣；教授为合成人物。', 'surface_variants': [{'surface': {}, 'item_ids': ['card_epiphany', 'card_artifact', 'card_credit', 'card_people', 'card_impact', 'card_freedom']}, {'surface': {}, 'item_ids': ['card_epiphany', 'card_artifact', 'card_people', 'card_impact', 'card_stable', 'card_fame']}, {'surface': {}, 'item_ids': ['card_epiphany', 'card_credit', 'card_people', 'card_freedom', 'card_stable', 'card_fame']}], 'data': {'items': [{'id': 'card_epiphany', 'text': '「搞懂」的快感：卡住三周的推导，洗澡时突然通了'}, {'id': 'card_artifact', 'text': '能跑的东西：代码或装置真的动起来的那一刻'}, {'id': 'card_credit', 'text': '署名：论文或专利上有你的名字'}, {'id': 'card_people', 'text': '同路人：和一群比你强的人天天混在一起'}, {'id': 'card_impact', 'text': '帮到具体的人：你做的事改变了某个陌生人的生活'}, {'id': 'card_freedom', 'text': '节奏自由：几点起床、在哪干活，自己说了算'}, {'id': 'card_stable', 'text': '稳定感：下个月、明年这个时候，大概都知道自己在哪'}, {'id': 'card_fame', 'text': '被同行认可：开会时有人引用你的工作'}]}}, 'values_offer_letter': {'case_id': 'values_offer_letter', 'task_id': 'values', 'variant_id': 'offer_letter', 'title': '辅导员的统计表', 'context': "辅导员的电脑里有一份匿名统计表：上一届学长姐'大一填的意向'和'最终落点'的重合率不到一半。他说：'不是被现实打败，是很多人毕业时才第一次认真想这个问题。'", 'phases': ["下面是那份统计表附带的一叠卡片，每张写着一种'毕业去向里可以看重的东西'。从'对我最重要'排到'最无所谓'，直接说顺序，也可以说为什么。", '家里突然经济紧张：头三年你每月需要往家寄一笔钱。条件变了，请重新排一次，说说哪里动了、为什么。'], 'hint': "第一次排的是'想要'，第二次排的是'代价'，两次的差距本身就是答案。", 'reflection': '两次排序里唯一没动的那张卡，是你的底线还是你的奢侈品？', 'knowledge_tags': ['职业价值', '代价', '代际责任'], 'related_majors': ['数学与应用数学', '统计学', '金融科技'], 'boundary': '不做职业规划建议；统计数据与情境均为合成。', 'surface_variants': [{'surface': {}, 'item_ids': ['card_stable', 'card_growth', 'card_interest', 'card_family', 'card_income', 'card_title']}, {'surface': {}, 'item_ids': ['card_stable', 'card_growth', 'card_interest', 'card_social', 'card_income', 'card_city']}, {'surface': {}, 'item_ids': ['card_interest', 'card_family', 'card_social', 'card_income', 'card_city', 'card_title']}], 'data': {'items': [{'id': 'card_stable', 'text': '稳定：编制或大平台，明年今天你在哪，大概猜得到'}, {'id': 'card_growth', 'text': '成长陡坡：高波动高上限，三年可能顶别人八年'}, {'id': 'card_interest', 'text': '兴趣对口：每天干的具体事情，自己不烦'}, {'id': 'card_family', 'text': '离家近：周末能回家吃饭，爸妈有事一小时内到'}, {'id': 'card_social', 'text': '社会价值：做的事被陌生人真切需要'}, {'id': 'card_income', 'text': '收入：明码标价，不丢人'}, {'id': 'card_city', 'text': '城市与圈子：在哪座城、和什么人混在一起'}, {'id': 'card_title', 'text': '专业名号：说出去好听，亲戚问起不虚'}]}}, 'values_team_role': {'case_id': 'values_team_role', 'task_id': 'values', 'variant_id': 'team_role', 'title': '不许碰的那件事', 'context': "软件工程课第一节，老师说：'大作业自由组队。提醒一句——每年挂掉的不是最弱的队，是四个人都想当架构师的队。'", 'phases': ["下面是你在一个团队项目里'最忍不住要管'的几件事。从'最忍不住'排到'随它去'，说说你的顺序。", '老师追加规定：你排第一的那件事，这学期由别人全权负责，你不许碰、不许问、不许查。请把剩下的重新排一次，并说说你打算怎么活。'], 'hint': "'忍不住要管'和'擅长管'是两回事，按前者排。", 'reflection': "排第一的卡被没收后，你的难受更多是'失控'还是'失聪'（看不见信息）？", 'knowledge_tags': ['协作角色', '控制感', '团队分工'], 'related_majors': ['软件工程', '计算机科学与技术', '信息安全'], 'boundary': '不评估领导力或性格类型；课程情境为合成。', 'surface_variants': [{'surface': {}, 'item_ids': ['card_deadline', 'card_quality', 'card_people', 'card_direction', 'card_present', 'card_docs']}, {'surface': {}, 'item_ids': ['card_deadline', 'card_quality', 'card_direction', 'card_present', 'card_tech', 'card_test']}, {'surface': {}, 'item_ids': ['card_deadline', 'card_people', 'card_direction', 'card_docs', 'card_tech', 'card_test']}], 'data': {'items': [{'id': 'card_deadline', 'text': '进度与期限：谁这周该交什么，交没交'}, {'id': 'card_quality', 'text': '代码质量：命名、结构、注释——烂代码看了手痒'}, {'id': 'card_people', 'text': '人的状态：谁最近不对劲，谁需要被拉一把'}, {'id': 'card_direction', 'text': '方向决策：做哪个功能、砍掉哪个需求'}, {'id': 'card_present', 'text': '对外展示：答辩、演示、站在台上的那个人是谁'}, {'id': 'card_docs', 'text': '文档与交接：说明文档不写清楚，这项目等于没做'}, {'id': 'card_tech', 'text': '技术选型：用什么框架、什么库，为什么'}, {'id': 'card_test', 'text': '测试与上线：什么时候算做完，谁守最后一道关'}]}}, 'hearing_gpu_quota': {'case_id': 'hearing_gpu_quota', 'task_id': 'hearing', 'variant_id': 'gpu_quota', 'title': '一千卡时怎么分', 'context': '学院新到一台 GPU 服务器，消息发出那天，三个社团的群同时炸了。教务处把分配方案交给学生委员会——你是委员之一。全学期共 {budget0} 卡时，五个申请方，怎么分都有人骂。', 'phases': ['把 {budget0} 卡时分给下面五个申请方。以 {step} 卡时为最小单位，可以给 0，单项最多 {cap}，总和必须正好 {budget0}。说出每项给多少，再说说你的理由。', '方案提交后，竞赛队教练找你：国赛提前，两周内拿不到 400 卡时就真的弃赛。只能改已提交的方案，你怎么调？总和仍是 {budget1}。说说新的分配和理由。'], 'hint': '没有方案能让五个群都不骂你。想清楚你打算让谁骂，以及拿什么回应。', 'reflection': "你分得最多的那一项，保护的是'最多人的基本盘'、'最强者的天花板'，还是'后来者的机会'？", 'knowledge_tags': ['资源分配', '利益相关者', '公平与效率'], 'related_majors': ['计算机科学与技术', '智能科学与技术', '数据科学'], 'boundary': "数字为虚构教学量；不评价任何真实院系政策；'弃赛威胁'为合成冲突。", 'surface_variants': [{'surface': {'budget0': '1000', 'budget1': '1000', 'step': '50', 'cap': '500'}}, {'surface': {'budget0': '800', 'budget1': '800', 'step': '50', 'cap': '500'}, 'data_overrides': {'budget': [800, 800]}}], 'data': {'items': [{'id': 'item_course', 'text': '全院《机器学习》课程实验：200 人选修，每人至少跑通一次大作业'}, {'id': 'item_competition', 'text': "校竞赛队：下月打国赛，放话'不给够就弃赛'"}, {'id': 'item_research', 'text': '教师科研训练：带 12 名本科生，成果署名归学生'}, {'id': 'item_personal', 'text': '个人自由申请池：先到先得——上学期池子被 3 个人用掉八成'}, {'id': 'item_reserve', 'text': '应急预留：谁都不给，留着救火（选它也是立场）'}], 'budget': [1000, 1000], 'unit': '卡时', 'min_step': 50, 'max_per_item': 500}}, 'hearing_fund_review': {'case_id': 'hearing_fund_review', 'task_id': 'hearing', 'variant_id': 'fund_review', 'title': '创新基金评审席', 'context': "学院创新基金流传一个数字：通过率约三分之一——'但被毙的项目里，每年都有一两个后来发了论文。'你是学生评审席的一员，手握 {budget0} 千元，五个申请项目，怎么分都有人不服。", 'phases': ['把 {budget0} 千元分给下面五个项目。以 {step} 千元为最小单位，可以给 0，单项最多 {cap}，总和必须正好 {budget0}。说出每项给多少，再说说理由。', "公示后，有团队在年级群质疑你'偏袒小项目'，说明会上你要公开回应。请重新确认或调整你的分配（总和仍为 {budget1} 千元），并写出你公开说明的第一段话。"], 'hint': '你的上限规则会先于金额暴露你的立场。', 'reflection': "你更愿意为'做成过的证据'付钱，还是为'没人试过的可能'付钱？", 'knowledge_tags': ['同行评审', '证据与风险', '公共说明'], 'related_majors': ['材料化学（新材料特色班）', '新能源科学与工程（数智能源特色班）', '应用化学', '生物技术（生物智造特色班）'], 'boundary': '项目全为合成，不构成科研或投资价值评价；不评价任何真实院系政策。', 'surface_variants': [{'surface': {'budget0': '100', 'budget1': '100', 'step': '5', 'cap': '50'}}, {'surface': {'budget0': '90', 'budget1': '90', 'step': '5', 'cap': '50'}, 'data_overrides': {'budget': [90, 90]}}], 'data': {'items': [{'id': 'item_catalyst', 'text': '电解水催化剂：导师方向热门，但去年同组项目烂尾'}, {'id': 'item_straw', 'text': '可降解吸管材料：本科生主导，已完成小试，要钱最少'}, {'id': 'item_protein', 'text': 'AI 辅助蛋白质筛选：想法性感，团队零生物背景'}, {'id': 'item_battery', 'text': '锂电热失控预警：企业合作，但成果归企业'}, {'id': 'item_scivideo', 'text': '科普视频项目：不硬核，播放量实打实'}], 'budget': [100, 100], 'unit': '千元', 'min_step': 5, 'max_per_item': 50}}, 'hearing_club_budget': {'case_id': 'hearing_club_budget', 'task_id': 'hearing', 'variant_id': 'club_budget', 'title': '换届的U盘', 'context': "{club}换届，老社长交给你一个 U 盘和一句话：'账上 {budget0} 千元。去年招新来了 {fresh} 人，现在活跃的还有 {active} 个——钱怎么花，你看着办。'", 'phases': ['把 {budget0} 千元分给下面六个事项。以 {step} 千元为最小单位，可以给 0，总和必须正好 {budget0}。说出每项给多少，再说说理由。', '学期中学校通知：社团经费统一核减，你的总额从 {budget0} 变成 {budget1} 千元。已定的计划砍哪块、怎么调？重新分配（总和必须正好 {budget1}），说说你砍的顺序。'], 'hint': '从招新到活跃之间那段落差里发生了什么，比总额怎么分更重要。', 'reflection': '你砍预算的顺序，和你砍自己周末时间的顺序，像不像？', 'knowledge_tags': ['组织运营', '留存', '取舍'], 'related_majors': ['自动化', '物联网工程', '电子信息科学与技术'], 'boundary': '金额为虚构；不评价真实社团管理；人物为合成。', 'surface_variants': [{'surface': {'club': '电子设计社', 'budget0': '20', 'budget1': '14', 'step': '1', 'fresh': '180', 'active': '19'}}, {'surface': {'club': '航模队', 'budget0': '20', 'budget1': '14', 'step': '1', 'fresh': '165', 'active': '17'}}, {'surface': {'club': 'ACM分部', 'budget0': '20', 'budget1': '14', 'step': '1', 'fresh': '198', 'active': '21'}}], 'data': {'items': [{'id': 'item_recruit', 'text': '招新与体验日：让下一批新生能摸到真东西'}, {'id': 'item_compete', 'text': '比赛报名与差旅：报名费和去外地的车票'}, {'id': 'item_training', 'text': '培训与教材：让零基础的新人第三周就能做出第一个作品'}, {'id': 'item_equipment', 'text': '设备与耗材：探头总在丢，焊台该换了'}, {'id': 'item_bonding', 'text': '团建与老社员维系：留下的活跃成员凭什么再留一年'}, {'id': 'item_reserve', 'text': '留存应急金：谁都不给，留着救火'}], 'budget': [20, 14], 'unit': '千元', 'min_step': 1, 'max_per_item': None}}, 'daylife_cell_lab': {'case_id': 'daylife_cell_lab', 'task_id': 'daylife', 'variant_id': 'cell_lab', 'title': '学姐的周日', 'context': "生物实验室学姐的手机屏保是她的细胞——荧光显微镜下像一片星空。她说这张图值她两个月的周日。'别误会，不是感动，'她笑，'是两个月里我只做出了这一张能看的。'", 'phases': ['学姐给你看了她上周日的真实时间账单。现在轮到你：如果这是你的周日，32 个半小时你怎么分？项目就在下面，每项可以是 0。说出每项给多少（单位：半小时），再说说为什么这么分。', "导师通知下月课题汇报你上。学姐提醒：'汇报前的周日长什么样，决定你汇报时是什么状态。'同样 32 个半小时重分一次——哪些必须保住，哪些可以砍？"], 'hint': "别抄学姐的账单。先圈出你'骗不了自己'必须花的时间，再分剩下的。", 'reflection': "对比两次分配，被你保住不动的那几小时，装的是你真正在意的东西。它像你想过的生活，还是只像'应该过'的生活？", 'knowledge_tags': ['科研日常', '湿实验真实感', '时间质地'], 'related_majors': ['生物科学', '生物技术（生物智造特色班）', '应用化学'], 'boundary': '实验操作仅为时长描述，不构成任何实验指导；人物为合成。', 'surface_variants': [{'surface': {}}, {'surface': {}, 'data_overrides': {'items': [{'id': 'imaging', 'text': '共聚焦拍图：等一个视野，像等一锅汤'}, {'id': 'washing', 'text': '灭菌与配液：不性感，但吃掉了真正的下午'}, {'id': 'papers', 'text': '看文献'}, {'id': 'discussion', 'text': '组会与搭档讨论'}, {'id': 'commute', 'text': '吃饭通勤'}, {'id': 'gym', 'text': '操场夜跑'}, {'id': 'idle', 'text': '追剧刷手机'}]}}, {'surface': {}, 'data_overrides': {'items': [{'id': 'imaging', 'text': '显微成像与拍图：等一个视野，像等一锅汤'}, {'id': 'washing', 'text': '洗瓶子、配试剂：是的，真的要这么久'}, {'id': 'papers', 'text': '看文献'}, {'id': 'discussion', 'text': '组会与搭档讨论'}, {'id': 'commute', 'text': '吃饭与校车通勤'}, {'id': 'gym', 'text': '羽毛球局'}, {'id': 'idle', 'text': '拼乐高发呆'}]}}], 'data': {'items': [{'id': 'imaging', 'text': '显微成像与拍图：等一个视野，像等一锅汤'}, {'id': 'washing', 'text': '洗瓶子、配试剂：是的，真的要这么久'}, {'id': 'papers', 'text': '看文献'}, {'id': 'discussion', 'text': '组会与搭档讨论'}, {'id': 'commute', 'text': '吃饭通勤'}, {'id': 'gym', 'text': '运动'}, {'id': 'idle', 'text': '发呆刷手机'}], 'budget': [32, 32], 'unit': '半小时', 'min_step': 1, 'max_per_item': None}}, 'daylife_quant': {'case_id': 'daylife_quant', 'task_id': 'daylife', 'variant_id': 'quant', 'title': '实习生的电影', 'context': "金融科技实习宣讲会上，HR 放出'团队平均年龄 26 岁'，台下哇声一片。散场你拦住刚下班的实习生{intern}，对方说了句 PPT 上没有的：'我上一次完整看完一部电影，是上个月。'", 'phases': ['如果这是你的实习日，32 个半小时你怎么分？项目就在下面，每项可以是 0。说出每项给多少（单位：半小时），再说说为什么这么分。', "实习第三周，带教说：'你这样下去三个月会烧完。'让你重排这一天，但工作类项目（盯盘、写策略、读研报、开会）合计不许砍。同样 32 个半小时，重分一次——说说你砍了什么、保住了什么。"], 'hint': '烧完你的通常不是时长，是某一项的密度。', 'reflection': "你把'学新东西'排在工作内还是工作外？这个位置比时长更说明问题。", 'knowledge_tags': ['实习真实感', '可持续节奏', '职业倦怠'], 'related_majors': ['金融科技', '数字经济', '信息与计算科学'], 'boundary': '不构成实习与职业建议；机构与人物均为合成。', 'surface_variants': [{'surface': {'intern': '小周'}}, {'surface': {'intern': '林汐'}, 'item_ids': ['work_market', 'work_code', 'work_meeting', 'work_learn', 'life_gym', 'life_friends', 'life_idle']}, {'surface': {'intern': '大熊'}, 'item_ids': ['work_market', 'work_code', 'work_report', 'work_learn', 'life_gym', 'life_friends', 'life_idle']}], 'data': {'items': [{'id': 'work_market', 'text': '盯盘与数据清洗：脏数据比盘面更耗人'}, {'id': 'work_code', 'text': '写策略代码：回测又崩在过拟合上'}, {'id': 'work_report', 'text': '读研报：三份券商报告结论互相打架'}, {'id': 'work_meeting', 'text': '开会对齐：晨会、周会、临时拉通'}, {'id': 'work_learn', 'text': '学新东西：没人教，只能自己啃的新工具'}, {'id': 'life_gym', 'text': '健身'}, {'id': 'life_friends', 'text': '朋友与娱乐：包括那部没看完的电影'}, {'id': 'life_idle', 'text': '发呆：什么都不干的半小时'}], 'budget': [32, 32], 'unit': '半小时', 'min_step': 1, 'max_per_item': None}}, 'daylife_chip': {'case_id': 'daylife_chip', 'task_id': 'daylife', 'variant_id': 'chip', 'title': '咖啡机是主力设备', 'context': "微电子校友分享会，学长{senior}第一句话：'我上班四年，最先进的设备不是光刻机，是我的咖啡机——流片等结果那几周，除了喝咖啡你什么也加速不了。'", 'phases': ['如果这是你的一个工作日，32 个半小时你怎么分？项目就在下面，每项可以是 0。说出每项给多少（单位：半小时），再说说为什么这么分。', "流片失败，下一轮排期紧张。重排这一天：哪些'慢功夫'你反而要加时间？同样 32 个半小时，重分一次，说说理由。"], 'hint': '等结果的 4 个小时你怎么填，决定了你是哪种工程师。', 'reflection': "你的分配里，'能加速的'和'只能等的'，哪个拿到的质量时间更多？", 'knowledge_tags': ['芯片行业日常', '等待与并行', '工程节奏'], 'related_majors': ['微电子科学与工程', '电子科学与技术', '光电信息科学与工程'], 'boundary': '工艺细节虚构，不构成工程指导；人物为合成。', 'surface_variants': [{'surface': {'senior': '老宋'}}, {'surface': {'senior': '阿沁'}, 'item_ids': ['sim', 'waiting', 'debug', 'docs', 'meeting', 'life_meal', 'coffee']}, {'surface': {'senior': '程姐'}, 'item_ids': ['sim', 'waiting', 'debug', 'docs', 'meeting', 'learn', 'life_meal']}], 'data': {'items': [{'id': 'sim', 'text': '写代码跑仿真：脚本永远差最后一个角落'}, {'id': 'waiting', 'text': '等结果：合法的空白——摸鱼还是并行干活，你说了算'}, {'id': 'debug', 'text': '看波形调 bug：一个毛刺能吃掉一下午'}, {'id': 'docs', 'text': '写文档：设计文档和评审记录'}, {'id': 'meeting', 'text': '跨部门会：和工艺、封装、测试互相翻译'}, {'id': 'learn', 'text': '学习新工具：新版本软件又改了界面'}, {'id': 'life_meal', 'text': '生活项：吃饭、通勤、喘口气'}, {'id': 'coffee', 'text': '咖啡与闲聊：听来的八卦比文档更快暴露风险'}], 'budget': [32, 32], 'unit': '半小时', 'min_step': 1, 'max_per_item': None}}, 'failure_modeling': {'case_id': 'failure_modeling', 'task_id': 'failure', 'variant_id': 'modeling', 'title': '查成绩那晚', 'context': "数学建模国赛出成绩那晚，你们队三个人在群里一句话没说。三天三夜，成功参与奖。队长发了张{photo}的照片，又秒撤回。两周后社团招新，新生问你：'{address}，打建模比赛是什么体验？'", 'phases': ['社团招新现场：给新生写一段不许说谎的回复。', '队长私聊之后：把那段话改写成给局内人的回复。'], 'hint': "如果卡住了，就从'第三天夜里我……'开头试试。", 'reflection': '重读两个版本：哪一段写得更快？快的那段里藏着你已经消化掉的东西；卡住的那段，可能还没过去。', 'knowledge_tags': ['挫折叙事', '复盘', '竞赛文化'], 'related_majors': ['数学与应用数学', '统计学', '数据科学'], 'boundary': '不评判写作水平；文本不用于任何能力推断；人物与赛队均为合成。', 'surface_variants': [{'surface': {'photo': '凌晨四点教学楼空走廊', 'address': '姐'}}, {'surface': {'photo': '凌晨四点手机屏幕上的七个未接来电', 'address': '哥'}}, {'surface': {'photo': '一张写满叉的草稿纸', 'address': '学姐'}}], 'data': {'writing': ['用一段话回复这位新生（200字以内）。要求只有一条：不许说谎——既不能装没事，也不能把人说跑。', "刚发出去，队长私聊你：'我一直在想要不要再来一年，但我怕又白干。你咋想？'把刚才那段话改写成给队长的回复（200字以内）——同样不许说谎，但这次你们俩都在局里。"], 'max_chars': 800, 'title_prompt': '再给这段话起一个15字以内的标题（标题不计入字数）。'}}, 'failure_cells': {'case_id': 'failure_cells', 'task_id': 'failure', 'variant_id': 'cells', 'title': '扔了吧', 'context': "科研训练第四周，你养了两周的细胞集体污染。{senior}看了一眼说：'扔了吧。'语气平淡得像在说外卖到了。后来{senior}告诉你，博一那年扔掉的{vessel}能铺满一张实验台。", 'phases': ["给两周前'一切尽在掌握'的自己写一段话。", '把那段话改写成公众号可发表的版本，并注明你不发表的部分。'], 'hint': "'扔了吧'三个字里其实有安慰，你听得出来吗？", 'reflection': '你不愿发表的那部分，恰恰是这次体验最想帮你留住的东西。', 'knowledge_tags': ['失败常态化', '科研叙事', '发表与真实'], 'related_majors': ['生物科学', '化学', '材料化学（新材料特色班）'], 'boundary': '不涉及实验操作细节；人物与情境均为合成。', 'surface_variants': [{'surface': {'senior': '师兄', 'vessel': '培养皿'}}, {'surface': {'senior': '师姐', 'vessel': '摇瓶'}}], 'data': {'writing': ['给两周前的自己写一段话（300字以内）——那时的你刚接种完这批细胞，正觉得一切尽在掌握。', "学院公众号约稿'科研训练心得'，编辑暗示想要'励志一点'。把那段话改写成可发表的版本（300字以内），并在末尾注明：哪些内容你决定不发表，为什么。"], 'max_chars': 800, 'title_prompt': '再给这段话起一个15字以内的标题（标题不计入字数）。'}}, 'failure_defense': {'case_id': 'failure_defense', 'task_id': 'failure', 'variant_id': 'defense', 'title': '十秒钟', 'context': "大创中期答辩，你准备了二十页 PPT，评委{question_num}就把你问住了——那个问题恰好是你 PPT 里加粗标出的'{innovation}'。全场安静的那十秒，你后来记得比整个学期都清楚。", 'phases': ["以'十秒钟之后'为题，写下从那十秒到现在你愿意承认的部分。", '从上一段文字里挑出你会讲给新生的部分，并说明挑它的理由。'], 'hint': "'愿意承认'不等于'全部坦白'，边界由你定。", 'reflection': '你挑给新生看的那部分，是为了帮他们，还是为了重新安置那个十秒钟里的自己？', 'knowledge_tags': ['公开受挫', '表达边界', '经验传承'], 'related_majors': ['软件工程', '信息安全', '智能科学与技术'], 'boundary': '不评价答辩表现；情境为合成。', 'surface_variants': [{'surface': {'question_num': '第三个问题', 'innovation': '创新点'}}, {'surface': {'question_num': '第二个问题', 'innovation': '核心创新'}}], 'data': {'writing': ["以'十秒钟之后'为题（可以改题），写下从那十秒到现在你愿意承认的部分（400字以内）。", "下周组会轮到你给新生讲三分钟'我踩过的坑'。从上一段文字里挑出你会讲给新生的部分，并说明挑它的理由（300字以内）。"], 'max_chars': 800, 'title_prompt': '再给这段话起一个15字以内的标题（标题不计入字数）。'}}}, 'source_mapping_version': '2026-10-17-v2'}
CATALOG = {'version': 'user-list-2026-10-17', 'source_id': 'U-GROUPS-20261017', 'source': '用户于2026-10-17在本次对话提供的8组大类清单', 'verification': 'user_provided_not_officially_verified', 'applicable_cohort': '未提供，不推定为2026级', 'rule': '本专业大类内专业任选；仅按用户提供文本记录，不推导跨大类资格', 'groups': {'future': {'name': '未来产业精英', 'display_name': '未来产业精英', 'majors': ['智能科学与技术（具身与行为智能特色班）', '智能医学工程（脑机接口特色班）', '新能源科学与工程（数智能源特色班）', '材料化学（新材料特色班）', '生物技术（生物智造特色班）']}, 'information': {'name': '信息科学与技术', 'display_name': '信息科学与技术', 'majors': ['计算机科学与技术', '物联网工程', '信息安全', '自动化', '智能科学与技术', '软件工程']}, 'physics_opto': {'name': '物理与光电信息技术工程', 'display_name': '物理与光电信息技术工程', 'majors': ['物理学', '应用物理学', '光电信息科学与工程', '电子信息科学与技术', '微电子科学与工程', '电子科学与技术', '通信工程']}, 'matter': {'name': '物质科学', 'display_name': '物质科学', 'majors': ['化学', '应用化学', '生物科学', '材料物理', '材料化学']}, 'digital_finance': {'name': '数智经济金融', 'display_name': '数智经济金融', 'majors': ['数字经济', '金融科技']}, 'boqin_info': {'name': '卓越拔尖计划伯芩班', 'display_name': '卓越拔尖计划伯芩班（信息方向，用于界面区分）', 'majors': ['计算机科学与技术', '智能科学与技术', '光电信息科学与工程']}, 'math_data': {'name': '数学与大数据', 'display_name': '数学与大数据', 'majors': ['数学与应用数学', '信息与计算科学', '统计学', '数据科学']}, 'boqin_science': {'name': '卓越拔尖计划伯芩班', 'display_name': '卓越拔尖计划伯芩班（理科方向，用于界面区分）', 'majors': ['物理学', '量子信息科学', '化学', '生物科学']}}, 'package_version': '2.0.0', 'naming_notes': ['官方2026报道使用伯苓；用户最初清单使用伯芩。两组成员分别保留，不把单独班名映射为确定组。', '官方报道可以提供专业与特色方向背景，不能无声改写用户的组内专业集合或个人资格。']}
CASE_VERSION = '2026-10-17.v4.0'
FAMILY_NAMES = {'route': '网络与路径', 'sensor': '阈值与误判', 'control': '反馈与动态', 'experiment': '实验对照', 'evidence': '数据与证据', 'resource': '资源与权衡', 'debug': '排错与系统', 'materials': '材料与性能', 'finance': '经济与决策', 'story': '叙事两难', 'values': '价值排序', 'hearing': '优先级听证', 'daylife': '一天拼图', 'failure': '失败复盘'}
ALIASES = {"senor": "sensor"}
DEFAULTS = {"route":"route_campus", "sensor":"sensor_luggage", "control":"control_cart"}
# Per-group activity menus. Only families listed here appear as buttons for a
# confirmed group; a student can still reach any family by explicitly naming it.
GROUP_FAMILIES = {
    "future":["experiment","materials","resource","sensor","control","story","hearing","daylife","failure"],
    "information":["debug","route","sensor","control","evidence","story","values","hearing","failure"],
    "physics_opto":["materials","sensor","control","debug","evidence","story","values","hearing","daylife"],
    "matter":["experiment","materials","evidence","resource","values","hearing","daylife","failure"],
    "digital_finance":["finance","resource","evidence","story","values","daylife","failure"],
    "boqin_info":["route","debug","sensor","materials","values","hearing","daylife"],
    "math_data":["evidence","resource","route","finance","story","values","hearing","daylife","failure"],
    "boqin_science":["experiment","evidence","materials","values","daylife","failure"],
}
DEFAULT_MENU_FAMILIES = ["story","values","hearing","daylife","failure","evidence","resource","experiment"]
STOP_WORDS = {"结束", "退出", "结束体验", "不做了", "停止体验"}
HINT_WORDS = {"提示", "给我提示", "求助", "不会", "不知道", "不确定"}
CONFIRM_WORDS = {"确认", "确认试算", "确认方案", "按此试算", "确认计算", "保持方案"}
GATE_CANCEL_WORDS = {"先不生成", "再想想", "继续", "先不要", "先不结束", "再看看", "取消", "先不了", "继续体验"}
NEW_MODES = ("rank", "allocation", "compose")


def markdown_text(value):
    """Display untrusted prose literally. Exact raw text stays in state/events."""
    value = html.escape(str(value), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~\-])", r"\\\1", value)


def quoted(value):
    return "\n".join("> " + markdown_text(line) if line else ">" for line in str(value).split("\n"))


def looks_like_question(text):
    return bool(re.search(r"(?:怎么|如何|能否|可不可以|会不会|有没有|什么时候|什么是|为什么|哪|吗|么)", text))


def wants_finish(raw):
    """Conservative explicit intent detector; do not act on reported/negative speech."""
    text = raw.strip().rstrip("。！？!? ")
    # Students may quote UI instructions or negate a past wish; these are not commands.
    if not text or re.search(r"[“”\"‘’]|(?:并不|不是|不要|不想|不用|无需|不需要|还不|先不|暂不|不能|别|不)(?:[^，,。；;]{0,5})(?:结束|退出|停止|报告)|(?:如果|假如|要是|比如|示例|有人说|你说的|上次|之前|刚才|结束后)", text):
        # '不想继续' is itself an explicit stop request, not a negated stop.
        if not re.fullmatch(r"(?:我)?(?:不想|不打算|不愿意)再?继续(?:做|体验|答题|回答)?了?(?:[，,；;\s]*(?:请)?(?:帮我|给我|为我)?(?:生成|整理|出|拿到|看看|提供)?(?:一下)?(?:本次|当前|一份|已有)?(?:的)?(?:报告|记录))?[吧了]?", text):
            return False
    if text in STOP_WORDS or text in {"生成报告", "给我报告", "给我一份报告", "我要报告", "先看报告", "查看报告", "拿报告", "直接拿报告", "直接拿到报告", "结束并给我报告", "结束并生成报告", "结束并查看报告", "查看已有记录", "先到这里", "先到这吧", "到这里吧", "不继续了", "不想继续了", "生成记录", "直接生成记录", "整理记录", "给我记录", "我要记录", "查看记录"}:
        return True
    if looks_like_question(text):
        return False
    if re.search(r"(?:不想|不打算|不愿意)再?继续|(?:想|要|打算|决定|希望)(?:先|现在|直接)?(?:结束|退出|停止)(?:本次|这次|这个)?(?:体验|活动|练习|答题)?|(?:^|[，,；;\s])(?:我)?(?:现在|先|就|请)?(?:结束|退出|停止)(?:本次|这次|这个)?(?:体验|活动|练习|答题)?(?:[，,；;\s]|$|并|吧|了)|(?:直接|现在|就|先|请|帮我).{0,6}(?:拿到|拿|给我|生成|看|出)(?:本次|当前|已有|一份|的)*(?:报告|记录)", text):
        return True
    return False


def stage_guide(state):
    evaluated = sum(e.get("kind") == "evaluated" for e in state.get("events", []))
    if state.get("status") in ("stopped", "completed"):
        return "*本次体验已结束。下面保留你实际做过的内容；需要时可以再开始一次。*"
    if state.get("report_gate"):
        return "**现在：确认是否整理记录**\n\n*整理前你可以自愿留下一句这次的想法；不想留可以直接生成。还没做的部分不会补写。*"
    if state.get("status") == "awaiting_record_confirmation":
        label = "核对记录"
    elif state.get("status") == "evaluated":
        label = "看看结果，再决定下一步"
    elif state.get("status") == "awaiting_confirmation":
        label = "核对你刚才的方案"
    else:
        label = "先试一个方案" if state.get("phase", 0) == 0 else "条件变了，再试一次"
    return "**现在：%s**\n\n*一轮体验会试一个方案，再看看条件变化后会怎样，最后由你决定是否整理一份探索记录。已试算%d次。你随时可以说“结束”，我会先问你要不要整理记录；没做的部分不会补写。*" % (label, evaluated)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def loads(value):
    if isinstance(value, dict):
        return copy.deepcopy(value)
    if not isinstance(value, str) or len(value) > 300000:
        raise ValueError("JSON须为不超过300000字符的字符串或对象")
    def invalid(token):
        raise ValueError("拒绝非有限数字：" + token)
    result = json.loads(value, parse_constant=invalid)
    if not isinstance(result, dict):
        raise ValueError("JSON顶层必须是对象")
    return result


def clean_text(value, limit=6000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("文本须为不超过%d字符的字符串" % limit)
    return value


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int,float)):
        raise ValueError("必须为有限数值，不能是布尔值")
    if not low <= value <= high:
        raise ValueError("数值须在%s至%s之间" % (low,high))
    if not math.isfinite(value):
        raise ValueError("必须为有限数值")
    return float(value)


def phase_value(phase):
    if type(phase) is not int or phase not in (0,1):
        raise ValueError("phase须为整数0或1")
    return phase


def _variants_of(case):
    variants = case.get("surface_variants")
    if not isinstance(variants, list) or not variants:
        return [{}]
    return [v if isinstance(v, dict) else {} for v in variants]


def _variant_of(case, state):
    variants = _variants_of(case)
    index = 0
    if state:
        index = state.get("variant_index", 0)
        if type(index) is not int or not 0 <= index < len(variants):
            index = 0
    return variants[index]


def _data_of(case, state):
    """Case data with the active variant's shallow overrides applied."""
    data = case["data"]
    overrides = _variant_of(case, state).get("data_overrides") if state else None
    if not overrides:
        return data
    merged = copy.deepcopy(data)
    merged.update(copy.deepcopy(overrides))
    return merged


def _fmt(text, case, state):
    """Substitute {surface_key} placeholders; leave {reason} for later stages."""
    if not isinstance(text, str) or "{" not in text:
        return text
    surface = _variant_of(case, state).get("surface", {}) if state else {}
    def repl(match):
        key = match.group(1)
        if key == "reason":
            return match.group(0)
        if key in surface:
            return str(surface[key])
        if state is None:
            return match.group(0)
        raise ValueError("变体缺少占位符：" + key)
    return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", repl, text)


def _active_items(case, state):
    """Rendered item list (rank cards / allocation entries) for this state."""
    items = _data_of(case, state).get("items", [])
    by_id = {it["id"]: it for it in items if isinstance(it, dict) and "id" in it}
    ids = _variant_of(case, state).get("item_ids") if state else None
    if ids:
        ordered = [by_id[i] for i in ids if i in by_id]
        if ordered:
            items = ordered
    return [{"id": it["id"], "text": _fmt(it.get("text", ""), case, state)} for it in items]


def _option_perm(case, state):
    perm = state.get("option_perm") if state else None
    if isinstance(perm, list) and sorted(perm) == ["A", "B", "C"]:
        return list(perm)
    return ["A", "B", "C"]


def _display_to_original(case, state, letter):
    perm = _option_perm(case, state)
    if letter in ("A", "B", "C"):
        return perm[ord(letter) - 65]
    return letter


def _original_to_display(case, state, letter):
    perm = _option_perm(case, state)
    if letter in perm:
        return chr(65 + perm.index(letter))
    return letter


def _rendered_options(case, phase, state):
    raw = case["data"].get("options", [{}, {}])[phase]
    perm = _option_perm(case, state)
    return {letter: _fmt(raw.get(perm[i], ""), case, state) for i, letter in enumerate(("A", "B", "C"))}


def _budget_of(data, phase):
    budget = data.get("budget", 0)
    if isinstance(budget, list):
        return budget[phase] if phase < len(budget) else budget[-1]
    return budget


def case_of(state):
    if state.get("engine_version") != ENGINE_VERSION:
        raise ValueError("状态版本与当前引擎不兼容，请重新开始")
    cid = state.get("case_id")
    case = state.get("case_snapshot")
    if case is None:
        if cid not in BANK["cases"]:
            raise ValueError("未知案例")
        case = BANK["cases"][cid]
        if state.get("case_version") != BANK["case_version"]:
            raise ValueError("题库版本与当前状态不一致，请重新开始")
    else:
        if state.get("case_version") != CASE_VERSION:
            raise ValueError("题库版本与当前状态不一致，请重新开始")
        if case.get("case_id") != cid:
            raise ValueError("状态案例快照不一致")
    phase_value(state.get("phase"))
    if state.get("task_id") != case["task_id"]:
        raise ValueError("状态中任务与案例不一致")
    if state.get("group_id") not in set(CATALOG["groups"]) | {"unknown"}:
        raise ValueError("未知所属大类")
    if type(state.get("group_confirmed")) is not bool:
        raise ValueError("group_confirmed须为布尔值")
    if type(state.get("report_gate", False)) is not bool:
        raise ValueError("report_gate须为布尔值")
    variants = _variants_of(case)
    vi = state.get("variant_index", 0)
    if type(vi) is not int or not 0 <= vi < len(variants):
        raise ValueError("variant_index超出范围")
    perm = state.get("option_perm")
    if perm is not None and (not isinstance(perm, list) or sorted(perm) != ["A", "B", "C"]):
        raise ValueError("option_perm格式不正确")
    if not isinstance(state.get("events"), list) or len(state["events"]) > 160:
        raise ValueError("状态事件格式不正确或本次体验过长")
    return case


def _mode_of(case, state=None):
    if isinstance(state, dict):
        fam = state.get("family_snapshot")
        if fam is not None:
            return fam["mode"]
    return BANK["families"][case["task_id"]]["mode"]


def _group_relevant(case, group_id):
    if group_id in (None, "unknown") or group_id not in CATALOG["groups"]:
        return False
    own = set(CATALOG["groups"][group_id].get("majors", []))
    return bool(own & set(case.get("related_majors", [])))


def choose_case(params):
    task = ALIASES.get(params.get("task_id"), params.get("task_id", "auto")) or "auto"
    cid = params.get("case_id", "")
    variant = params.get("variant_id", "")
    excluded = params.get("exclude_case_ids", [])
    if not isinstance(excluded,list) or any(not isinstance(x,str) for x in excluded):
        raise ValueError("exclude_case_ids须为字符串数组")
    if cid and cid != "auto":
        if cid not in BANK["cases"]:
            raise ValueError("case_id不存在")
        if task not in ("auto", BANK["cases"][cid]["task_id"]):
            raise ValueError("task_id与case_id冲突")
        return cid
    if task != "auto" and task not in BANK["families"]:
        raise ValueError("未知task_id")
    if variant and variant != "auto":
        if task == "auto":
            raise ValueError("指定variant_id时须同时指定task_id")
        cid = task + "_" + str(variant)
        if cid not in BANK["cases"]:
            raise ValueError("variant_id不存在")
        return cid
    # Legacy task-only calls preserve original numeric fixtures.
    if task in DEFAULTS and "seed" not in params and not variant and not cid and DEFAULTS[task] not in excluded:
        return DEFAULTS[task]
    allowed = GROUP_FAMILIES.get(params.get("group_id"), list(BANK["families"])) if task == "auto" else [task]
    candidates = [c for c,v in BANK["cases"].items() if v["task_id"] in allowed]
    available = [c for c in candidates if c not in excluded]
    if not available:
        raise ValueError("当前候选案例均已排除，请清空已体验列表或更换活动")
    relevant = [c for c in available if _group_relevant(BANK["cases"][c], params.get("group_id"))]
    if relevant:
        available = relevant
    seed = str(params.get("seed", "0"))
    rank = int(hashlib.sha256((seed+"|"+str(params.get("group_id","unknown"))+"|"+task).encode("utf-8")).hexdigest(),16)
    return available[rank % len(available)]


PLAN_SCHEMAS = {
    "route":{"path":"按本人明确顺序填写节点字符串数组，须包含起终点", "reason":"本人理由，可为空，不得补写"},
    "sensor":{"threshold":"0至100的有限数值", "reason":"本人理由，可为空，不得补写"},
    "control":{"k":"0至2的有限数值", "reason":"本人理由，可为空，不得补写"},
    "choice":{"choice":"A或B或C，仅能有一个", "reason":"本人理由，可为空，不得补写"},
    "rank":{"order":"把题目给出的卡片按本人明确顺序排列：项目id字符串数组，每张卡片恰好出现一次", "reason":"本人理由，可为空，不得补写"},
    "allocation":{"allocation":"对象：每个事项id对应一个非负整数（单位见题面），所有事项都要出现，总和须正好等于题面总额", "reason":"本人理由，可为空，不得补写"},
    "compose":{"response":"本人写下的正文原文，不能为空，不得替本人改写", "title":"本人给正文起的标题，没有则为空字符串", "reason":"可为空"},
}


def normalize_context(case,phase,state=None):
    mode = _mode_of(case, state)
    schema = PLAN_SCHEMAS[mode]
    options = _rendered_options(case, phase, state) if mode == "choice" else case["data"].get("options",[{},{}])[phase]
    ctx = {"case_id":case["case_id"],"task_id":case["task_id"],"phase":phase,"mode":mode,"plan_fields":schema,"options":options,"extract_schema":{"action":"submit|hint|clarify|stop","plan":schema,"quote":"学生本轮原文连续片段","question":"需要时只问一个澄清问题"},"rule":"不代替用户选方案，不算结果，不判断专业适配；多备选须clarify，JSON只是候选，必须本人确认后计算。"}
    if mode in ("rank","allocation"):
        ctx["items"] = _active_items(case, state)
        ctx["budget"] = _budget_of(_data_of(case, state), phase) if mode == "allocation" else ""
    if mode == "compose":
        data = _data_of(case, state)
        ctx["writing"] = _fmt(data.get("writing", ["", ""])[phase], case, state)
        ctx["max_chars"] = data.get("max_chars", 800)
    return ctx


def task_text(case,phase,state=None):
    phase_value(phase)
    data=_data_of(case,state); mode=_mode_of(case,state)
    parts=["## "+case["title"], "*这是为理解工作方法编写的教学情境，数据为合成，不用来判断你的能力或专业适合程度。*", _fmt(case["context"],case,state),"### "+("先看看现在的情况" if phase==0 else "接下来，情况有了变化"),_fmt(case["phases"][phase],case,state)]
    if mode=="choice":
        evidence=data.get("evidence",["",""])
        if evidence[phase]: parts.append(_fmt(evidence[phase],case,state))
        rendered=_rendered_options(case,phase,state)
        parts += ["- **方案 "+key+"**："+text for key,text in rendered.items()]
        parts.append("**你会怎么做？**\n\n请点选一个做法。这里没有标准答案——几个做法往年都有人真选过；想补充自己的考虑，可以在核对时选择“我想改一下”再告诉我。还拿不准的话，可以先要一点提示。")
    elif mode=="route":
        parts.append("**可走的路段**（两个方向都能走）：\n\n| 路段 | 基础耗时 |\n| --- | --- |\n"+"\n".join("| %s ↔ %s | %s%s |"%(a,b,w,data["unit"]) for a,b,w in data["edges"]))
        parts.append("**你打算怎么走？**\n\n说出从%s到%s经过的地点，按先后顺序写就好，也可以补充你的考虑。"%(data["start"],data["end"]))
    elif mode=="sensor":
        parts.append("**这次用到的样本**\n\n1表示确实有需要检测的情况，0表示没有。\n\n| 检测分数 | 实际情况（1/0） |\n| --- | --- |\n"+"\n".join("| %s | %s |"%tuple(s) for s in data["samples"]))
        parts.append("**你会把分界线设在多少分？**\n\n选一个0到100的数。分数达到这个数，就算检测到了。也可以说说你更担心哪一种判断错误。")
    elif mode=="control":
        gain=data["gains"][phase]
        limit=data.get("limits",[data.get("limit",2)]*2)[phase]
        disturbance=data.get("disturbances",[0,0])[phase]
        parts.append("**这个简化模型怎样变化**\n\n- 起始位置：%s；希望到达的位置：%s。\n- 一共观察%s步。每一步先算“目标位置减去当前位置”，再乘你选的调整力度k。\n- 每一步的调整量最多为%s，反方向最多为−%s。\n- 下一步的位置 = 当前位置 + %s × 实际调整量 − %s。最后一项表示每一步受到的固定外部影响。"%(data["initial"],data["target"],data["steps"],limit,limit,gain,disturbance))
        parts.append("**希望看到的结果**\n\n最后一步离目标不超过%s；过程中超过目标的幅度不超过%s。"%(data["error_target"],data["overshoot_limit"]))
        parts.append("**你想用多大的调整力度？**\n\n用0到2之间的一个数表示，题目把它记作k。数值越大，每次根据偏差做出的调整越强。这里只观察这个简化模型里的变化。")
    elif mode=="rank":
        items=_active_items(case,state)
        parts.append("**这次要排序的卡片**\n\n"+"\n".join("- "+it["text"] for it in items))
        parts.append("**你会怎么排？**\n\n按题面要求说出先后顺序（例如“××第一，××第二……”），把每张卡片都排到，也可以补充你的理由。")
    elif mode=="allocation":
        items=_active_items(case,state)
        budget=_budget_of(data,phase); unit=data.get("unit",""); step=data.get("min_step") or 1; cap=data.get("max_per_item")
        parts.append("**这次要分配的事项**\n\n"+"\n".join("- "+it["text"] for it in items))
        rule="分配规则：总额 **%s%s**，必须正好分完；每项最小单位 %s%s，可以是 0。"%(budget,unit,step,unit)
        if cap is not None: rule+="单项最多 %s%s。"%(cap,unit)
        parts.append(rule)
        parts.append("**你会怎么分？**\n\n逐项说出各给多少，再说说你的理由。没有能让所有人都满意的方案，重要的是你按什么取舍。")
    else:
        writing=data.get("writing",["",""])
        parts.append("**这次的写作任务**\n\n"+_fmt(writing[phase],case,state))
        if data.get("title_prompt"): parts.append(_fmt(data["title_prompt"],case,state))
        parts.append("直接写下你的话就好；标题可以另起一行写“标题：……”。这段话不会被评分，会原样保留在你的记录里。")
    parts.append("*可以求提示，也可以随时结束；结束前我会先问你要不要整理记录。*")
    return "\n\n".join(parts)


def validate_plan(case, plan, state=None, phase=0):
    if not isinstance(plan,dict): raise ValueError("plan必须为对象")
    mode=_mode_of(case,state)
    key={"route":"path","sensor":"threshold","control":"k","choice":"choice","rank":"order","allocation":"allocation","compose":"response"}[mode]
    allowed={key,"reason"} | ({"title"} if mode=="compose" else set())
    if key not in plan or set(plan)-allowed: raise ValueError("本题仅接受%s和可选reason字段"%("、".join(sorted(allowed))))
    reason=clean_text(plan.get("reason",""),4000)
    if mode=="route":
        path=plan[key]; nodes={x for e in case["data"]["edges"] for x in e[:2]}
        if not isinstance(path,list) or not 2<=len(path)<=20 or any(not isinstance(x,str) or x not in nodes for x in path): raise ValueError("路线须为本题有效节点数组，长度2至20")
        if path[0]!=case["data"]["start"] or path[-1]!=case["data"]["end"]: raise ValueError("路线须包含本题起点与终点")
        value=list(path)
    elif mode=="choice":
        if plan[key] not in ("A","B","C"): raise ValueError("请明确选择A、B或C中的一个")
        value=plan[key]
    elif mode in ("sensor","control"):
        value=number(plan[key],0,100 if mode=="sensor" else 2)
    elif mode=="rank":
        ids=[it["id"] for it in _active_items(case,state)]
        order=plan[key]
        if not isinstance(order,list) or any(not isinstance(x,str) for x in order) or sorted(order)!=sorted(ids):
            raise ValueError("排序须把每张卡片恰好排入一次")
        value=list(order)
    elif mode=="allocation":
        data=_data_of(case,state)
        ids=[it["id"] for it in _active_items(case,state)]
        alloc=plan[key]
        if not isinstance(alloc,dict) or set(alloc)!=set(ids):
            raise ValueError("分配须恰好覆盖每个事项各一次")
        budget=_budget_of(data,phase); step=data.get("min_step") or 1; cap=data.get("max_per_item")
        if cap is None: cap=budget
        total=0
        for name,amount in alloc.items():
            if isinstance(amount,bool) or not isinstance(amount,int):
                raise ValueError("每项须为整数")
            if amount<0: raise ValueError("每项不能为负")
            if amount%step!=0: raise ValueError("每项须为最小单位%s的倍数"%step)
            if amount>cap: raise ValueError("单项最多%s"%cap)
            total+=amount
        if total!=budget: raise ValueError("各项总和须正好等于%s"%budget)
        value=dict(alloc)
    else:
        data=_data_of(case,state)
        limit=data.get("max_chars",800)
        response=clean_text(plan[key],max(limit*2,800))
        if not response.strip(): raise ValueError("正文不能为空")
        if len(response)>limit: raise ValueError("正文请在%s字以内"%limit)
        value=response
    result={key:value,"reason":reason}
    if mode=="compose":
        title=plan.get("title","")
        if not isinstance(title,str) or len(title)>40: raise ValueError("标题须为不超过40字的字符串")
        result["title"]=title.strip()
    return result


def parse_standard(case,text,state=None):
    """Conservative local correction parser; never selects among alternatives."""
    mode=_mode_of(case,state)
    if mode=="compose":
        base=text.strip()
        match=re.search(r"(?:^|[\n。！？；;，,])\s*标题[:：]\s*(.+)$", base)
        title=match[1].strip() if match else ""
        body=(base[:match.start()] if match else base).rstrip("。，,；; \n").strip()
        if body: return {"response":body,"title":title}
        return None
    raw=text.strip().replace("，",",").replace("。","")
    raw=re.sub(r"^(试算|选择|选|我选|改为|改成|那就|那|就用|就|设为|用)\s*", "", raw)
    raw=re.sub(r"吧$", "", raw).strip()
    if mode=="choice":
        match=re.fullmatch(r"([ABCabc])(?:[,:：;；\s]+(.+))?",raw)
        if match:return {"choice":match[1].upper(),"reason":match[2] or ""}
    elif mode in ("sensor","control"):
        raw=re.sub(r"^(?:阈值|threshold|k)\s*[=：:]?\s*", "", raw, flags=re.I)
        if re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)",raw):return {{"sensor":"threshold","control":"k"}[mode]:float(raw)}
    elif mode=="rank":
        ids=[it["id"] for it in _active_items(case,state)]
        parts=[x for x in re.split(r"[-－—→>,、\s]+",raw) if x]
        if len(parts)>1 and all(x in ids for x in parts): return {"order":parts}
    else:
        path=re.split(r"[-－—→>\s]+",raw.upper())
        if len(path)>1 and all(re.fullmatch(r"[A-Z]+",x) for x in path): return {"path":path}
    return None


def edge_weights(case,phase):
    d=case["data"]; blocked={frozenset(x) for x in d.get("blocked",[[],[]])[phase]}
    weights={frozenset((a,b)):w for a,b,w in d["edges"] if frozenset((a,b)) not in blocked}
    for a,b,w in d.get("edge_additions",[[],[]])[phase]:
        edge=frozenset((a,b))
        if edge in weights: weights[edge]+=w
    return weights


def shortest(case,phase):
    weights=edge_weights(case,phase); graph={}
    for edge,w in weights.items():
        a,b=tuple(edge); graph.setdefault(a,[]).append((b,w)); graph.setdefault(b,[]).append((a,w))
    start,end=case["data"]["start"],case["data"]["end"]
    q=[(0,start)]; dist={start:0}
    while q:
        score,node=heapq.heappop(q)
        if score!=dist[node]:continue
        if node==end:return score
        for other,w in graph.get(node,[]):
            value=score+w
            if value<dist.get(other,math.inf):dist[other]=value;heapq.heappush(q,(value,other))
    return None


def evaluate(case_id,plan,phase,state=None):
    phase_value(phase)
    snap=state.get("case_snapshot") if isinstance(state,dict) else None
    if snap is not None:
        if snap.get("case_id")!=case_id:raise ValueError("状态案例快照不一致")
        case=snap
    else:
        if case_id not in BANK["cases"]:raise ValueError("未知case_id")
        case=BANK["cases"][case_id]
    plan=validate_plan(case,plan,state,phase)
    mode=_mode_of(case,state); d=_data_of(case,state)
    out={"case_id":case_id,"task_id":case["task_id"],"case_version":CASE_VERSION or BANK["case_version"],"phase":phase,"kind":"synthetic_teaching_result","plan":plan}
    if mode=="choice":
        outcome=copy.deepcopy(d["outcomes"][phase][plan["choice"]])
        if isinstance(outcome.get("feedback"),str):
            template=_fmt(outcome["feedback"],case,state)
            reason_block=(quoted(plan["reason"])+"\n\n") if plan.get("reason") else ""
            outcome["feedback"]=template.replace("{reason}",reason_block)
        out.update(outcome);out["valid"]=True
    elif mode=="route":
        weights=edge_weights(case,phase); total=0; bad=[]
        for a,b in zip(plan["path"],plan["path"][1:]):
            edge=frozenset((a,b))
            if edge not in weights:bad.append(a+"-"+b+"不存在或已封闭")
            else:total+=weights[edge]
        minimum=shortest(case,phase); deadline=d.get("deadlines",[None,None])[phase]
        out.update(valid=not bad,problems=bad,minutes=None if bad else total,unit=d["unit"],reference_min_minutes=minimum,deadline=deadline,meets_deadline=(None if deadline is None or bad else total<=deadline),any_path_meets_deadline=(None if deadline is None or minimum is None else minimum<=deadline))
    elif mode=="sensor":
        counts=dict(tp=0,fp=0,fn=0,tn=0)
        for score,label in d["samples"]:
            predicted=int(score>=plan["threshold"])
            counts[{(1,1):"tp",(1,0):"fp",(0,1):"fn",(0,0):"tn"}[predicted,label]]+=1
        fpw,fnw=d["weights"][phase]
        out.update(valid=True,**counts,sample_count=len(d["samples"]),false_alarm_weight=fpw,miss_weight=fnw,loss=fpw*counts["fp"]+fnw*counts["fn"])
    elif mode=="rank":
        items=_active_items(case,state); texts={it["id"]:it["text"] for it in items}
        out.update(valid=True,order=plan["order"],item_order=[it["id"] for it in items],item_texts=texts,top_item=plan["order"][0],bottom_item=plan["order"][-1])
    elif mode=="allocation":
        items=_active_items(case,state); texts={it["id"]:it["text"] for it in items}
        budget=_budget_of(d,phase); unit=d.get("unit","")
        top=None
        for it in items:
            if top is None or plan["allocation"][it["id"]]>plan["allocation"][top]: top=it["id"]
        out.update(valid=True,allocation=plan["allocation"],budget=budget,unit=unit,item_order=[it["id"] for it in items],item_texts=texts,top_item=top)
    elif mode=="compose":
        out.update(valid=True,response=plan["response"],title=plan.get("title",""))
    else:
        gain=d["gains"][phase]; limit=d.get("limits",[d.get("limit",2)]*2)[phase]; disturbance=d.get("disturbances",[0,0])[phase]
        target=d["target"]; xs=[float(d["initial"])]; us=[]
        for _ in range(d["steps"]):
            u=max(-limit,min(limit,plan["k"]*(target-xs[-1])));us.append(u);xs.append(xs[-1]+gain*u-disturbance)
        error=abs(xs[-1]-target);overshoot=max(0,max(xs)-target)
        settled=next((i for i in range(1,len(xs)) if all(abs(x-target)<=d["error_target"] for x in xs[i:])),None)
        out.update(valid=True,gain=gain,target=target,disturbance=disturbance,actuator_limit=limit,trajectory=[round(x,6) for x in xs],controls=[round(x,6) for x in us],final_abs_error=round(error,6),max_overshoot=round(overshoot,6),within_observation_settled_step=settled,meets_teaching_target=error<=d["error_target"] and overshoot<=d["overshoot_limit"])
    return out


def feedback(result, state=None):
    if "feedback" in result:return "### 看看这个选择会怎样\n\n"+result["feedback"]+"\n\n*这只是对本题方案的反馈，不代表能力或专业适合程度。*"
    fam=state.get("family_snapshot") if isinstance(state,dict) else None
    mode=fam["mode"] if fam else BANK["families"].get(result.get("task_id"),{}).get("mode","")
    if mode=="rank":
        texts=result.get("item_texts",{})
        top=texts.get(result["top_item"],result["top_item"]); bottom=texts.get(result["bottom_item"],result["bottom_item"])
        reason_block=("你给出的理由：\n\n"+quoted(result["plan"].get("reason",""))+"\n\n") if result["plan"].get("reason") else ""
        return ("### 看看你的排序\n\n- 你排在第一的：**"+top+"**\n- 你排在最后的：**"+bottom+"**\n\n"+reason_block+
            "把「"+top+"」放在最前、把「"+bottom+"」放在最后——排序没有对错，它呈现的是这一次你在这些事物之间的取舍顺序。两个阶段连起来看，动了哪几张、为什么动，往往比顺序本身更值得回味。\n\n*这是一种倾向线索，不是能力判断，也不是专业匹配结论。*")
    if mode=="allocation":
        texts=result.get("item_texts",{}); unit=result.get("unit","")
        rows="\n".join("| %s | %s%s |"%(texts.get(k,k),result["allocation"][k],unit) for k in result.get("item_order",list(result["allocation"])))
        top=texts.get(result.get("top_item"),result.get("top_item",""))
        reason_block=("你给出的理由：\n\n"+quoted(result["plan"].get("reason",""))+"\n\n") if result["plan"].get("reason") else ""
        return ("### 看看你的分配\n\n| 事项 | 分给多少 |\n| --- | --- |\n"+rows+"\n\n"+reason_block+
            "这次你把最多的"+unit+"给了「"+top+"」。分配没有标准答案，它呈现的是你在几个互相冲突的诉求之间放的权重；别人把最多的给另一项，同样可能成立。\n\n*这是一种倾向线索，不是能力判断，也不是专业匹配结论。*")
    if mode=="compose":
        title_block="\n\n标题：「"+markdown_text(result["title"])+"」" if result.get("title") else ""
        return ("### 你写下的这段话\n\n"+quoted(result["response"])+title_block+"\n\n这段话不会被评分，也不会被用来推断能力或适合度；它会在你的探索记录里原样保留，含义由你自己决定。")
    if result["task_id"]=="route":
        if not result["valid"]:return "### 这条路暂时走不通\n\n"+"\n".join("- "+p for p in result["problems"])+"\n\n**这次没有计算总时长。**你可以换一条路再想想。"
        text="### 看看这条路线\n\n- **你的方案耗时：%s%s**\n- 当前路网中，最短路线耗时：%s%s"%(result["minutes"],result["unit"],result["reference_min_minutes"],result["unit"])
        if result["deadline"] is not None:text+="\n\n时限为%s，当前方案**%s按时到达**；给定路网中%s满足时限的路线。"%(result["deadline"],"可以" if result["meets_deadline"] else "不能","存在" if result["any_path_meets_deadline"] else "不存在")
        return text
    if result["task_id"]=="sensor":return "### 看看这条分界线的结果\n\n| 判断结果 | 条数 |\n| --- | --- |\n| 有情况，也检出了 | {tp} |\n| 没有情况，却报出了（误报） | {fp} |\n| 有情况，却漏掉了（漏报） | {fn} |\n| 没有情况，也没有报出 | {tn} |\n\n**总代价：{fp} × {false_alarm_weight} + {fn} × {miss_weight} = {loss}**\n\n*只适用于这批教学样本和题目给定的代价，不能直接代表真实设备效果。*".format(**result)
    return "### 看看调整之后的变化\n\n- 最后一步离目标还差：**{final_abs_error}**\n- 过程中超过目标的最大幅度：**{max_overshoot}**\n- 题目希望的结果：**{goal}**\n\n各步位置：{trajectory}\n\n*这是简化教学模型，短时间内的表现不能证明真实系统一直稳定。*".format(goal="达到了" if result["meets_teaching_target"] else "还没达到",**result)


def scope_majors(group_id,confirmed,majors):
    if not isinstance(majors,list) or any(not isinstance(x,str) for x in majors):raise ValueError("majors须为完整专业名称字符串数组")
    all_majors={m for g in CATALOG["groups"].values() for m in g["majors"]}
    own=CATALOG["groups"].get(group_id,{}).get("majors",[]) if confirmed else []
    scope={"within_group":[],"cross_group":[],"unverified":[],"group_confirmed":bool(confirmed),"catalog_source":CATALOG["source_id"],"catalog_verification":CATALOG["verification"]}
    for major in dict.fromkeys(majors):
        if not confirmed or group_id=="unknown" or major not in all_majors:scope["unverified"].append(major)
        elif major in own:scope["within_group"].append(major)
        else:scope["cross_group"].append(major)
    scope["notice"]="只按用户提供大类清单区分范围；不推导跨类转入、辅修资格，也不把活动关联专业直接变成推荐。"
    return scope


def add_event(state,kind,**data):
    if len(state["events"])>=160:raise ValueError("本次体验事件过多，请结束并新开一次")
    state["events"].append(dict(event_id=len(state["events"])+1,kind=kind,phase=state["phase"],**data))


def preview_plan(plan, case=None, phase=0, state=None):
    if plan is None:
        return "还没有一个明确的方案。"
    if "choice" in plan:
        letter=plan["choice"]
        display=_original_to_display(case,state,letter) if case else letter
        text="**你的选择：方案 "+display+"**"
        if case:
            raw=case["data"]["options"][phase][letter]
            text+="\n\n"+(_fmt(raw,case,state) if state else raw)
    elif "path" in plan:text="**你的路线："+" → ".join(plan["path"])+"**"
    elif "threshold" in plan:text="**你的分界线："+str(plan["threshold"])+"分**"
    elif "k" in plan:text="**你的调整力度："+str(plan["k"])+"**"
    elif "order" in plan:
        texts={it["id"]:it["text"] for it in _active_items(case,state)} if case else {}
        text="**你的排序：**\n\n"+"\n".join("%d. %s"%(i,texts.get(x,x)) for i,x in enumerate(plan["order"],1))
    elif "allocation" in plan:
        texts={it["id"]:it["text"] for it in _active_items(case,state)} if case else {}
        unit=_data_of(case,state).get("unit","") if case else ""
        text="**你的分配：**\n\n"+"\n".join("- %s：%s%s"%(texts.get(k,k),plan["allocation"][k],unit) for k in (texts.keys() if texts else plan["allocation"].keys()))
    else:
        text="**你写下的内容：**\n\n"+quoted(plan.get("response",""))
        if plan.get("title"):text+="\n\n标题：「"+markdown_text(plan["title"])+"」"
    if plan.get("reason"):text+="\n\n你给出的理由：\n\n"+quoted(plan["reason"])
    return text


def suggestion_lines(state, case):
    """Evidence-based next-step suggestions; never a score, ranking, or aptitude verdict."""
    completed=[e for e in state["events"] if e["kind"]=="evaluated"]
    lines=["## 下一步建议（依据你这次实际做过的内容）"]
    if not completed:
        lines.append("这次还没有试算任何方案，下面的建议只依据你选过的题目，依据较弱；如果愿意，可以先把这一题试完再看。")
    related=[m for m in case["related_majors"]]
    if state["group_confirmed"] and state["group_id"] in CATALOG["groups"]:
        scope=scope_majors(state["group_id"],True,related)
        if scope["within_group"]:
            lines.append("**与这次活动直接相关、且在你确认的大类内：** "+"、".join(markdown_text(m) for m in scope["within_group"]))
        rest=scope["cross_group"]+scope["unverified"]
        if rest:
            lines.append("**也相关，但不在你确认的大类内（跨类资格需另行核验）：** "+"、".join(markdown_text(m) for m in rest))
    elif related:
        lines.append("**与这次活动直接相关的专业方向：** "+"、".join(markdown_text(m) for m in related)+"\n\n*你还没有确认所属大类，这里不判断哪些专业对你可选。*")
    others=[fid for fid in GROUP_FAMILIES.get(state["group_id"],[]) if fid!=state["task_id"] and fid in FAMILY_NAMES]
    if not others:
        others=[fid for fid in FAMILY_NAMES if fid!=state["task_id"]]
    if others:
        picks="".join("「"+FAMILY_NAMES[fid]+"」" for fid in others[:2])
        lines.append("**再多一点依据：** 一次体验只呈现一种方法。建议再试一两类不同的活动，比如"+picks+"，把几次的感受放在一起比较，再下结论。")
    lines.append("**想深入了解某个专业：** 直接问我它“平时学什么课、做什么实验、毕业去向有哪些”，我会按知识库里的资料回答，并注明来源和年份。")
    lines.append("*这些建议只依据你本次实际完成并确认的内容和你写下的原话；不是测评分数，不是专业排名，也不是适合程度判断。*")
    return lines


def render_report(state):
    case=case_of(state); group=CATALOG["groups"].get(state["group_id"],{}).get("display_name","不清楚/暂不提供")
    completed=[e for e in state["events"] if e["kind"]=="evaluated"]
    cohort=state.get("cohort","")
    cohort_display="未提供；本次不据此判断年级资格" if cohort in ("","未知","跳过","未提供") else markdown_text(cohort)+"\n\n*由本人说明，未核验目录是否适用于该年级。*"
    lines=["# 本次专业活动探索记录", "**体验内容：** "+case["title"], "**所属大类：** "+markdown_text(group)+("（本人已确认）" if state["group_confirmed"] else "（尚未确认，暂不判断个人可选范围）"),"**入学年级：** "+cohort_display, "**记录状态：** "+("本人已确认整份记录" if state.get("record_confirmed") else "草稿。事实按已确认方案记录；整份记录尚未由本人确认")]
    if completed:
        phases={e["phase"] for e in completed}
        progress="已经试过初始方案和条件变化后的方案" if phases=={0,1} else "已经试过初始方案；还没有确认条件变化后的新方案"
        lines.append("## 这次实际做了什么\n\n"+progress+"。以下只列出实际完成的内容。")
    else:
        lines.append("## 这次实际做了什么\n\n还没有确认并试算任何方案，因此没有计算结果。已经提出但未确认的方案会单独列出。")
    for event in state["events"]:
        if event["kind"] in ("evaluated","recomputed"):
            label=("条件变化后，重新检查原方案" if event["kind"]=="recomputed" else ("第一次：本人确认的方案" if event["phase"]==0 else "条件变化后：本人确认的新方案"))
            chosen=preview_plan(event["plan"],case,event["phase"],state)
            lines += ["## "+label,chosen]
            if event.get("proposal_raw"):
                lines += ["你当时说的是：\n\n"+quoted(event["proposal_raw"])]
            lines.append(feedback(event["result"],state))
    if state.get("pending_plan"):
        lines += ["## 已提出、还没确认的方案", preview_plan(state["pending_plan"],case,state["phase"],state),"*这个方案没有作为你的正式选择，也没有试算。*", "你的原话：\n\n"+quoted(state.get("pending_raw",""))]
    elif state.get("unfinished_plan"):
        pending=state["unfinished_plan"]
        lines += ["## 已提出、还没确认的方案",preview_plan(pending["plan"],case,pending["phase"],state),"*结束前尚未确认，没有试算，也没有改写前面的结果。*","你的原话：\n\n"+quoted(pending.get("raw",""))]
    reflection=state.get("reflection_raw","")
    lines += ["## 你对这次体验的感受"]
    if reflection:
        lines += [quoted(reflection), "*"+("这段感受已随记录由本人确认。" if state.get("record_confirmed") else "保留本人原话；这段感受尚未随整份记录确认。")+"*"]
    else:
        lines += ["你在整理记录前选择不填写感受，或当时还没有填写。不会根据做题结果替你补写兴趣判断。"]
    lines += ["## 这次接触到了什么", "**涉及的方法：** "+"、".join(case["knowledge_tags"]),"**还没有体验：** "+case["boundary"],"*这些关联只帮助你继续了解专业，不是推荐或适合程度排名。*"]
    if state.get("requested_majors"):
        lines.append("## 你想继续了解的专业")
        scope=scope_majors(state["group_id"],state["group_confirmed"],state["requested_majors"])
        for k,label in [("within_group","按用户清单在本大类内，可继续了解"),("cross_group","跨大类兴趣，转入资格未核验"),("unverified","所属范围待核验")]:
            if scope[k]:lines.append("**"+label+"：** "+"、".join(markdown_text(m) for m in scope[k]))
    lines += suggestion_lines(state,case)
    lines += ["## 接下来可以怎么了解", "挑出刚才你最想继续追问的一点，再看一份相关专业的入门材料、真实课程或实验介绍，比较其中哪些事情你还愿意亲手尝试。", "*资料边界：大类目录来自用户提供的清单，尚未按个人年级核验分流规则。案例使用合成教学数据；建议部分只依据你实际完成的内容，没有测量能力、人格或专业适合程度，也不做专业排名。*"]
    return "\n\n".join(lines)


def gate_prompt(state):
    """Explicit pre-report question. The record is never rendered before this."""
    case=case_of(state)
    evaluated=sum(e.get("kind")=="evaluated" for e in state.get("events",[]))
    lines=["## 要现在为你整理这次的探索记录吗？",
        "本次体验："+case["title"]+"。已确认并试算 **%d** 个方案；没完成的部分不会补写。"%evaluated,
        "整理之前还有一件**完全自愿**的事：你可以留下一句这次的想法——印象最深的一刻、一句吐槽，或者给这次体验起个一句话标题都可以。你的想法会原样写进记录。",
        "- 想留一句：直接把你的想法告诉我；",
        "- 不想留：说“生成记录”，或点页面上的「直接生成记录」；",
        "- 还不想结束：点「先不生成」，回到刚才的内容，记录不会生成。"]
    return "\n\n".join(lines)


def _report_final(state, raw, skip_reflection=False):
    """Render the record after explicit gate consent; thoughts only from this explicit entrance."""
    if state["status"] in ("stopped","completed"):
        return response(state,"report",report=render_report(state))
    if state.get("pending_plan"):
        state["unfinished_plan"]={"plan":copy.deepcopy(state["pending_plan"]),"raw":state.get("pending_raw",""),"phase":state["phase"]}
        state["pending_plan"]=None
    text=raw.strip()
    if text and not skip_reflection:
        state["reflection_raw"]=text;add_event(state,"reflection",raw_text=text,at_report_gate=True)
    elif not state.get("reflection_raw"):
        add_event(state,"reflection_skipped",raw_text="",at_report_gate=True)
    state["report_gate"]=False;state["record_confirmed"]=False;state["status"]="awaiting_record_confirmation"
    add_event(state,"report_generated")
    return response(state,"report_ready",report=render_report(state),
        feedback_text="记录已经在上面了，请核对一下：\n\n- 准确：点「记录准确，完成体验」；\n- 想法想改：点「改一下我的想法」，改完再核对一次；\n- 先不确认：点「先不确认，保留」，记录会如实标注尚未确认。")


def _resume_current(state, case):
    state["report_gate"]=False
    if state.get("status")=="evaluated" and state.get("last_result"):
        return response(state,"resumed",feedback_text="好的，还没有生成记录，我们接着刚才的内容。\n\n"+feedback(state["last_result"],state))
    if state.get("status")=="awaiting_confirmation" and state.get("pending_plan"):
        return response(state,"resumed",preview="### 继续核对这个方案\n\n"+preview_plan(state["pending_plan"],case,state["phase"],state),feedback_text=correction_format(case,state))
    return response(state,"resumed",task_text(case,state["phase"],state),feedback_text="好的，还没有生成记录，我们接着刚才的内容。")


def response(state=None,action="ready",prompt="",preview="",feedback_text="",result=None,report="",**extra):
    out=dict(ok=True,action=action,state_json=dumps(state) if state is not None else "",prompt=prompt,preview=preview,feedback=feedback_text,result_json=dumps(result) if result is not None else "",report=report,error="")
    if state is not None:
        case=case_of(state);out.update(case_id=state["case_id"],task_id=state["task_id"],phase=state["phase"],title=case["title"],variant_id=case["variant_id"],normalizer_context=dumps(normalize_context(case,state["phase"],state)),knowledge_query=" ".join([case["title"]]+case["knowledge_tags"]+case["related_majors"][:3]))
    out.update(extra)
    pieces=[x for x in (report,preview,feedback_text) if x] if report else [x for x in (stage_guide(state) if state is not None else "",prompt,preview,feedback_text) if x]
    out["display_text"]="\n\n".join(pieces)
    return out


def dispatch(params):
    state=None
    original_state=None
    try:
        params=loads(params);op=params.get("op","catalog")
        if op=="catalog":return response(action="catalog",catalog_json=dumps({"engine_version":ENGINE_VERSION,"case_version":BANK["case_version"],"families":BANK["families"],"cases":[{"case_id":c["case_id"],"task_id":c["task_id"],"variant_id":c["variant_id"],"title":c["title"]} for c in BANK["cases"].values()],"groups":CATALOG["groups"],"group_families":GROUP_FAMILIES}))
        if op=="start":
            group=params.get("group_id","unknown") or "unknown"
            if group not in set(CATALOG["groups"])|{"unknown"}:raise ValueError("group_id不存在；两个伯芩班须按方向区分，不能只凭同名猜测")
            confirmed=params.get("group_confirmed",False)
            if type(confirmed) is not bool:raise ValueError("group_confirmed须为布尔值")
            if group=="unknown":confirmed=False
            selection=dict(params)
            if not confirmed:selection["group_id"]="unknown"
            cid=choose_case(selection);case=BANK["cases"][cid]
            seed=str(params.get("seed","") or "")
            variants=_variants_of(case)
            variant_index=0
            if seed and case.get("surface_variants"):
                variant_index=int(hashlib.sha256((seed+"|variant|"+cid).encode("utf-8")).hexdigest(),16)%len(variants)
            option_perm=None
            if seed and case.get("surface_variants") and BANK["families"][case["task_id"]]["mode"]=="choice":
                letters=["A","B","C"];h=int(hashlib.sha256((seed+"|perm|"+cid).encode("utf-8")).hexdigest(),16)
                for i in range(2,0,-1):
                    j=h%(i+1);letters[i],letters[j]=letters[j],letters[i];h//=3
                if letters!=["A","B","C"]:option_perm=letters
            state=dict(engine_version=ENGINE_VERSION,case_version=CASE_VERSION or BANK["case_version"],case_id=cid,task_id=case["task_id"],phase=0,status="awaiting_plan",group_id=group,group_confirmed=confirmed,cohort=clean_text(params.get("cohort","未知"),80),events=[],pending_plan=None,reflection_raw="",requested_majors=[],record_confirmed=False,variant_index=variant_index,option_perm=option_perm,report_gate=False,case_snapshot=case,family_snapshot=BANK["families"][case["task_id"]])
            add_event(state,"started",group_id=group,group_confirmed=confirmed)
            return response(state,"awaiting_plan",task_text(case,0,state))
        state=loads(params.get("state_json",""));original_state=copy.deepcopy(state);case=case_of(state)
        raw=clean_text(params.get("user_text",""));text=raw.strip().rstrip("。！! ")
        if op=="scope":
            scope=scope_majors(state["group_id"],state["group_confirmed"],params.get("majors",[]))
            return response(state,"scope_checked",scope_json=dumps(scope))
        if op=="report_final":
            return _report_final(state,raw,bool(params.get("skip_reflection")))
        if op=="report_cancel":
            return _resume_current(state,case)
        if op in ("stop","finish","hint") or wants_finish(raw) or (text in HINT_WORDS and op in ("propose","confirm")):
            is_stop=op in ("stop","finish") or wants_finish(raw)
            if is_stop:
                if state["status"] in ("stopped","completed"):
                    return response(state,"report",report=render_report(state))
                if state.get("report_gate"):
                    # The gate was already shown; a fresh explicit finish is consent to render now.
                    return _report_final(state,raw,skip_reflection=True)
                state["report_gate"]=True
                return response(state,"report_gate",feedback_text=gate_prompt(state))
            if state["status"] in ("stopped","completed"):
                return response(state,"report",report=render_report(state))
            state["report_gate"]=False
            add_event(state,"hint",raw_text=raw)
            return response(state,"hint",task_text(case,state["phase"],state),feedback_text="### 给你一点提示\n\n"+_fmt(case["hint"],case,state)+"\n\n你可以继续想一个方案，也可以先结束；结束前我会先问你要不要整理记录。")
        if op=="report":return response(state,"report",report=render_report(state))
        if state["status"] in ("stopped","completed"):
            return response(state,"report",report=render_report(state))
        if state.get("report_gate") and op=="propose":
            # Natural-language answers while the report gate is open.
            if text in GATE_CANCEL_WORDS:
                return _resume_current(state,case)
            if looks_like_question(text):
                return response(state,"clarify",feedback_text="你是想留一句想法、直接生成记录，还是先不生成、继续刚才的内容？告诉我你的意思就好。")
            return _report_final(state,raw,skip_reflection=False)
        if op=="propose":
            if state["status"] not in ("awaiting_plan","awaiting_confirmation"):raise ValueError("当前阶段已计算；请advance或reflect，不重复覆盖事实")
            candidate=loads(params["candidate_json"]) if params.get("candidate_json") else {}
            action=candidate.get("action",params.get("candidate_action","submit"))
            if action in ("stop","finish") and not wants_finish(raw):
                return response(state,"clarify",feedback_text="你是想继续试一个方案，还是先到这里、看看目前的记录？我会按你的意思继续。")
            if action in ("stop","finish","hint"):
                return dispatch({"op":action,"state_json":dumps(state),"user_text":raw})
            if action=="clarify":
                state["pending_plan"]=None;state["status"]="awaiting_plan";add_event(state,"clarification",raw_text=raw)
                question=clean_text(candidate.get("question", "你想先试哪一个方案？可以选定一个，也可以先要一点提示。"),300)
                return response(state,"clarify",task_text(case,state["phase"],state),feedback_text="### 我想确认一下\n\n"+markdown_text(question))
            if action!="submit":raise ValueError("未知候选action")
            plan=candidate.get("plan")
            if plan is None and params.get("plan_json"):plan=loads(params["plan_json"])
            if plan is None:plan=parse_standard(case,raw,state)
            if plan is None:return response(state,"clarify",task_text(case,state["phase"],state),feedback_text="### 我还没听清你的选择\n\n你想先试哪一个方案？可以直接说一个明确的选择，也可以先要一点提示。")
            mode=_mode_of(case,state)
            if mode=="choice" and isinstance(plan,dict) and plan.get("choice") in ("A","B","C"):
                plan=dict(plan);plan["choice"]=_display_to_original(case,state,plan["choice"])
            plan=validate_plan(case,plan,state,state["phase"])
            if not raw.strip():raise ValueError("候选方案必须绑定学生本轮非空原文")
            if plan.get("reason") and plan["reason"] not in raw:raise ValueError("方案理由须保留学生本轮连续原话，不可替本人改写或补充")
            quote=candidate.get("quote",raw)
            if not isinstance(quote,str) or not quote or quote not in raw:raise ValueError("提取quote不是学生本轮原文连续片段")
            state["pending_plan"]=plan;state["pending_raw"]=raw;state["status"]="awaiting_confirmation";add_event(state,"proposed",raw_text=raw,plan=plan)
            return response(state,"awaiting_confirmation",preview="### 先核对一下，我有没有理解对\n\n"+preview_plan(plan,case,state["phase"],state)+"\n\n如果对，选择“就按这个试”。想改的话，请先选择“我想改一下”，再告诉我新方案。",feedback_text=correction_format(case,state))
        if op=="confirm":
            if state["status"] not in ("awaiting_confirmation","awaiting_plan"):raise ValueError("当前没有等待确认的方案")
            pending=state.get("pending_plan");plan=None;explicit_replacement=False
            if text in CONFIRM_WORDS|{"按这个方案试一试","就按这个试","就按这个试试","试试这个方案","可以，就这样","对，就这个","没错","准确","对"} and pending is not None:plan=pending
            elif text.startswith("试算") or text.startswith("更正并确认"):
                explicit_replacement=True
                confirmed_input=re.sub(r"^更正并确认[:：]?\s*", "", text)
                plan=parse_standard(case,confirmed_input,state)
                if plan is not None:
                    if _mode_of(case,state)=="choice" and plan.get("choice") in ("A","B","C"):
                        plan["choice"]=_display_to_original(case,state,plan["choice"])
                    plan=validate_plan(case,plan,state,state["phase"])
            else:
                # A correction becomes a new visible candidate, not an unconfirmed result.
                standard=parse_standard(case,raw,state)
                if standard is not None:return dispatch({"op":"propose","state_json":dumps(state),"user_text":raw,"plan_json":dumps(standard)})
            if plan is None:
                current=preview_plan(pending,case,state["phase"],state) if pending else "还没有一个明确的方案。"
                return response(state,"need_confirmation",preview="### 还没有开始试算\n\n"+current+"\n\n你是想按这个方案试一试，还是改成别的？如果还拿不准，也可以先要一点提示。",feedback_text=correction_format(case,state))
            result=evaluate(state["case_id"],plan,state["phase"],state)
            add_event(state,"evaluated",plan=plan,result=result,confirmation_raw=raw,proposal_raw=raw if explicit_replacement else state.get("pending_raw",raw))
            state["last_plan"]=plan;state["last_result"]=result;state["pending_plan"]=None;state["status"]="evaluated"
            return response(state,"evaluated",feedback_text=feedback(result,state),result=result,reflection_prompt=case["reflection"])
        if op=="advance":
            if state["phase"]!=0 or state["status"]!="evaluated":raise ValueError("仅第一阶段已计算后可进入条件变化")
            state["phase"]=1;state["status"]="awaiting_plan";state["pending_plan"]=None
            mode=_mode_of(case,state)
            if mode=="choice":
                old=state["last_plan"]["choice"]
                add_event(state,"conditions_changed",previous_choice=old,previous_option=case["data"]["options"][0][old])
                return response(state,"awaiting_plan",task_text(case,1,state),feedback_text="### 回头看看刚才的选择\n\n你刚才选择的是：\n\n"+quoted(_fmt(case["data"]["options"][0][old],case,state))+"\n\n**这次的条件和选项都变了，请重新看过后再选。**同一个字母，可能已经是另一个方案。")
            if mode in NEW_MODES:
                last=copy.deepcopy(state["last_plan"])
                add_event(state,"conditions_changed",previous_plan=last)
                return response(state,"awaiting_plan",task_text(case,1,state),feedback_text="### 回头看看刚才\n\n"+preview_plan(last,case,0,state)+"\n\n**这次的条件变了，请重新看过后再做。**可以沿用刚才的思路，也可以完全推翻；两次放在一起看，变化的地方最有意思。")
            result=evaluate(state["case_id"],state["last_plan"],1,state);add_event(state,"recomputed",plan=state["last_plan"],result=result)
            return response(state,"awaiting_plan",task_text(case,1,state),feedback_text="## 如果沿用刚才的方案\n\n"+feedback(result,state),result=result)
        if op=="reflect":
            if state["status"] not in ("evaluated","awaiting_record_confirmation"):raise ValueError("先完成一个明确方案，才生成探索草稿")
            majors=params.get("majors",[])
            scope=scope_majors(state["group_id"],state["group_confirmed"],majors)
            skip_reflection=text in {"跳过","先跳过","暂时跳过","不知道","不确定","还没想好","暂时没想好","没有","暂不填写","先不填"}
            state["reflection_raw"]="" if skip_reflection else raw;state["record_confirmed"]=False;state["status"]="awaiting_record_confirmation";state["requested_majors"]=majors
            add_event(state,"reflection_skipped" if skip_reflection else "reflection",raw_text=raw)
            return response(state,"awaiting_record_confirmation",preview="### 请看看这份记录\n\n准确的话，可以选择“确认记录”。感受想修改的话，直接告诉我完整的新说法；也可以先保留这份未确认的记录。",report=render_report(state),scope_json=dumps(scope))
        if op=="confirm_record":
            if state["status"]!="awaiting_record_confirmation":raise ValueError("当前没有待确认记录")
            if text.startswith("更正并确认：") or text.startswith("更正并确认:"):
                revised=re.split("[:：]",raw,maxsplit=1)[1]
                if not revised.strip():raise ValueError("更正反思不能为空")
                state["reflection_raw"]=revised
            elif text not in ("确认记录","确认","记录准确","没问题，确认","确认保存"):
                if text in ("先不确认","先保留这份记录","保留未确认记录","跳过","暂不确认"):
                    state["status"]="completed";add_event(state,"record_unconfirmed",raw_text=raw)
                    return response(state,"record_unconfirmed",report=render_report(state))
                # A replacement reflection remains visibly unconfirmed until the student accepts it.
                state["reflection_raw"]=raw;state["record_confirmed"]=False;add_event(state,"reflection_revised",raw_text=raw)
                return response(state,"need_record_confirmation",preview="### 已按你的原话更新感受\n\n请再看看记录，准确的话选择“确认记录”；也可以先保留这份未确认的记录。",report=render_report(state))
            state["record_confirmed"]=True;state["status"]="completed";add_event(state,"record_confirmed",raw_text=raw)
            return response(state,"completed",report=render_report(state))
        raise ValueError("未知op")
    except (ValueError,TypeError,KeyError,IndexError,AttributeError) as exc:
        # Retain the last valid input state for a recoverable correction where possible.
        message="这一步还没有完成，刚才已经确认过的内容仍保留在本次记录里。你可以换个说法继续，也可以直接结束并查看报告。"
        report=""
        if original_state is not None:
            try:report=render_report(original_state)
            except (ValueError,TypeError,KeyError,IndexError,AttributeError):pass
        if not report:
            message="这一步没有成功开始，因此还没有生成新的计算结果。你可以重新开始；如果你手里有先前的报告，可以继续按那份报告查看。"
        return dict(ok=False,action="error",state_json=dumps(original_state) if original_state is not None else "",prompt="",preview="",feedback=message,result_json="",report=report,display_text="### 需要再确认一下\n\n"+message+"\n\n*已确认的内容仍在；想整理完整记录时，说「生成记录」即可。*",normalizer_context="",knowledge_query="",error=str(exc))


def correction_format(case, state=None):
    mode=_mode_of(case, state)
    return {"choice":"*想修改请先选择“我想改一下”，再说明你想换成哪种做法，也可以补充理由。*", "route":"*想修改请先选择“我想改一下”，再按经过顺序写出整条路线，例如S-A-T；请使用题目中的地点。*", "sensor":"*想修改请先选择“我想改一下”，再说你想把分界线改成多少分。*", "control":"*想修改请先选择“我想改一下”，再告诉我新的调整力度，用0到2之间的数表示。*", "rank":"*想修改请先选择“我想改一下”，再按新顺序把每张卡片说一遍。*", "allocation":"*想修改请先选择“我想改一下”，再逐项说出新的分配，总和须正好等于题面总额。*", "compose":"*想修改请先选择“我想改一下”，再把你想写的内容完整重写一遍。*"}[mode]


def handler(params):
    return dispatch(params)


async def main(params):
    """Optional NK-GeniOS code-node wrapper; params may wrap inputs in params['input']."""
    if isinstance(params,dict) and "input" in params and "op" not in params:params=params["input"]
    return dispatch(params)
