# v2 独立工程检查

检查日期：2026-10-17。阶段：4份实际生成YAML独立结构检查与46条夹具重放。本报告只记录实际读到的文件与实际执行的检查，不代表平台导入或多轮挂起实测。

## 已读范围

- `integration/platform_support.py`：检索结果整形、问答引用检查、开放练习草稿检查。
- `runtime/interface.md`：引擎输入输出与状态约束。
- 旧版 `platform_import/build_importable_workflow.py`：原生节点配置、依赖、变量绑定、占位提取与单End。
- `integration/build_knowledge.py`：源数据整合与知识卡生成。
- `F:\华为杯\知识库调用实例-20261017-020328.yaml`：后补示例已实际找到并读完。

## 初审发现

### 需要修正或后续验证

1. **已修复并回归：问答缺项说明绕过URL出处检查。** 原先 `validate_answer`只扫描 `answer` 内URL，`missing`中的虚构链接可透传。现对两字段同时扫描，本地伪链接被拒。
2. **已修复并回归：检索score非有限数异常。** 原先 `metadata.score=NaN`导致未捕获异常。现先检查有限数字，异常分数设空，本地已复测不抛出。
3. **已修复并核查交付卡片：知识来源无日期导致登记表生成异常。** 登记表与专业卡均显示“未标明”，33张专业卡均未发现 `日期：None/null`。
4. **已修复并核查交付卡片：特色班边界字符串逐字拆分。** 现对字符串先包装为单项列表再追加边界；33张卡的边界段均未发现单字符列表项。
5. **已修复并在实际YAML回归：开放题草稿真实URL被误拒。** 原来整体JSON匹配会把后续引号拼入URL；正则已明确排除引号和反斜线。实际 `WF_KB_Practice_Draft_v2.yaml`代码节点接受命中正文与metadata中存在的URL，`DraftCheck.ok=true`。
6. **已修复并核查实际平台运行模块：排除案例与事务性。** 原先默认route提前返回绕过排除，反思失败前已mutation。最终 `package/code/platform_runtime.py` 实测排除默认案例后选到其他route案例；反思输入错误majors类型时返回失败且state与调用前完全相同。

## Knowledge示例语法核对

真实示例位于 `F:\华为杯\知识库调用实例-20261017-020328.yaml`，不是会话attachments。已读到：

- 原生类型 `Type: Knowledge`，配置为 `Configs.Knowledge`、`ConfigVersion: 2`。
- `QueryVariable`为单对象，引用上游节点输出，不是 `InputVariables`数组。
- `DatasetParamsVariable`为数组，其项 `Name: dataset_params[0].dataset_id`，`JsonValue`是JSON字符串字面量。
- `KnowledgeRange`、`DatabaseInfos[].ID`、`Depends.KnowledgeMap`和上述参数使用同一知识库ID。
- 输出 `outputList`为数组Type9，每项有 `output`字符串和 `metadata`对象Type4；metadata含document_name、可选document_url、dataset_id、segment_id、score等。辅助代码按此读取结构相符。
- 示例End只写Name/RefType，没有NodeCode/Path，是尚未接好的输出；生成器不能照抄该空绑定。
- 原知识库ID是租户资源绑定。保留它可方便同租户使用，但上传新Markdown和跨工作区重绑仍属平台动作，不能假定导入YAML即自动上传本地资料。

## 辅助函数实际回归

当前12项已全部通过：有效引用问答、缺项/正文伪URL拒绝、伪引用片段拒绝、引用URL不匹配拒绝、空检索显式降级、NaN分数安全处理、字符串化hits支持、损坏hits降级、有效练习草稿、伪草稿引用拒绝及命中真实URL接受。最后一项已在实际YAML中再次调用确认。这些检查只覆盖结构与出处约束，不是语义正确性测试。

### 已确认的合理边界

- 问答的引文要求命中正文中6至100字连续片段，并核对该片段所属记录里的URL。缺检索时明确不补编。
- 开放练习草稿要求固定字段、A/B/C选项、1至3条原文依据；明确只做结构/来源片段检查，不声称学科答案已审定。
- 开放练习不自动写入固定题库、不参与客观反馈、不产生专业适配分数。固定引擎结果与检索解释应保持这种权限区分。
- 引文存在不能证明整份回答或题目正确；应在文档和测试里保留这一限制，不把结构通过称为事实核验通过。
- 原生多轮信息收集必须保留平台必填ExtractSchema占位，下游读 `USER_RESPONSE`。原文不能被无关提取字段代替。
- 原生单End之前应只聚合互斥终态输出。已执行上游空字符串不能进入同一聚合竞争最终回答。

## 新工作流生成后必须核对

1. 所有节点Code/ID、依赖NodeCode、分支PortID均存在，图无环，Start到End有路且唯一End。
2. 每条输入变量绑定、模板变量和 `{{模板占位}}` 对应；Path必须属于来源节点输出schema。特别检查Knowledge的 `outputList` 是否真实绑定，不写成LLM的 `raw_output`。
3. 选择器应核对 `ok` 与具体 `action`，不能只靠成功布尔值把hint/clarify/stop误接进计算或advance。
4. 原方案、条件变化后方案、本人确认原文、反思原文分别指向当前阶段的信息收集节点；状态始终来自上一步代码，不从模型重写。
5. 因平台编排为有界重试，次数用尽应保存已完成事实并给出可恢复说明，不能因含糊输入静默当作确认或丢失草稿。
6. Knowledge结果只支持解释与开放草稿，不更换在途case_id、题面条件、选项和引擎结果。
7. 检索示例的真实dataset标识若不可移植，需要清楚标注导入后必须重新绑定；不能使用伪标识宣称导入即能检索本地Markdown。
8. 新case_id和多样家族菜单必须有实际接口接线，避免只有文案增加、运行仍固定三题。

## 实际YAML独立检查结果

独立脚本 `review/check_native_independent.py`直接加载4份交付YAML，不导入builder或原先verify脚本；结果见 `review/native_independent_results.json`。

|文件|节点|代码节点|独立结构检查|
|---|---:|---:|---|
|WF_Explore_One_v2.yaml|74|38|单Start/End、ID唯一、引用均在上游、输出字段存在、Knowledge与示例结构一致|
|WF_Explore_One_v2_Offline.yaml|70|36|单Start/End、ID唯一、引用均在上游、输出字段存在|
|WF_Major_Knowledge_v2.yaml|6|2|单End、query绑定、outputList读取及来源检查链完整|
|WF_KB_Practice_Draft_v2.yaml|6|2|单End、query绑定、outputList读取及草稿检查链完整|

重放46种场景，包括两个Explore版本的正常完成、基础/修改/更正环节退出、一次更正成功/失败、模型JSON损坏后显式更正、大类不明和跨家族情境选择失败、暂不确认记录、记录二次确认、空检索，以及两份知识工作流的命中/不命中。所有重放均到达唯一End；每次VariableMerge只出现一个已执行候选，无上游空反馈竞争。

所有实际执行Code节点均核对声明字段和类型。两个正常输入不易触发的 `XAdvanceError/XDraftError` 已另以直接调用验证终态输出schema完整。模型提取与检索为显式夹具，不构成在线模型准确性或检索召回率证据。

**已修复并复跑的报告阶段退出问题：**

- 两份Explore现均增加 `DraftGate.if02 → XDraftStop`：反思回复“结束体验”直接结束，不再进入RecordConfirm。
- 两份Explore现均增加 `FinalGate.if03 → XRecordStopped`：记录确认回复“结束体验”直接结束，不再进入RecordRetry。
- Stop终态同时返回结束反馈与未确认报告，不把草稿标成确认。最终重跑46条夹具路径，`known_failures=[]`。

## 知识卡与引用登记最终核查

直接读取 `package/config/major_profiles.json`、33张 `10_major_*.md`、`references/source_register.json/md` 及全部知识卡的引用ID：33条专业记录与33张专业卡对应；36条来源记录ID完整；专业记录引用和知识卡中出现的来源ID均能在登记表找到。

新增3条计量概念来源 `CONCEPT-NIM-AUDIT`、`CONCEPT-NIM-REFERENCE`、`CONCEPT-NIM-MATERIAL-COMPARISON` 均已登记并由相应方法卡引用。来源注明读取状态、历史材料范围与不能支持的结论，不称合成题的数据为这些来源中的真实实测数据。

抽读普通专业与特色班卡，包括“智能医学工程（脑机接口特色班）”“智能科学与技术（具身与行为智能特色班）”，示例标记、边界段落和来源日期现正常；基础专业通识不再被误写为特色班已核验课表。自动检查覆盖全部33卡，无None日期或逐字符limits残留。

## 当前检查结论

最终交付的4份实际YAML通过独立结构、引用、Knowledge规范、代码输出字段与46条夹具路径检查，本轮发现的问题均已修复并复核。33专业卡、36来源及引用关联检查通过，未发现仍阻塞本地交付的工程问题。平台实际导入、多轮挂起、真实知识库命中与模型行为仍未实测；结构通过不构成学科语义、测评效度或线上体验保证。
