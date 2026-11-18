# Runtime v2.1 interface

`engine_source.py` is the editable source. Run `python build_standalone.py` to embed the adjacent case bank and major directory into `standalone_runtime.py`. Only the Python standard library is used. The numeric `evaluate` function and reviewed case outcomes are unchanged from v2.0.

## Compatible calls and new finish call

Existing `start`, `propose`, `confirm`, `advance`, `reflect`, `confirm_record`, `report`, `stop`, `hint`, `scope`, `catalog` operations remain available.

To end from any stage with a valid state:

```json
{"op":"finish","state_json":"<current state>","user_text":"结束并给我报告"}
```

This returns `ok=true`, `action=stopped`, an updated `state_json`, and a nonempty Markdown `report`. It does not require an evaluated second proposal, reflection, or whole-record confirmation. Confirmed calculations remain unchanged. A proposed but unconfirmed plan is preserved under `unfinished_plan` and identified as unconfirmed, with no result invented. An unconfirmed reflection remains unconfirmed. Repeated finish calls do not duplicate events or change facts.

All operations with a valid state check clear natural-language finish intent before their normal stage checks. These include “结束并给我报告”, “不想继续了，生成报告”, and “做完两次了想结束”. Negative requests, quoted examples, hypothetical questions, and mentions of an “结束按钮” do not automatically end an activity. This local parser is deliberately conservative; a displayed Finish button should invoke `op=finish` directly, rather than depend on text classification. A model candidate's stop action alone cannot terminate a session without a matching raw student request.

## Display fields

`display_text` is the complete user-facing Markdown for a dispatch response. When a report is present, it contains the report followed by any necessary confirmation instruction, without duplicating the report. Otherwise it combines the stage guide, question, preview, and feedback in order.

The older `prompt`, `preview`, `feedback`, and `report` fields remain separate for workflows that show them at separate moments. Display either `display_text` **or** the chosen component fields, avoiding repeated text.

Do not display `state_json`, `normalizer_context`, `result_json`, `error`, `action`, or the internal IDs as student-facing content. These remain machine-readable values. On failure, `feedback` and `display_text` contain a friendly recovery message; if the input state is valid, the last valid report is also returned. `error` remains diagnostic only.

Raw student text is stored unchanged in event `raw_text` / `proposal_raw` and in `reflection_raw`. Rendered reports and reason previews put it on a separate blockquote line, escape Markdown/HTML formatting, and append no punctuation to the quotation. Thus text ending in a full stop, containing multiple lines, or containing Markdown syntax does not break the report layout. The raw stored text is not escaped or silently rewritten.

## Reflection and confirmation

`reflect` accepts uncertain or skipped reflection replies without inventing interest. The raw reply is retained in the `reflection_skipped` event; the report states that reflection was skipped. A natural-language change given to `confirm_record` replaces the reflection as an unconfirmed draft and asks the student to check it again. Only an explicit confirmation or the existing “更正并确认：…” command marks the record confirmed.

Friendly confirmation button text `按这个方案试一试` is accepted by `confirm`. A different plan is shown again before calculation. The existing explicit “试算 …” shortcut remains compatible but is no longer required in user-facing instructions.

## Verification boundary

Run `python test_runtime.py`. The tests replay all 27 cases through eight valid lifecycle states, then end each through seven entry operations; check quoted text, repeat finish, negative intent, model-invented stop prevention, failure recovery, natural reflection revision, and all nine legacy numerical snapshots. This is local runtime verification. It does not prove platform YAML import, information-collection suspension/resumption, button rendering, or model extraction quality.
