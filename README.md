# 专业试驾场 v4.0.0

「专业试驾场」是面向南开大学大类分流新生的专业探索智能体，运行于 NK-GeniOS。项目提供 14 类活动、42 个固定情境及 77 份知识库资料。学生可以在模拟情境中提交方案、查看条件变化后的结果，并生成一份可核对的探索记录。

## 工作流与资源

| 组件 | 用途 |
| --- | --- |
| [在线体验工作流](kit/platform_import/WF_Explore_One_v4.yaml) | 管理大类、活动和情境选择，执行情境推演，生成探索记录，并按需检索知识库。 |
| [离线体验工作流](kit/platform_import/WF_Explore_One_v4_Offline.yaml) | 在未连接知识库的空间中运行体验流程。模型节点仍需绑定平台模型。 |
| [专业知识问答](kit/platform_import/WF_Major_Knowledge_v2.yaml)和[开放练习](kit/platform_import/WF_KB_Practice_Draft_v2.yaml) | 根据检索结果回答专业问题，或生成附来源的练习草稿。 |
| [Agent 提示词](kit/prompts/agent_system.md)和 [@ 引用版](kit/prompts/agent_system_at.md) | 定义意图判断、工作流调用和结果展示。 |
| [知识库原稿](kit/knowledge_base/)和[导入 ZIP](kit/knowledge_base_upload.zip) | 77 份 Markdown，另有 [39 条来源记录](kit/references/source_register.md)。 |
| [情境数据](kit/config/case_bank.json)、[引擎源码](kit/code/engine_source.py)和[平台适配](kit/code/platform_runtime.py) | 情境内容、确定性状态流转和代码节点调用入口。 |

## 主工作流参数

| 参数 | 必填 | 含义 |
| --- | --- | --- |
| `task_id` | 是 | 活动类型。学生未指定活动时传 `auto`。 |
| `reported_group_text` | 是 | 学生已明确的所属大类原文。未提供时传空字符串。 |
| `session_seed` | 否 | 控制题面变体和选项顺序。同一会话沿用同一种子。 |
| `exclude_case_ids` | 否 | 已体验的情境 ID，以逗号分隔。 |

工作流通过状态快照 `state_json` 在节点间传递当前情境、方案与阶段。Python 节点调用 `handler(params)`。选题节点加载题库，求解和报告节点从快照读取当前情境。整理记录前，工作流询问学生是否生成记录以及是否添加自己的想法。

## 部署

上传知识库 ZIP，按[部署说明](kit/platform_import/DEPLOY_v4.0.0.md)配置知识库和模型绑定，再导入所需工作流并挂载 Agent 提示词。在线 YAML 使用示例知识库标识，需要绑定到目标空间的资源。

## 本地验证

```sh
cd kit
python -m pip install -r requirements.txt
python -X utf8 maintenance/check_new_cases_v4.py
python -X utf8 maintenance/check_slim_equivalence.py
python -X utf8 tests/check_legacy.py --golden cases/golden_results.json
```

上述命令检查情境数据、工作流内嵌节点与本地运行时的一致性，以及数值快照。平台交互见 [NK-GeniOS 手工测试计划](kit/tests/manual_test_plan_v4.md)。
