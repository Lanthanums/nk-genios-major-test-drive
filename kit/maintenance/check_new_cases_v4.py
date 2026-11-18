# -*- coding: utf-8 -*-
"""v4 新增情景自检脚本。

校验内容：
1. case_bank.json 可加载，case_version 为 2026-10-17.v4.0；
2. 共 14 个 family、42 个 case；5 个新 family 各恰好 3 个 case，mode 正确；
3. 旧 27 个 case 仍在（不改动旧字段由编辑方式保证，此处核对存在性）；
4. 所有新 case 的 related_majors 存在于 config/major_groups.json 的专业集合；
5. 每个新 case 的每个 surface_variant 展开后，context/phases/options/items/feedback
   中无残留占位符（{reason} 为引擎运行时替换，属允许项）；
6. story（choice）case 的 options 与 outcomes 两阶段均覆盖 A/B/C，
   且每条 feedback 以固定 disclaimer 结尾；
7. allocation case 的 budget 长度 2、min_step 整除 budget、max_per_item 合法；
8. rank case 的 item_ids 引用存在的卡片；data_overrides 与 budget 一致。

运行：python maintenance/check_new_cases_v4.py
退出码 0 = 全部通过；非 0 = 有错误。
"""
import copy
import json
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISCLAIMER = "这是一种倾向线索，不是能力判断，也不是专业匹配结论。"
ENGINE_KEYS = {"reason"}  # 引擎运行时替换的占位符，不算残留

NEW_FAMILIES = {
    "story": "choice",
    "values": "rank",
    "hearing": "allocation",
    "daylife": "allocation",
    "failure": "compose",
}
NEW_CASE_IDS = [
    "story_lab_deadline", "story_clinic_volunteer", "story_model_ethic",
    "values_research_day", "values_offer_letter", "values_team_role",
    "hearing_gpu_quota", "hearing_fund_review", "hearing_club_budget",
    "daylife_cell_lab", "daylife_quant", "daylife_chip",
    "failure_modeling", "failure_cells", "failure_defense",
]
OLD_CASE_IDS = [
    "route_campus", "route_coldchain", "route_relay",
    "sensor_luggage", "sensor_water", "sensor_artifact",
    "control_cart", "control_greenhouse", "control_storage",
    "experiment_growth", "experiment_catalyst", "experiment_fluorescence",
    "evidence_survey", "evidence_leakage", "evidence_quantum",
    "resource_energy", "resource_samples", "resource_bandwidth",
    "debug_boundary", "debug_calibration", "debug_packets",
    "materials_shell", "materials_adsorption", "materials_optics",
    "finance_promotion", "finance_fraud", "finance_publicdata",
]

errors = []


def err(msg):
    errors.append(msg)


def main():
    bank = json.loads((ROOT / "config" / "case_bank.json").read_text(encoding="utf-8"))
    groups = json.loads((ROOT / "config" / "major_groups.json").read_text(encoding="utf-8"))
    families, cases = bank["families"], bank["cases"]

    # 1. 版本
    if bank.get("case_version") != "2026-10-17.v4.0":
        err(f"case_version 错误: {bank.get('case_version')}")

    # 2. 数量与家族结构
    if len(families) != 14:
        err(f"family 数量 {len(families)} != 14")
    if len(cases) != 42:
        err(f"case 数量 {len(cases)} != 42")
    for fam, mode in NEW_FAMILIES.items():
        if fam not in families:
            err(f"缺少 family: {fam}")
            continue
        if families[fam].get("mode") != mode:
            err(f"family {fam} mode 应为 {mode}，实为 {families[fam].get('mode')}")
        member = [c["case_id"] for c in cases.values() if c.get("task_id") == fam]
        if len(member) != 3:
            err(f"family {fam} 有 {len(member)} 个 case（应为 3）: {member}")

    # 3. 旧 case 存在性
    for cid in OLD_CASE_IDS:
        if cid not in cases:
            err(f"旧 case 丢失: {cid}")

    # 4. related_majors 合法性（对全部 42 个 case 检查）
    major_set = {m for g in groups["groups"].values() for m in g["majors"]}
    for cid, c in cases.items():
        for m in c.get("related_majors", []):
            if m not in major_set:
                err(f"{cid}: related_majors 含未知专业 '{m}'")

    # 5-8. 新 case 逐个校验
    fmt = string.Formatter()

    def texts_of(case):
        ts = [case["context"]] + list(case["phases"])
        d = case["data"]
        mode = NEW_FAMILIES[case["task_id"]]
        if mode == "choice":
            for stage in d["options"]:
                ts.extend(stage.values())
            for stage in d["outcomes"]:
                for o in stage.values():
                    ts.append(o["feedback"])
            ts.extend(d.get("evidence", []))
        elif mode in ("rank", "allocation"):
            ts.extend(it["text"] for it in d["items"])
        elif mode == "compose":
            ts.extend(d["writing"])
            ts.append(d["title_prompt"])
        return ts

    for cid in NEW_CASE_IDS:
        if cid not in cases:
            err(f"新 case 缺失: {cid}")
            continue
        c = cases[cid]
        mode = NEW_FAMILIES[c["task_id"]]
        variants = c.get("surface_variants", [])
        if len(variants) < 2:
            err(f"{cid}: surface_variants 少于 2 个")

        for i, v in enumerate(variants):
            surface = dict(v.get("surface", {}))
            cc = copy.deepcopy(c)
            overrides = v.get("data_overrides", {})
            cc["data"].update(overrides)  # 浅合并，与引擎一致
            item_ids = v.get("item_ids")

            # item_ids 引用存在
            if item_ids is not None:
                known = {it["id"] for it in cc["data"]["items"]}
                for it in item_ids:
                    if it not in known:
                        err(f"{cid} 变体{i}: item_ids 引用未知卡片 '{it}'")

            # 占位符：全部可由 surface 或引擎键提供；展开后无残留
            for t in texts_of(cc):
                fields = [f for _, f, _, _ in fmt.parse(t) if f is not None]
                for f in fields:
                    if f not in surface and f not in ENGINE_KEYS:
                        err(f"{cid} 变体{i}: 占位符 {{{f}}} 未由 surface 提供")
                mapping = {**{k: "" for k in ENGINE_KEYS}, **surface}
                try:
                    rendered = fmt.vformat(t, (), mapping)
                except KeyError as e:
                    err(f"{cid} 变体{i}: 展开失败 KeyError {e}")
                    continue
                if "{" in rendered or "}" in rendered:
                    err(f"{cid} 变体{i}: 展开后仍残留花括号: {rendered[:60]}...")

            # data_overrides 与 surface 数字一致性（若有 budget 覆盖）
            if "budget" in overrides and "budget0" in surface:
                if str(overrides["budget"][0]) != surface["budget0"]:
                    err(f"{cid} 变体{i}: data_overrides.budget 与 surface.budget0 不一致")

        # 6. story(choice) 结构
        if mode == "choice":
            d = c["data"]
            for s in range(2):
                if set(d["options"][s].keys()) != {"A", "B", "C"}:
                    err(f"{cid}: options[{s}] 未覆盖 A/B/C")
                if set(d["outcomes"][s].keys()) != {"A", "B", "C"}:
                    err(f"{cid}: outcomes[{s}] 未覆盖 A/B/C")
                for k, o in d["outcomes"][s].items():
                    if DISCLAIMER not in o.get("feedback", ""):
                        err(f"{cid}: outcomes[{s}][{k}] feedback 缺少固定 disclaimer")

        # 7. allocation 数值
        if mode == "allocation":
            d = c["data"]
            budgets = [tuple(v.get("data_overrides", {}).get("budget", d["budget"]))
                       for v in variants] or [tuple(d["budget"])]
            for b in budgets:
                if len(b) != 2:
                    err(f"{cid}: budget 长度 {len(b)} != 2")
                step = d["min_step"]
                for x in b:
                    if x % step != 0:
                        err(f"{cid}: budget {x} 不能被 min_step {step} 整除")
                cap = d.get("max_per_item")
                if cap is not None:
                    if cap % step != 0:
                        err(f"{cid}: max_per_item {cap} 不能被 min_step {step} 整除")
                    for x in b:
                        if cap > x:
                            err(f"{cid}: max_per_item {cap} 超过 budget {x}")
            if len(d["items"]) < 5:
                err(f"{cid}: allocation items 少于 5 项")

        # 8. rank 卡片数量
        if mode == "rank":
            n = len(c["data"]["items"])
            if not (6 <= n <= 8):
                err(f"{cid}: rank 卡片数 {n} 不在 6-8")

        # compose 结构
        if mode == "compose":
            d = c["data"]
            if len(d.get("writing", [])) != 2:
                err(f"{cid}: compose writing 应为 2 段")
            if "title_prompt" not in d or "max_chars" not in d:
                err(f"{cid}: compose 缺 title_prompt 或 max_chars")

    # 输出
    if errors:
        print(f"FAILED: {len(errors)} 个问题")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: case_bank.json 加载成功")
    print(f"OK: 14 families / 42 cases；5 个新 family 各 3 个 case")
    print(f"OK: 旧 27 case 全部在位；42 个 case 的 related_majors 均合法")
    print(f"OK: 15 个新 case 的全部 surface_variants 展开无残留占位符")
    print(f"OK: story 三案 options/outcomes 两阶段均覆盖 A/B/C 且 disclaimer 齐备")
    print(f"OK: allocation 数值规则、rank 卡片数、compose 结构均通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
