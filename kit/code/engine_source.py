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
BANK = {}  # Standalone builder embeds case_bank.json here.
CATALOG = {}  # Standalone builder embeds user-provided major_groups.json here.
CASE_VERSION = ""  # Builder embeds case_bank.json case_version; works without full BANK.
FAMILY_NAMES = {}  # Builder embeds {family_id: display name}; works without full BANK.
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
