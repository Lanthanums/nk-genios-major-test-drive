# v2.1 图构建器适配合同

供集成维护，不上传学生知识库。图模块为 `integration/graph_v21.py`，依赖父构建器 Flow 及现有知识库帮助函数。

## 统一输出

所有运行节点按 ENGINE_FIELDS 补齐字段：state_json、selection_json、action、ok(Boolean)、prompt、preview、feedback、display_text、normalizer_context、mode、choiceA/B/C、case1/2/3、result_json、knowledge_query、reflection_prompt、record_summary。其他旧字段可保留。所有字符串缺省为空；有状态响应恢复当前 mode、choice 原文、normalizer_context 和 reflection_prompt。

按钮选项分支不读取或解析 optionContent 来判断选择。图直接给确定常量。动态文本只用于展示和保存当时选择。真实截图只有optionId/optionContent，不能假定按钮节点提供USER_RESPONSE。按钮class_other统一友好结束并保留现有记录，不能将Others当成学生原话。只有自由回答信息节点读取USER_RESPONSE。

## 前置信息操作

| op | 输入 | 输出 |
|---|---|---|
| init_selection | task_id、reported_group_text 两个必填字符串 | selection_json；有唯一匹配的本人明确大类时 action=known_group，否则need_group。空大类不猜测；两个同名班仅班名不唯一 |
| set_group | selection_json、group_id 常量 | selection_json（本人按钮选择的大类或unknown）；无需年级经历 |
| prepare_cases | selection_json | 若方向未选返回 action=need_activity；否则action=menu并给case1/2/3、prompt、selection_json |
| set_activity | selection_json、task_id 常量 | 与prepare_cases明确方向结果相同，输出三个情境的通俗按钮文案；不重问大类 |
| select_case | selection_json、case_index整型0/1/2 | state_json，action=awaiting_plan，prompt/display_text题面、mode与当时choiceA/B/C |
| selection_finish | selection_json、user_text可空 | display_text：尚未开始的友好结束说明；class_other无关输入不猜大类/方向/情境，不产生计算事实 |

## 有状态操作

- `submit_button(state_json,choice,user_text)`：choice为A/B/C常量；user_text为当时按钮完整文字。与propose一样保存pending，仅返回awaiting_confirmation，不直接计算。
- `propose/confirm/hint/advance/report`：保留已有接口；相同字段合同，`report`只读恢复元数据，不中途展示report全文。`hint`仅提示；`confirm`只在按钮确定确认时计算。
- `reflect_auto_majors(state_json,user_text)`：自然结束优先；否则记录反思。没有新明确意向时保留已有requested_majors；不能因改感受删意向。record_summary用于简短记录核对摘要，而非完整report；包括本人感受独立引用、已做次数和需要核对的意向范围。
- `confirm_record(state_json,user_text)`：保留现有接口，明确确认才改变record_confirmed；普通自然结束返回现有未确认状态，不能把结束句当感受。
- `finish(state_json,finish_notice='')`：返回display_text为完整报告；尚未本人确认的草稿如实标记。已有completed/record_confirmed不得改回草稿。finish_notice是图的固定说明，可放在报告前；保留已确认方案计算，pending不算已做结果。

## 图的有界容错

单阶段最多一次自由修改并重新显示候选。“我想改一下”按钮进入自由回答节点，新的方案重新提取并再次展示，绝不直接计算。再次含糊时只保存既有记录，未确认新方案不计结果。所有按钮class_other采用友好结束，不从文字猜选项；不能读取未确认存在的按钮原文字段。所有停止/纠错耗尽经两个互斥退出汇聚，只有单End。

计算和报告数值只来自现有内核。题面、字段和来源的改变不得由检索结果或学生模板文字注入。
