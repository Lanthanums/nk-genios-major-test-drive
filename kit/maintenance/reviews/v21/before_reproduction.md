# v2.0 独立复现（修改前）

本地实际YAML代码、节点和模板重放。模型提取为显式夹具；不证明真实模型识别能力、在线平台报错根因或网页排版。

## 结论

- 长句退出缺少代码兜底。B/V提取若返回stop即可结束；若返回clarify就继续，不能把模型夹具视为线上模型结果。
- 确认节点中的长句退出进入重试；反思节点把长句当反思；记录确认节点要求重新确认。固定短语“结束体验”可退出且报告保留已有事实。
- 出错响应保留state_json，但report为空，图端若只拼接report会丢失可见报告。
- auto实际一次调用顺序是Group→Profile→27情境，Group一次。重复大类具体线上根因需工具调用/完整轨迹；再次调用确实总会重收。
- 原报告有换行与一个一级标题，但缺少统一层次、强调、注释；原文Markdown不转义。用户原文本身带{{USER_RESPONSE}}会原样显示；未发现该字面量被模板漏绑定。

## 逐案证据

### natural_stop_BAsk_clarify_fixture

长句退出未在代码兜底识别，进入确认及后续计算流程；此处后续答案为预置夹具。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BRetry → BRetryCompute → BRetryGate → BRetryError → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "clarify", "BCompute": "need_confirmation", "BRetryCompute": "need_confirmation"}`

### natural_stop_BAsk_stop_fixture

模型明确提取stop时能结束且含报告。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BStopBeforeConfirm → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "stopped"}`

### natural_stop_VAsk_clarify_fixture

长句退出未在代码兜底识别，进入确认及后续计算流程；此处后续答案为预置夹具。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VRetry → VRetryCompute → VRetryGate → VRetryError → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "clarify", "VCompute": "need_confirmation", "VRetryCompute": "need_confirmation"}`

### natural_stop_VAsk_stop_fixture

模型明确提取stop时能结束且含报告。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VStopBeforeConfirm → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "stopped"}`

### natural_stop_BConfirm

未识别退出，触发need_confirmation及一次重试。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BRetry → BRetryCompute → BRetryGate → BRetrySuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → XConfirmed → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "need_confirmation", "BRetryCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "completed"}`

### natural_stop_VConfirm

未识别退出，触发need_confirmation及一次重试。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VRetry → VRetryCompute → VRetryGate → VRetrySuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → XConfirmed → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "need_confirmation", "VRetryCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "completed"}`

### natural_stop_Reflection

被当成反思存入报告并继续问确认。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → XConfirmed → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "completed"}`

### natural_stop_RecordConfirm

未识别退出，触发need_record_confirmation及RecordRetry。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → RecordRetry → FinalizeRetry → XRecordRetry → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "need_record_confirmation", "FinalizeRetry": "completed"}`

### punctuation_multiline_markdown_literal_template

单次模板替换不会递归展开用户原文。用户主动写入的字面占位会原样显示；不是缺失绑定。原报告把本人原话置于独立行，但未转义Markdown或逐行引用。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → XConfirmed → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "completed"}`

### auto_entry

当前交付图入口Group→Profile→CaseSelect；一次调用Group只执行一次。截图/日志没有实际工具调用参数和完整节点运行轨迹，不能独立证明是哪次调用重复。主Agent接口只传task_id，任何再次调用均会重新收集。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → KBBridge → KBBridgeContext → BridgeLLM → BridgeCheck → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → XConfirmed → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "completed"}`

### exact_stop_BConfirm

固定短语可退出并有草稿报告，已计算事件仍保留。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BStop → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "stopped"}`

### exact_stop_VConfirm

固定短语可退出并有草稿报告，已计算事件仍保留。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VStop → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "stopped"}`

### exact_stop_Reflection

固定短语可退出并有草稿报告，已计算事件仍保留。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → XDraftStop → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "stopped"}`

### exact_stop_RecordConfirm

固定短语可退出并有草稿报告，已计算事件仍保留。

节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → XRecordStopped → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "stopped"}`

### baseline



节点：Start → Group → Profile → Menu → MenuGate → CaseSelect → StartCase → StartGate → BridgeMessage → BAsk → BExtract → BPropose → BProposeGate → BConfirm → BCompute → BGate → BSuccess → BSuccessMerge → BReady → BFeedback → Advance → AdvanceGate → ChangeFeedback → VAsk → VExtract → VPropose → VProposeGate → VConfirm → VCompute → VGate → VSuccess → VSuccessMerge → VReady → VFeedback → ReflectionQuestion → Reflection → Draft → DraftGate → RecordConfirm → Finalize → FinalGate → XConfirmed → FinalMerge → End

代码action：`{"Menu": "menu", "StartCase": "awaiting_plan", "BPropose": "awaiting_confirmation", "BCompute": "evaluated", "BReady": "report", "Advance": "awaiting_plan", "VPropose": "awaiting_confirmation", "VCompute": "evaluated", "VReady": "report", "Draft": "awaiting_record_confirmation", "Finalize": "completed"}`

完整入参、实际报告、阶段状态和节点模板见 before_reproduction.json。

未修改F盘正式包。未进行平台导入或在线模型测试。
