# 在 NK-GeniOS 部署专业试驾场 v4.0.0

## 知识库和工作流

1. 在目标空间上传 [knowledge_base_upload.zip](../knowledge_base_upload.zip)。ZIP 内含 77 份 Markdown。来源登记见 [source_register.md](../references/source_register.md)。
2. 在线主工作流及两个知识工作流中，使用目标知识库的实际标识替换公开 YAML 内的占位值。将 `00000000-0000-4000-8000-000000000001` 替换为目标知识库 ID，将 `personal-00000000000000000000` 替换为其所属空间 ID。知识库 ID 同时出现在依赖表和检索节点中，需全文件替换。可以从目标空间的知识库检索工作流导出 YAML，查看 `Depends.KnowledgeMap` 中的 `ID` 和 `ResourceWorkspaceID`。
3. 导入 [在线主工作流](WF_Explore_One_v4.yaml)。不使用知识库时导入 [离线主工作流](WF_Explore_One_v4_Offline.yaml)。如平台提示模型资源无法映射，在目标空间选择可用模型，并在编辑器中检查各模型节点的绑定。
4. 按需导入 [专业知识问答](WF_Major_Knowledge_v2.yaml)和[开放练习草稿](WF_KB_Practice_Draft_v2.yaml)。
5. 挂载工作流并配置 [Agent 提示词](../prompts/agent_system.md)或 [@ 引用版](../prompts/agent_system_at.md)。提示词通过 `WF_Explore_One_v4` 调用主体验工作流。使用离线版时，将该工具引用指向离线工作流。

## 验收

[手工测试计划](../tests/manual_test_plan_v4.md)覆盖大类识别、按钮交互、自然语言方案提取、暂停后继续、报告核对与知识库检索。使用目标空间确认可选参数 `session_seed`、`exclude_case_ids` 留空时的行为。
