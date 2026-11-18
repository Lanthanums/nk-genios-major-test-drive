"""Native DLVersion-v2 workflows assembled only from supplied tenant node schemas. v4."""
from pathlib import Path
import base64
import copy
import hashlib
import importlib.util
import json
import re
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]

for parent in ROOT.parents:
    sys.path.insert(0, str(parent / '.workflow_deps'))
import yaml

PKG = ROOT
BASE = yaml.safe_load((PKG/'maintenance/templates/workflow_schema_template.yaml').read_text(encoding='utf-8'))
KB_SAMPLE = yaml.safe_load((PKG/'maintenance/templates/knowledge_example.yaml').read_text(encoding='utf-8'))
BUTTON_SAMPLE = yaml.safe_load((PKG/'maintenance/templates/button_example.yaml').read_text(encoding='utf-8'))
TEMPLATES = {}
for node in BASE['Nodes'] + KB_SAMPLE['Nodes']:
    TEMPLATES.setdefault(node['Type'], node)
SUPPORT = (PKG / 'code/platform_support.py').read_text(encoding='utf-8')
ENGINE = (PKG / 'code/engine.py').read_text(encoding='utf-8')
bank_bytes = (PKG / 'config/case_bank.json').read_bytes()
packed_bank = base64.b85encode(zlib.compress(bank_bytes,9)).decode('ascii')
ENGINE = re.sub(r'^BANK = .+$',lambda match:'import base64 as _bank_b64, zlib as _bank_zlib\nBANK = json.loads(_bank_zlib.decompress(_bank_b64.b85decode('+repr(packed_bank)+')).decode("utf-8"))',ENGINE,count=1,flags=re.MULTILINE)
bank_meta = json.loads(bank_bytes.decode('utf-8'))
ENGINE = re.sub(r'^CASE_VERSION = .*$','CASE_VERSION = '+repr(bank_meta['case_version']),ENGINE,count=1,flags=re.MULTILINE)
ENGINE = re.sub(r'^FAMILY_NAMES = .*$','FAMILY_NAMES = '+repr({k:v['name'] for k,v in bank_meta['families'].items()}),ENGINE,count=1,flags=re.MULTILINE)
# Lean flavor: case data travels inside state snapshots, so in-conversation
# nodes do not embed the bank at all (platform YAML stays under the 2 MiB cap).
_marker = 'import base64 as _bank_b64, zlib as _bank_zlib'
_head, _sep, _rest = ENGINE.partition(_marker)
assert _sep, 'bank embed marker missing'
ENGINE_LEAN = _head + 'BANK = {"cases":{},"families":{},"case_version":'+repr(bank_meta['case_version'])+'}\n' + _rest.split('\n',2)[2]
assert len(ENGINE_LEAN) < len(ENGINE) - len(packed_bank)//2
PROFILES = json.loads((PKG / 'config/major_profiles.json').read_text(encoding='utf-8'))

_spec = importlib.util.spec_from_file_location('engine_meta', PKG/'code/engine.py')
ENGINE_META = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ENGINE_META)
GROUP_FAMILIES = ENGINE_META.GROUP_FAMILIES
DEFAULT_MENU_FAMILIES = ENGINE_META.DEFAULT_MENU_FAMILIES

FAMILY_LABELS = {
    'route':'安排一条合适的路线', 'sensor':'让设备少一些误报和漏报', 'control':'让运动或温度更稳一点',
    'experiment':'设计一次公平的对比实验', 'evidence':'看看一份数据能说明什么', 'resource':'资源有限时怎样分配',
    'debug':'找出一个系统为什么出了错', 'materials':'比较材料性能和使用条件', 'finance':'分析一次经济选择和它的证据',
    'story':'走进一个两难的现场，看你会怎么做', 'values':'给在乎的东西排个序', 'hearing':'主持一次分资源的听证',
    'daylife':'拼出某个职业真实的一天', 'failure':'把一次搞砸的经历讲出来'}

ADAPTER = '''
_core_handler = handler
MAJOR_NAMES = __MAJOR_NAMES__

def _explicit_majors(raw):
    # Intent is captured only in an explicit optional line, never inferred from
    # a mention such as "不想学计算机科学与技术" in the reflection.
    match = re.search(r'(?:^|\\n)\\s*想了解[:：]([^\\n]+)', raw)
    if not match:
        return []
    values = [x.strip().strip('。') for x in re.split(r'[,，、;；]+',match.group(1)) if x.strip()]
    if len(values)>30 or any(len(x)>100 for x in values):
        raise ValueError('想了解的专业请填最多30个完整名称')
    return list(dict.fromkeys(values))

def handler(params):
    try:
        params = copy.deepcopy(params)
        op = params.get('op')
        if op == 'reflect_auto_majors':
            params['op']='reflect'
            params['majors']=_explicit_majors(params.get('user_text',''))
        elif op == 'confirm_record':
            raw = params.get('user_text','')
            if raw.startswith('更正并确认：') or raw.startswith('更正并确认:'):
                state = loads(params['state_json'])
                state['requested_majors'] = _explicit_majors(re.split('[:：]',raw,maxsplit=1)[1])
                params['state_json'] = dumps(state)
        return _core_handler(params)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError) as error:
        return {'ok':False,'action':'error','state_json':params.get('state_json','') if isinstance(params,dict) else '',
                'prompt':'','preview':'','feedback':str(error),'result_json':'','report':'','error':str(error)}
'''.replace('__MAJOR_NAMES__', repr([p['major'] for p in PROFILES['profiles']]))

APPENDED = '''
"""Appended to the embedded engine. All menu selections arrive as branch constants."""
_legacy_platform_handler = handler

SELECTION_VERSION = '4.0.0'

SELECTION_ROADMAP = "**这次会怎么进行**\\n\\n先选一个小情境，试试你的做法；如果愿意，再看看条件改变后会怎样。最后由你决定是否整理一份可核对的探索记录——整理前我会明确问你，并给你留想法的入口。\\n\\n*不用做满全程。你可以随时结束；不会把活动当成能力或专业适配测评。*"


def _reported_group(raw):
    text = clean_text(raw, 600).strip().rstrip("。！! ")
    if not text:
        return None
    if text in {"不清楚", "不知道", "暂不提供", "还没确定"}:
        return "unknown"
    aliases = {}
    for gid, group in CATALOG['groups'].items():
        values = [group['display_name']]
        if not gid.startswith('boqin_'):
            values.append(group['name'])
        else:
            direction = '信息' if gid == 'boqin_info' else '理科'
            values.extend(['卓越拔尖计划伯芩班（'+direction+'方向）', '伯芩班（'+direction+'方向）', '伯芩班'+direction+'方向'])
        for name in values:
            aliases[name] = gid
            aliases[name.replace('伯芩', '伯苓')] = gid
    if text in aliases:
        return aliases[text]
    matches = set()
    # Read explicit membership clauses; an additional interest clause must not
    # invalidate an otherwise clear self-report or trigger another class question.
    for clause in re.split(r'[。！!？?；;，,\\n]+',text):
        clause=clause.strip()
        if not clause or re.search(r"想去|想选|想学|希望|不是|不在|不属于|不确定|可能|如果|假如|[“”‘’\\"]",clause):
            continue
        if clause in aliases:
            matches.add(aliases[clause])
        for alias, gid in sorted(aliases.items(), key=lambda pair: -len(pair[0])):
            pattern = r"(?:我(?:现在|目前)?(?:是|在|属于|就读于)|我(?:现在|目前)?的(?:专业)?(?:当前|所属)?大类是|目前(?:是|在|属于))\\s*" + re.escape(alias) + r"(?:大类)?(?:的(?:学生)?|学生)?"
            if re.fullmatch(pattern,clause):
                matches.add(gid)
    return next(iter(matches)) if len(matches)==1 else None


def _selection(params):
    selection = loads(params.get('selection_json', ''))
    if selection.get('version') != SELECTION_VERSION:
        raise ValueError('selection version mismatch')
    if selection.get('group_id') not in set(CATALOG['groups']) | {'unknown'}:
        raise ValueError('unknown group')
    return selection


def _families_for(group_id):
    if group_id in GROUP_FAMILIES:
        return list(GROUP_FAMILIES[group_id])
    return list(DEFAULT_MENU_FAMILIES)


def _relevance_rank(case, group_id):
    if group_id in (None, 'unknown') or group_id not in CATALOG['groups']:
        return 1
    own = set(CATALOG['groups'][group_id].get('majors', []))
    return 0 if (own & set(case.get('related_majors', []))) else 1


def _menu_result(selection):
    task = selection['task_id']
    if task == 'auto':
        selection['families_shown'] = _families_for(selection['group_id'])
        return dict(ok=True, action='need_activity', group_id=selection['group_id'], selection_json=dumps(selection),
                    prompt="## 想从哪种小问题开始？\\n\\n选择一项你愿意动手想一想的事情。不需要有基础，也不用把它当成选专业的决定。")
    if task not in BANK['families']:
        raise ValueError('unknown activity')
    cases = [case for case in BANK['cases'].values() if case['task_id'] == task]
    if len(cases) != 3:
        raise ValueError('case count must be three')
    cases = sorted(cases, key=lambda c: _relevance_rank(c, selection['group_id']))
    selection['case_ids'] = [case['case_id'] for case in cases]
    related = sum(1 for case in cases if _relevance_rank(case, selection['group_id']) == 0)
    if selection['group_id'] == 'unknown':
        note = ""
    elif related:
        note = "前 %d 个与你的大类直接相关。" % related
    else:
        note = "这三个情境离你的大类稍远，可以当作跨界了解。"
    return dict(ok=True, action='menu', group_id=selection['group_id'], selection_json=dumps(selection),
                prompt="## 选一个更想试试的情境\\n\\n这三个情境练习同一类方法，但问题和条件不同。点一个你更想了解的就好，也可以让系统替你随机挑一个。" + note + "\\n\\n*题目使用编写的教学数据，每次打开细节可能略有不同；不是真实校内考题。*",
                **{'case'+str(index+1):case['title'] for index,case in enumerate(cases)})


def _roll_seed(selection, extra):
    base = selection.get('session_seed') or selection.get('group_id', 'unknown')
    return '|'.join([str(base), str(extra), str(selection.get('rolls', 0))])


def _selection_finish(params):
    selection = _selection(params)
    group = CATALOG['groups'].get(selection['group_id'], {}).get('display_name', '尚未提供')
    text = "# 本次探索记录\\n\\n**所属大类：** " + markdown_text(group) + "\\n\\n这次先到这里。还没有开始具体情境，也没有确认或试算方案，因此没有计算结果。\\n\\n*没有根据选择或退出推断你的能力、兴趣或专业适合程度。下次想体验时，可以重新开始。*"
    return dict(ok=True, action='stopped', selection_json=dumps(selection), report=text, display_text=text)


def _record_summary(state):
    case = case_of(state)
    count = sum(event.get('kind') == 'evaluated' for event in state['events'])
    parts = ["## 最后，核对一下想留下的记录", "**体验内容：** " + case['title'],
             "你已经确认并试过 **" + str(count) + " 个方案**。结果会原样放进最终记录。"]
    if state.get('reflection_raw'):
        parts += ["你对体验的感受：\\n\\n" + quoted(state['reflection_raw'])]
    else:
        parts += ["你暂时没有填写感受，这部分会如实留空。"]
    if state.get('requested_majors'):
        scope = scope_majors(state['group_id'], state['group_confirmed'], state['requested_majors'])
        for field, label in [('within_group','按你提供的大类清单属于类内'), ('cross_group','跨大类兴趣，转入资格尚未核验'), ('unverified','范围尚待核验')]:
            if scope[field]:
                parts.append('**'+label+'：** '+'、'.join(markdown_text(x) for x in scope[field]))
    parts += ["感受准确的话，选择‘记录准确，完成体验’；也可以改一下，或先不确认、保留这份记录。"]
    return '\\n\\n'.join(parts)


def _v4_dispatch(params):
    params = copy.deepcopy(params)
    op = params.get('op')
    if op == 'init_selection':
        raw = params.get('reported_group_text', '')
        gid = _reported_group(raw)
        task = ALIASES.get(params.get('task_id'), params.get('task_id')) or 'auto'
        if task not in set(BANK['families']) | {'auto'}:
            task = 'auto'
        seed_text = clean_text(params.get('session_seed', '') or '', 80)
        excluded_raw = clean_text(params.get('exclude_case_ids', '') or '', 2000)
        excluded = [x.strip() for x in re.split(r'[,，;；\\s]+', excluded_raw) if x.strip() in BANK['cases']][:40]
        selection = dict(version=SELECTION_VERSION, task_id=task, group_id=gid or 'unknown',
                         group_confirmed=gid not in (None, 'unknown'), group_raw=raw if gid is not None else '',
                         session_seed=seed_text, exclude_case_ids=excluded, rolls=0)
        if gid is not None:
            group = CATALOG['groups'].get(gid, {}).get('display_name', '尚未确定')
            intro = SELECTION_ROADMAP + '\\n\\n**这次使用的大类信息：** ' + markdown_text(group) + '。'
        else:
            intro = SELECTION_ROADMAP
        return dict(ok=True, action='known_group' if gid is not None else 'need_group',
                    selection_json=dumps(selection), prompt=intro, display_text=intro)
    if op == 'set_group':
        selection = _selection(params)
        gid = params.get('group_id')
        if gid not in set(CATALOG['groups']) | {'unknown'}:
            raise ValueError('unknown group')
        selection.update(group_id=gid, group_confirmed=gid != 'unknown', group_raw=CATALOG['groups'].get(gid,{}).get('display_name','暂不提供'))
        return dict(ok=True, action='known_group', selection_json=dumps(selection))
    if op in ('selection_finish', 'selection_other'):
        return _selection_finish(params)
    if op in ('prepare_cases', 'set_activity'):
        selection = _selection(params)
        if op == 'set_activity':
            task = params.get('task_id')
            if task == 'random':
                families = _families_for(selection['group_id'])
                families = [f for f in families if any(c['case_id'] not in selection.get('exclude_case_ids', []) for c in BANK['cases'].values() if c['task_id'] == f)] or families
                roll = int(hashlib.sha256(_roll_seed(selection, 'activity').encode('utf-8')).hexdigest(), 16)
                task = families[roll % len(families)]
                selection['rolls'] = selection.get('rolls', 0) + 1
            if task not in BANK['families']:
                raise ValueError('unknown activity')
            selection['task_id'] = task
        return _menu_result(selection)
    if op == 'select_case' and 'case_index' in params:
        selection = _selection(params)
        index = params['case_index']
        if type(index) is not int or index not in (-1, 0, 1, 2):
            raise ValueError('invalid case branch')
        ids = selection['case_ids']
        if index == -1:
            roll = int(hashlib.sha256(_roll_seed(selection, 'case').encode('utf-8')).hexdigest(), 16)
            index = roll % len(ids)
            selection['rolls'] = selection.get('rolls', 0) + 1
        result = _core_handler(dict(op='start', task_id=selection['task_id'], case_id=ids[index],
                                    group_id=selection['group_id'], group_confirmed=selection['group_confirmed'],
                                    cohort='未提供', seed=_roll_seed(selection, ids[index]),
                                    exclude_case_ids=selection.get('exclude_case_ids', [])))
        if result['ok']:
            state = loads(result['state_json'])
            state['group_raw'] = selection.get('group_raw', '')
            state['group_source'] = 'user_self_report_not_officially_verified'
            result['state_json'] = dumps(state)
        return result
    if op == 'submit_button':
        state = loads(params['state_json'])
        case = case_of(state)
        choice = params.get('choice')
        if _mode_of(case, state) != 'choice' or choice not in ('A', 'B', 'C'):
            raise ValueError('invalid proposal branch')
        raw = _rendered_options(case, state['phase'], state)[choice]
        return _core_handler(dict(op='propose', state_json=dumps(state), user_text=raw,
                                  candidate_json=dumps(dict(action='submit', plan={'choice':choice,'reason':''}, quote=raw, question=''))))
    if op == 'reflect_auto_majors':
        state = loads(params['state_json'])
        raw = params.get('user_text', '')
        params['op'] = 'reflect'
        # An absent optional line must not erase a previously stated intention.
        params['majors'] = _explicit_majors(raw) if re.search(r'(?:^|\\n)\\s*想了解[:：]', raw) else state.get('requested_majors', [])
        return _core_handler(params)
    if op == 'confirm_record':
        raw = params.get('user_text', '')
        if raw.startswith(('更正并确认：','更正并确认:')):
            state = loads(params['state_json'])
            if re.search(r'(?:^|\\n)\\s*想了解[:：]', re.split('[:：]',raw,maxsplit=1)[1]):
                state['requested_majors'] = _explicit_majors(re.split('[:：]',raw,maxsplit=1)[1])
                params['state_json'] = dumps(state)
        return _core_handler(params)
    return _legacy_platform_handler(params)


def handler(params):
    try:
        result = _v4_dispatch(params)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        if isinstance(params, dict) and params.get('state_json'):
            result = _core_handler(dict(op='invalid_recoverable_operation', state_json=params['state_json']))
        else:
            text = '## 这次还没有开始具体情境\\n\\n刚才的选择没有成功接上，因此没有生成新的计算结果。你可以重新开始一次；这一步不会被记录成做题结果。'
            result = dict(ok=False, action='error', display_text=text, report=text, feedback=text, error=str(exc))
    if result.get('state_json'):
        try:
            state = loads(result['state_json'])
            case = case_of(state)
            result['mode'] = _mode_of(case, state)
            result['group_id'] = state.get('group_id', '')
            if not result.get('reflection_prompt'):
                result['reflection_prompt'] = case['reflection']
            if result['mode'] == 'choice':
                rendered = _rendered_options(case, state['phase'], state)
                for choice in ('A','B','C'):
                    result['choice'+choice] = rendered[choice]
            result['record_summary'] = _record_summary(state)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            pass
    notice = params.get('finish_notice', '') if isinstance(params, dict) else ''
    if notice and (result.get('report') or result.get('feedback')):
        result['display_text'] = '*'+markdown_text(notice)+'*\\n\\n'+result.get('display_text',result.get('report',''))
        if result.get('feedback'):
            result['feedback'] = '*'+markdown_text(notice)+'*\\n\\n'+result['feedback']
    names = ['action','state_json','prompt','preview','feedback','result_json','report','error','case_id','task_id',
             'normalizer_context','knowledge_query','catalog_json','scope_json','reflection_prompt','selection_json',
             'display_text','mode','group_id','case1','case2','case3','choiceA','choiceB','choiceC','record_summary']
    normalized = {name:result.get(name,'') for name in names}
    normalized['ok'] = result.get('ok',False)
    return normalized
'''

RUNTIME = ENGINE + '\n' + ADAPTER + '\n' + APPENDED
RUNTIME_LEAN = ENGINE_LEAN + '\n' + ADAPTER + '\n' + APPENDED
BANK_OPS = {'init_selection', 'prepare_cases', 'set_activity', 'select_case', 'start', 'catalog'}


def _packed(src):
    """Compress a code-node source; the platform still receives plain Python."""
    blob = base64.b85encode(zlib.compress(src.encode('utf-8'), 9)).decode('ascii')
    return ("import base64 as _rt_b64, zlib as _rt_z\n"
            "exec(compile(_rt_z.decompress(_rt_b64.b85decode(" + repr(blob) + ")).decode('utf-8'), '<runtime>', 'exec'), globals())\n")
(PKG / 'code').mkdir(exist_ok=True)
(PKG / 'code/platform_runtime.py').write_text(RUNTIME, encoding='utf-8')

NORMALIZE_SYSTEM = ''''''
ANSWER_SYSTEM = ''''''
ACTIVITY_SYSTEM = ''''''
DRAFT_SYSTEM = ''''''


def _prompt_spec(filename):
    text = (PKG/'prompts'/filename).read_text(encoding='utf-8')
    return text.split('用户变量模板',1)[0].strip()

NORMALIZE_SYSTEM = _prompt_spec('normalize_input.md')
ANSWER_SYSTEM = _prompt_spec('resource_answer.md')
ACTIVITY_SYSTEM = _prompt_spec('activity_bridge.md')
DRAFT_SYSTEM = _prompt_spec('kb_practice_draft.md')

def xid(label):
    stamp = base64.b32hexdecode(BASE['ID'].upper()+'====')[:4]
    return base64.b32hexencode(stamp+hashlib.sha256(label.encode()).digest()[:8]).decode().lower().rstrip('=')


class Flow:
    def __init__(self, name, with_kb=False):
        self.data = {k:copy.deepcopy(v) for k,v in BASE.items() if k!='Nodes'}
        self.data.update(DisplayName=name, ID=xid(name+'-4.0.0'), UniqueName=xid(name+'-4.0.0'), Nodes=[])
        self.data['Depends']['KnowledgeMap'] = copy.deepcopy(KB_SAMPLE['Depends']['KnowledgeMap']) if with_kb else {}
        self.nodes = {}
        self.name = name

    def add(self, name, kind, deps=()):
        node = copy.deepcopy(TEMPLATES[kind])
        node.update(Code=xid(self.name+'-4.0.0'+name), ID=xid(self.name+'-4.0.0'+name), Name=name,
                    Depends=[self.edge(d) if isinstance(d,str) else self.edge(*d) for d in deps])
        node['Layout'] = {'X':200+400*len(self.nodes),'Y':300}
        self.nodes[name] = node
        self.data['Nodes'].append(node)
        return node['Configs'][kind]

    def edge(self, name, port=None):
        result={'NodeCode':self.nodes[name]['Code']}
        if port:result['PortID']=port
        return result

    def ref(self, name, source, path):
        return {'Name':name, 'NodeCode':self.nodes[source]['Code'],'Path':path,'RefType':'node_field'}

    @staticmethod
    def val(name, value):
        return {'Name':name,'JsonValue':json.dumps(value,ensure_ascii=False),'RefType':'value'}

    def code(self, name, deps, inputs, source, fields):
        config=self.add(name,'Code',deps)
        # Platform validation rejects empty-string constant inputs; the runtime
        # already defaults missing params to "" via params.get(k, "").
        inputs=[iv for iv in inputs if not (iv.get('RefType')=='value' and iv.get('JsonValue') in ('""', "''"))]
        config.update(Code=_packed(source) if len(source)>2000 else source, InputVariables=inputs,
                      OutputSchema=[{'Name':key,'Type':typ} for key,typ in fields],Language=1,Retries=0,TimeoutSeconds=120)

    def engine(self, name, deps, op, inputs):
        self.code(name,deps,[self.val('op',op)]+inputs,RUNTIME if op in BANK_OPS else RUNTIME_LEAN,ENGINE_FIELDS)

    def info(self, name, deps, question, variables=()):
        config=self.add(name,'InformationGathering',deps)
        config.update(QuestionTemplate=question,TemplateVars=list(variables),ExtractParameters=True,
            ExtractSchema=[{'Name':'unused_ack','Type':0,'Desc':'平台必填占位，收到任意回答后填写received；不要追问。业务只读USER_RESPONSE，不读本字段。'}])
        config['ModelConfig']['Temperature']=0


    def buttons(self, name, deps, question, options, variables=()):
        config = self.add(name, 'InformationGathering', deps)
        model = copy.deepcopy(config['ModelConfig'])
        template = next(n['Configs']['InformationGathering'] for n in BUTTON_SAMPLE['Nodes'] if n['Type']=='InformationGathering')
        config.clear()
        config.update(copy.deepcopy(template))
        config.update(QuestionTemplate=question, TemplateVars=list(variables), ModelConfig=model,
            ExtractParameters=True, ExtractSchema=[{'Name':'unused_ack','Type':0,'Desc':'平台必填占位，收到回答填写received，不追问；下游不读本字段。'}])
        config['ModelConfig']['Temperature'] = 0
        config['OptionConfig'] = {'BranchMode': True, 'OptionType': 'solid', 'Options':
            [{'CondID':port,'OptionID':oid,'OptionContent':text} for port,oid,text in options] +
            [{'CondID':'class_other','OptionID':'Others','OptionContent':'Others'}]}

    def merge(self, name, sources, fields):
        config = self.add(name, 'VariableMerge', sources)
        config['Groups'] = [{'Name':key,'Type':typ,'Variables':
            [self.ref(key+'['+str(i)+']',source,key) for i,source in enumerate(sources)]}
            for key,typ in fields]

    def message(self,name,deps,text,variables):
        config=self.add(name,'Message',deps)
        config.update(Content=text,InputVariables=variables,AsContext=True,RenderAsReasoning=False)

    def llm(self,name,deps,system,prompt,variables,max_tokens=1000):
        config=self.add(name,'LLM',deps)
        config.update(SystemPrompt=system,Prompt=prompt,InputVariables=variables,OutputFormat='text',
            OutputSchema=[{'Name':'raw_output','Type':0}],Temperature=0,MaxTokens=max_tokens,EnableChatHistories=False)

    def condition(self,name,source,branches):
        config=self.add(name,'Condition',[source])
        config.update(ElseBranch={'ID':'else'},IfBranches=[{'ID':port,'ConditionLogic':'AND','Conditions':[
            {'Left':self.ref('Left',source,path),'Operator':'EQ','Right':self.val('Right',value)} for path,value in terms]} for port,terms in branches])

    def terminal(self,name,dependency,source,field='feedback'):
        if field=='report' and ('Stop' in name or name=='XRecordStopped'):
            self.code(name,[dependency],[self.ref('report',source,'report'),self.ref('feedback',source,'feedback')],
                'def handler(params):\n    return {"final_text":(params.get("feedback") or "本次体验已结束。")+"\\n\\n"+(params.get("report") or "记录未确认。")}\n',[('final_text',0)])
            return
        self.code(name,[dependency],[self.ref('text',source,field),self.val('fallback','本次未完成有效计算或确认，可重新发起。')],
                  SUPPORT+'\ndef handler(params):\n    return terminal_text(params)\n',[('final_text',0)])

    def end_merge(self,terminals):
        config=self.add('FinalMerge','VariableMerge',terminals)
        config['Groups']=[{'Name':'final','Type':0,'Variables':[self.ref('final['+str(i)+']',name,'final_text') for i,name in enumerate(terminals)]}]
        config=self.add('End','End',['FinalMerge'])
        config.update(OutputType='Variable',InputVariables=[self.ref('final_text','FinalMerge','final')])

    def save(self, filename):
        levels = {}
        pending = list(self.data['Nodes'])
        while pending:
            ready = [node for node in pending if all(dep['NodeCode'] in levels for dep in node.get('Depends',[]))]
            if not ready:raise ValueError('Cyclic or unresolved dependency')
            for node in ready:
                levels[node['Code']] = 1+max([levels[dep['NodeCode']] for dep in node.get('Depends',[])],default=-1)
                pending.remove(node)
        columns = {}
        for node in self.data['Nodes']:
            columns.setdefault(levels[node['Code']],[]).append(node)
        for depth,nodes in columns.items():
            for row,node in enumerate(nodes):
                node['Layout']={'X':180+depth*420,'Y':260+row*260}
        self.data['Desc']=self.description
        target=PKG/'platform_import'/filename
        target.write_text(yaml.dump(self.data,Dumper=LiteralDumper,allow_unicode=True,sort_keys=False,width=160),encoding='utf-8')
        assert yaml.safe_load(target.read_text(encoding='utf-8'))==self.data
        return target


ENGINE_FIELDS=[(x,2 if x=='ok' else 0) for x in ['ok', 'action', 'state_json', 'prompt', 'preview', 'feedback', 'result_json', 'report', 'error', 'case_id', 'task_id', 'normalizer_context', 'knowledge_query', 'catalog_json', 'scope_json', 'reflection_prompt', 'selection_json', 'display_text', 'mode', 'group_id', 'case1', 'case2', 'case3', 'choiceA', 'choiceB', 'choiceC', 'record_summary']]


class LiteralDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):return True


LiteralDumper.add_representer(str,lambda dumper,text:dumper.represent_scalar('tag:yaml.org,2002:str',text,style='|' if '\n' in text else None))


def add_knowledge(flow,name,deps,query_source,query_path):
    config=flow.add(name,'Knowledge',deps)
    config['QueryVariable']=flow.ref('query',query_source,query_path)
    config['TopK']=4
    # Retain the example's search method/threshold as an initial configuration,
    # not a claim that these parameters were optimized on the new corpus.
    flow.code(name+'Context',[name],[flow.ref('hits',name,'outputList')],SUPPORT+'\ndef handler(params):\n    return retrieval_context(params)\n',
        [('context',0),('hit_count',1),('retrieval_note',0),('source_list',0)])
    return name+'Context'


def add_grounded_answer(flow,prefix,deps,query_source,query_path,knowledge_node,context_node,brief=False):
    flow.llm(prefix+'LLM',deps,ACTIVITY_SYSTEM if brief else ANSWER_SYSTEM,
        ('作为体验前说明，不泄露题目答案。\n' if brief else '')+'问题：{{query}}\n检索正文：{{context}}\n检索状态：{{note}}',
        [flow.ref('query',query_source,query_path),flow.ref('context',context_node,'context'),flow.ref('note',context_node,'retrieval_note')],1000)
    flow.code(prefix+'Check',[prefix+'LLM'],[flow.ref('hits',knowledge_node,'outputList'),flow.ref('answer_json',prefix+'LLM','raw_output')],
        SUPPORT+'\ndef handler(params):\n    return validate_answer(params)\n',[('final_text',0),('ok',2)])
    return prefix+'Check'


"""Experience graph v4; splice after Flow/add_knowledge/add_grounded_answer.

Uses the existing builder globals Flow, PKG, NORMALIZE_SYSTEM, copy and json.
Flow.buttons(name,deps,question,[(port,id,text)],variables) must append the
class_other branch using the real tenant option schema. Flow.merge accepts
[(field,type)]. Button choices are constants; class_other safely ends with
the existing record and never reads unverified option-node raw fields.

Adapter operations and output fields are documented in review/adapter_contract.md.
"""

_V4_FIELDS = [
    ('state_json', 0), ('selection_json', 0), ('action', 0), ('ok', 2),
    ('prompt', 0), ('preview', 0), ('feedback', 0), ('display_text', 0),
    ('normalizer_context', 0), ('mode', 0), ('group_id', 0), ('choiceA', 0), ('choiceB', 0),
    ('choiceC', 0), ('case1', 0), ('case2', 0), ('case3', 0),
    ('result_json', 0), ('knowledge_query', 0), ('reflection_prompt', 0),
    ('record_summary', 0),
]


def _v4_copy(flow, name, dependency, source, fields=None, constants=None, refs=None):
    """A tiny edge adapter; never embeds the large runtime just to select a value."""
    fields = fields if fields is not None else _V4_FIELDS
    inputs = {k: flow.ref(k, source, k) for k, _ in fields}
    output = dict(fields)
    for key, value in (constants or {}).items():
        # The platform rejects empty-string constant inputs ("参数节点配置不合法").
        # The generated code already defaults missing keys to "", so skip them.
        if value == "":
            output[key] = 0
            continue
        inputs[key] = flow.val(key, value)
        output[key] = 2 if isinstance(value, bool) else (1 if isinstance(value, int) else 0)
    for key, node, path, typ in (refs or []):
        inputs[key] = flow.ref(key, node, path)
        output[key] = typ
    keys = list(output)
    code = 'def handler(params):\n    return {k:params.get(k, "") for k in ' + repr(keys) + '}\n'
    flow.code(name, [dependency], list(inputs.values()), code, list(output.items()))
    return name


def _v4_exit(flow, name, dependency, source, notice='', selection=False):
    if selection:
        fields = [('selection_json', 0)]
        constants = {'user_text': ''}
        target = flow._v4_selection_exits
    else:
        fields = [('state_json', 0)]
        constants = {'finish_notice': notice}
        target = flow._v4_state_exits
    _v4_copy(flow, name, dependency, source, fields, constants, [])
    target.append(name)
    return name


def _v4_extract(flow, name, dependency, raw_source, state_source, task_source):
    flow.llm(name, [dependency], NORMALIZE_SYSTEM,
        '本轮题目：{{task}}\n方案格式：{{schema}}\n本轮学生原话：{{raw}}',
        [flow.ref('task', task_source, 'prompt'),
         flow.ref('schema', task_source, 'normalizer_context'),
         flow.ref('raw', raw_source, 'USER_RESPONSE')], 800)
    proposed = name + 'Propose'
    flow.engine(proposed, [name], 'propose',
        [flow.ref('state_json', state_source, 'state_json'),
         flow.ref('user_text', raw_source, 'USER_RESPONSE'),
         flow.ref('candidate_json', name, 'raw_output')])
    return proposed


def add_phase(flow, prefix, state_source, task_source=None, prompt_field='prompt', before=None):
    """One fixed stage, one optional correction, all exits retain prior facts."""
    task_source = task_source or state_source
    before = before or state_source
    title = '第一次尝试' if prefix == 'B' else '换个条件，再试一次'
    flow.condition(prefix+'Mode', state_source, [('if01', [('mode', 'choice')])])
    # Execution may also need to wait for a grounded explanation message.
    flow.nodes[prefix+'Mode']['Depends'] = [flow.edge(before)]
    flow.buttons(prefix+'Choice', [(prefix+'Mode', 'if01')],
        '## '+title+'\n\n{{task}}\n\n请选择你想尝试的做法；也可以看提示或结束。',
        [('class01', 'A', '{{choiceA}}'), ('class02', 'B', '{{choiceB}}'),
         ('class03', 'C', '{{choiceC}}'), ('class04', 'hint', '给我一点提示'),
         ('class05', 'finish', '结束并整理记录')],
        [flow.ref('task', task_source, prompt_field)] +
        [flow.ref('choice'+x, state_source, 'choice'+x) for x in 'ABC'])
    chosen = []
    for index, letter in enumerate('ABC', 1):
        node = prefix+'Pick'+letter
        _v4_copy(flow, node, (prefix+'Choice', 'class0'+str(index)), state_source,
            [('state_json', 0)], {'choice': letter},
            [('user_text', state_source, 'choice'+letter, 0)])
        chosen.append(node)
    flow.merge(prefix+'ChoiceMerge', chosen,
        [('state_json', 0), ('choice', 0), ('user_text', 0)])
    flow.engine(prefix+'ButtonPropose', [prefix+'ChoiceMerge'], 'submit_button',
        [flow.ref(k, prefix+'ChoiceMerge', k) for k in ['state_json', 'choice', 'user_text']])
    _v4_exit(flow, prefix+'ChoiceExit', (prefix+'Choice', 'class05'), state_source)
    _v4_exit(flow, prefix+'ChoiceOther', (prefix+'Choice', 'class_other'), state_source,
        '这次没有选中页面上的按钮，我先把已经完成的部分整理成记录。')

    flow.info(prefix+'Ask', [(prefix+'Mode', 'else')],
        '## '+title+'\n\n{{task}}\n\n你想怎么做？可以说说做法和理由。\n\n*需要提示或想结束时，直接告诉我就好。*',
        [flow.ref('task', task_source, prompt_field)])
    proposed = _v4_extract(flow, prefix+'Extract', prefix+'Ask',
        prefix+'Ask', state_source, task_source)
    flow.merge(prefix+'Candidate', [prefix+'ButtonPropose', proposed], _V4_FIELDS)
    flow.condition(prefix+'CandidateGate', prefix+'Candidate', [
        ('if01', [('ok', True), ('action', 'awaiting_confirmation')]),
        ('if02', [('action', 'stopped')]),
        ('if03', [('action', 'report_gate')])])
    _v4_exit(flow, prefix+'StoppedAtProposal',
        (prefix+'CandidateGate', 'if02'), prefix+'Candidate')
    _v4_exit(flow, prefix+'GateAtProposal',
        (prefix+'CandidateGate', 'if03'), prefix+'Candidate')

    flow.buttons(prefix+'Confirm', [(prefix+'CandidateGate', 'if01')],
        '{{preview}}\n\n{{feedback}}\n\n这个方案和你的意思一致吗？',
        [('class01', 'confirm', '就按这个试'), ('class02', 'edit', '我想改一下'),
         ('class03', 'hint', '给我一点提示'), ('class04', 'finish', '结束并整理记录')],
        [flow.ref('preview', prefix+'Candidate', 'preview'),
         flow.ref('feedback', prefix+'Candidate', 'feedback')])
    flow.engine(prefix+'Compute', [(prefix+'Confirm', 'class01')], 'confirm',
        [flow.ref('state_json', prefix+'Candidate', 'state_json'), flow.val('user_text', '确认')])
    flow.condition(prefix+'ComputeGate', prefix+'Compute', [
        ('if01', [('ok', True), ('action', 'evaluated')])])
    _v4_exit(flow, prefix+'ComputeExit', (prefix+'ComputeGate', 'else'),
        prefix+'Compute', '这一轮没有形成新的已确认结果，下面保留此前的记录。')
    _v4_exit(flow, prefix+'ConfirmExit', (prefix+'Confirm', 'class04'), prefix+'Candidate')

    # A single help engine is shared by both entry points. Only edge maps copy state.
    hint_inputs = []
    for tag, dependency, source in [
        ('ChoiceHint', (prefix+'Choice', 'class04'), state_source),
        ('ConfirmHint', (prefix+'Confirm', 'class03'), prefix+'Candidate')]:
        hint_inputs.append(_v4_copy(flow, prefix+tag, dependency, source, [('state_json', 0)]))
    flow.merge(prefix+'HintMerge', hint_inputs, [('state_json', 0)])
    flow.engine(prefix+'Hint', [prefix+'HintMerge'], 'hint',
        [flow.ref('state_json', prefix+'HintMerge', 'state_json')])
    edit_sources = [prefix+'Hint']
    edit_sources.append(_v4_copy(flow, prefix+'WantEdit',
        (prefix+'Confirm', 'class02'), prefix+'Candidate'))
    edit_sources.append(_v4_copy(flow, prefix+'NeedsDetails',
        (prefix+'CandidateGate', 'else'), prefix+'Candidate'))
    flow.merge(prefix+'EditState', edit_sources, _V4_FIELDS)
    flow.info(prefix+'Edit', [prefix+'EditState'],
        '## 再说具体一点\n\n{{feedback}}\n\n{{task}}\n\n请告诉我这次想尝试的完整方案；也可以直接结束并整理已有记录。',
        [flow.ref('feedback', prefix+'EditState', 'feedback'),
         flow.ref('task', task_source, prompt_field)])
    edited = _v4_extract(flow, prefix+'EditExtract', prefix+'Edit',
        prefix+'Edit', prefix+'EditState', task_source)
    _v4_exit(flow, prefix+'ConfirmOther', (prefix+'Confirm', 'class_other'), prefix+'Candidate',
        '这次没有选中页面上的按钮，尚未确认的新方案不会计入结果。下面保留已经完成的记录。')
    _v4_copy(flow, prefix+'RetryCandidate', edited, edited)
    flow.condition(prefix+'RetryCandidateGate', prefix+'RetryCandidate', [
        ('if01', [('ok', True), ('action', 'awaiting_confirmation')]),
        ('if02', [('action', 'report_gate')])])
    _v4_exit(flow, prefix+'RetryCandidateExit',
        (prefix+'RetryCandidateGate', 'else'), prefix+'RetryCandidate',
        '这一轮还没有确认出一个完整方案，已有结果仍会保留。')
    _v4_exit(flow, prefix+'RetryGateExit',
        (prefix+'RetryCandidateGate', 'if02'), prefix+'RetryCandidate')
    flow.buttons(prefix+'RetryConfirm', [(prefix+'RetryCandidateGate', 'if01')],
        '{{preview}}\n\n如果已经准确，就按这个试；想先到这里，也可以直接整理记录。',
        [('class01', 'confirm', '就按这个试'), ('class02', 'finish', '结束并整理记录')],
        [flow.ref('preview', prefix+'RetryCandidate', 'preview')])
    flow.engine(prefix+'RetryCompute', [(prefix+'RetryConfirm', 'class01')], 'confirm',
        [flow.ref('state_json', prefix+'RetryCandidate', 'state_json'), flow.val('user_text', '确认')])
    flow.condition(prefix+'RetryComputeGate', prefix+'RetryCompute', [
        ('if01', [('ok', True), ('action', 'evaluated')])])
    _v4_exit(flow, prefix+'RetryComputeExit', (prefix+'RetryComputeGate', 'else'),
        prefix+'RetryCompute', '这一轮没有新增已确认结果，下面是已有记录。')
    _v4_exit(flow, prefix+'RetryConfirmExit',
        (prefix+'RetryConfirm', 'class02'), prefix+'RetryCandidate')
    _v4_exit(flow, prefix+'LastOtherExit',
        (prefix+'RetryConfirm', 'class_other'), prefix+'RetryCandidate',
        '本次先记录到这里。没有经过你确认的新方案，不会计入结果。')

    success = []
    for label, gate, source in [('Success', 'ComputeGate', 'Compute'),
                               ('RetrySuccess', 'RetryComputeGate', 'RetryCompute')]:
        success.append(_v4_copy(flow, prefix+label, (prefix+gate, 'if01'),
            prefix+source, [('state_json', 0), ('feedback', 0), ('result_json', 0)]))
    flow.merge(prefix+'SuccessMerge', success,
        [('state_json', 0), ('feedback', 0), ('result_json', 0)])
    flow.engine(prefix+'Ready', [prefix+'SuccessMerge'], 'report',
        [flow.ref('state_json', prefix+'SuccessMerge', 'state_json')])
    flow.message(prefix+'Feedback', [prefix+'Ready'],
        '## 这次尝试的结果\n\n{{feedback}}',
        [flow.ref('feedback', prefix+'SuccessMerge', 'feedback')])
    return prefix+'Ready', prefix+'Feedback', []


def _add_report_gate(flow):
    """Shared explicit pre-report gate: write thoughts / render directly / continue.

    The record is only rendered after this gate; the thoughts entrance is a
    first-class button plus a standalone prominent question, never a hidden field.
    """
    flow.condition('GateSwitch', 'StateFinish', [('if01', [('action', 'report_gate')])])
    flow.terminal('StateTerminal', ('GateSwitch', 'else'), 'StateFinish', 'display_text')
    flow.buttons('GateButtons', [('GateSwitch', 'if01')],
        '{{gate}}\n\n**这是整理记录前的最后一步，由你决定。**',
        [('class01', 'write', '写一句我的想法，再生成记录'),
         ('class02', 'skip', '不写想法，直接生成记录'),
         ('class03', 'cancel', '先不生成，我再说几句')],
        [flow.ref('gate', 'StateFinish', 'feedback')])
    flow.info('ThoughtsInfo', [('GateButtons', 'class01')],
        '## 留下一句你的想法\n\n可以写印象最深的一刻、一句吐槽，或者给这次体验起个一句话标题——想说什么都可以。\n\n如果有想进一步了解的专业，可以另起一行写“想了解：专业名称”（可不填）。\n\n*你的话会原样写进记录，不会被评分，也不会被拿来判断你适不适合什么。*')
    flow.engine('FinalizeWrite', ['ThoughtsInfo'], 'report_final',
        [flow.ref('state_json', 'StateFinish', 'state_json'),
         flow.ref('user_text', 'ThoughtsInfo', 'USER_RESPONSE')])
    flow.engine('FinalizeSkip', [('GateButtons', 'class02')], 'report_final',
        [flow.ref('state_json', 'StateFinish', 'state_json'),
         flow.val('skip_reflection', True)])
    flow.info('ContinueAsk', [('GateButtons', 'class03'), ('GateButtons', 'class_other')],
        '## 好的，记录先不生成\n\n你可以继续说想法、补充一个新方案，或者改主意；想结束时说“生成记录”就好。')
    flow.engine('ReportCancelOp', ['ContinueAsk'], 'report_cancel',
        [flow.ref('state_json', 'StateFinish', 'state_json')])
    flow.llm('ContinueExtract', ['ReportCancelOp'], NORMALIZE_SYSTEM,
        '本轮题目：{{task}}\n方案格式：{{schema}}\n本轮学生原话：{{raw}}',
        [flow.ref('task', 'ReportCancelOp', 'prompt'),
         flow.ref('schema', 'ReportCancelOp', 'normalizer_context'),
         flow.ref('raw', 'ContinueAsk', 'USER_RESPONSE')], 800)
    flow.engine('ContinuePropose', ['ContinueExtract'], 'propose',
        [flow.ref('state_json', 'ReportCancelOp', 'state_json'),
         flow.ref('user_text', 'ContinueAsk', 'USER_RESPONSE'),
         flow.ref('candidate_json', 'ContinueExtract', 'raw_output')])
    flow.condition('ContinueGate', 'ContinuePropose', [
        ('if01', [('ok', True), ('action', 'awaiting_confirmation')]),
        ('if02', [('action', 'report_gate')]), ('if03', [('action', 'stopped')])])
    flow.buttons('ContinueConfirm', [('ContinueGate', 'if01')],
        '{{preview}}\n\n{{feedback}}\n\n这个方案和你的意思一致吗？',
        [('class01', 'confirm', '就按这个试'), ('class02', 'finish', '不弄了，去整理记录')],
        [flow.ref('preview', 'ContinuePropose', 'preview'),
         flow.ref('feedback', 'ContinuePropose', 'feedback')])
    flow.engine('ContinueCompute', [('ContinueConfirm', 'class01')], 'confirm',
        [flow.ref('state_json', 'ContinuePropose', 'state_json'), flow.val('user_text', '确认')])
    flow.message('ContinueDoneMsg', ['ContinueCompute'],
        '## 这次尝试的结果\n\n{{feedback}}', [flow.ref('feedback', 'ContinueCompute', 'feedback')])
    _v4_copy(flow, 'ContinueFailCopy', ('ContinueGate', 'else'), 'ContinuePropose', _V4_FIELDS)
    flow.message('ContinueFailMsg', ['ContinueFailCopy'],
        '{{feedback}}', [flow.ref('feedback', 'ContinueFailCopy', 'feedback')])
    flow.condition('Gate2Switch', 'ContinueCompute', [
        ('if01', [('ok', True), ('action', 'evaluated')])])
    _v4_copy(flow, 'Gate2FromStop', ('ContinueGate', 'if02'), 'ContinuePropose', [('state_json', 0)])
    _v4_copy(flow, 'Gate2FromStopped', ('ContinueGate', 'if03'), 'ContinuePropose', [('state_json', 0)])
    _v4_copy(flow, 'Gate2FromFail', 'ContinueFailMsg', 'ContinueFailCopy', [('state_json', 0)])
    _v4_copy(flow, 'Gate2FromCancel', ('ContinueConfirm', 'class02'), 'ContinuePropose', [('state_json', 0)])
    _v4_copy(flow, 'Gate2FromOther', ('ContinueConfirm', 'class_other'), 'ContinuePropose', [('state_json', 0)])
    _v4_copy(flow, 'Gate2FromComputed', ('Gate2Switch', 'if01'), 'ContinueCompute', [('state_json', 0)])
    _v4_copy(flow, 'Gate2FromComputeFail', ('Gate2Switch', 'else'), 'ContinueCompute', [('state_json', 0)])
    flow.merge('Gate2Merge', ['Gate2FromStop', 'Gate2FromStopped', 'Gate2FromFail',
                              'Gate2FromCancel', 'Gate2FromOther', 'Gate2FromComputed', 'Gate2FromComputeFail'],
        [('state_json', 0)])
    flow.nodes['Gate2Merge']['Depends'] = [flow.edge('ContinueDoneMsg'), flow.edge('ContinueFailMsg'),
        flow.edge('Gate2FromStop'), flow.edge('Gate2FromStopped'), flow.edge('Gate2FromFail'),
        flow.edge('Gate2FromCancel'), flow.edge('Gate2FromOther'), flow.edge('Gate2FromComputed'),
        flow.edge('Gate2FromComputeFail')]
    flow.engine('Gate2Prepare', ['Gate2Merge'], 'finish',
        [flow.ref('state_json', 'Gate2Merge', 'state_json')])
    flow.buttons('Gate2Buttons', ['Gate2Prepare'],
        '{{gate}}',
        [('class01', 'write', '写一句我的想法，再生成记录'),
         ('class02', 'skip', '不写想法，直接生成记录'),
         ('class03', 'cancel', '先不生成，结束本次体验')],
        [flow.ref('gate', 'Gate2Prepare', 'feedback')])
    flow.info('Thoughts2Info', [('Gate2Buttons', 'class01')],
        '## 留下一句你的想法\n\n印象最深的一刻、一句吐槽，或给这次体验起个一句话标题都可以。\n\n*你的话会原样写进记录，不会被评分。*')
    flow.engine('Finalize2Write', ['Thoughts2Info'], 'report_final',
        [flow.ref('state_json', 'Gate2Prepare', 'state_json'),
         flow.ref('user_text', 'Thoughts2Info', 'USER_RESPONSE')])
    flow.engine('Finalize2Skip', [('Gate2Buttons', 'class02')], 'report_final',
        [flow.ref('state_json', 'Gate2Prepare', 'state_json'),
         flow.val('skip_reflection', True)])
    flow.message('NoReportMsg', [('Gate2Buttons', 'class03'), ('Gate2Buttons', 'class_other')],
        '好的，记录保留未生成，本次体验先到这里。已经确认过的内容没有被整理成报告；之后想再体验时，可以重新开始。', [])
    flow.code('NoReportTerminal', ['NoReportMsg'],
        [flow.val('text', '好的，记录保留未生成，本次体验先到这里。已经确认过的内容没有被整理成报告；之后想再体验时，可以重新开始。'),
         flow.val('fallback', '本次体验已结束。')],
        SUPPORT+'\ndef handler(params):\n    return terminal_text(params)\n', [('final_text', 0)])
    flow.merge('RecordMerge', ['FinalizeWrite', 'FinalizeSkip', 'Finalize2Write', 'Finalize2Skip'], _V4_FIELDS)
    flow.condition('RecordGate', 'RecordMerge', [('if01', [('ok', True), ('action', 'report_ready')])])
    flow.code('RecordErrorTerminal', [('RecordGate', 'else')],
        [flow.val('text', '这一步没有成功生成记录；已确认的内容仍保留，可以重新发起一次体验。'),
         flow.val('fallback', '本次体验已结束。')],
        SUPPORT+'\ndef handler(params):\n    return terminal_text(params)\n', [('final_text', 0)])
    flow.buttons('RecordButtons', [('RecordGate', 'if01')],
        '{{summary}}',
        [('class01', 'confirm', '记录准确，完成体验'),
         ('class02', 'edit', '改一下我的想法'),
         ('class03', 'skip', '先不确认，保留')],
        [flow.ref('summary', 'RecordMerge', 'record_summary')])
    flow.engine('ConfirmRecordOp', [('RecordButtons', 'class01')], 'confirm_record',
        [flow.ref('state_json', 'RecordMerge', 'state_json'), flow.val('user_text', '确认记录')])
    flow.engine('SkipConfirmOp', [('RecordButtons', 'class03')], 'confirm_record',
        [flow.ref('state_json', 'RecordMerge', 'state_json'), flow.val('user_text', '先不确认')])
    flow.engine('SkipConfirmOtherOp', [('RecordButtons', 'class_other')], 'confirm_record',
        [flow.ref('state_json', 'RecordMerge', 'state_json'), flow.val('user_text', '先不确认')])
    flow.info('ThoughtsEditInfo', [('RecordButtons', 'class02')],
        '## 修改你的想法\n\n请写下你希望记录的完整想法。已经做过的题目和结果不会被改动。')
    flow.engine('FinalizeEdit', ['ThoughtsEditInfo'], 'report_final',
        [flow.ref('state_json', 'RecordMerge', 'state_json'),
         flow.ref('user_text', 'ThoughtsEditInfo', 'USER_RESPONSE')])
    flow.condition('RecordEditGate', 'FinalizeEdit', [('if01', [('ok', True), ('action', 'report_ready')])])
    # A failed re-finalize must still end the conversation with a real final_text;
    # leaving the else port unwired stranded the run without reaching the single End.
    flow.terminal('RecordEditErrorTerminal', ('RecordEditGate', 'else'), 'FinalizeEdit', 'display_text')
    flow.buttons('RecordButtons2', [('RecordEditGate', 'if01')],
        '{{summary}}',
        [('class01', 'confirm', '记录准确，完成体验'),
         ('class02', 'skip', '先不确认，保留')],
        [flow.ref('summary', 'FinalizeEdit', 'record_summary')])
    flow.engine('ConfirmRecordOp2', [('RecordButtons2', 'class01')], 'confirm_record',
        [flow.ref('state_json', 'FinalizeEdit', 'state_json'), flow.val('user_text', '确认记录')])
    flow.engine('SkipConfirmOp2', [('RecordButtons2', 'class02'), ('RecordButtons2', 'class_other')], 'confirm_record',
        [flow.ref('state_json', 'FinalizeEdit', 'state_json'), flow.val('user_text', '先不确认')])
    flow.terminal('RecordTerminal', 'ConfirmRecordOp', 'ConfirmRecordOp', 'display_text')
    flow.terminal('SkipTerminal', 'SkipConfirmOp', 'SkipConfirmOp', 'display_text')
    flow.terminal('SkipOtherTerminal', 'SkipConfirmOtherOp', 'SkipConfirmOtherOp', 'display_text')
    flow.terminal('RecordTerminal2', 'ConfirmRecordOp2', 'ConfirmRecordOp2', 'display_text')
    flow.terminal('SkipTerminal2', 'SkipConfirmOp2', 'SkipConfirmOp2', 'display_text')
    return ['StateTerminal', 'RecordTerminal', 'SkipTerminal', 'SkipOtherTerminal',
            'RecordTerminal2', 'SkipTerminal2', 'NoReportTerminal', 'RecordErrorTerminal',
            'RecordEditErrorTerminal']


def build_explore(with_kb=True):
    name = 'WF_Explore_One_v4' if with_kb else 'WF_Explore_One_v4_Offline'
    flow = Flow(name, with_kb)
    flow._v4_selection_exits = []
    flow._v4_state_exits = []
    start = flow.add('Start', 'Start')
    schema = [
        {'Name': 'task_id', 'Type': 0, 'Required': True,
         'Desc': '已明确的活动方向；没有明确方向时传auto，仅供工具内部使用。'},
        {'Name': 'reported_group_text', 'Type': 0, 'Required': True,
         'Desc': '学生本人已明确说明的当前大类原文；没有时传空字符串，不从专业兴趣推测。'},
        {'Name': 'session_seed', 'Type': 0, 'Required': False,
         'Desc': '本次会话的随机种子（任意短字符串），用于情境表面细节随机化；没有时传空串。'},
        {'Name': 'exclude_case_ids', 'Type': 0, 'Required': False,
         'Desc': '本次对话里已经体验过的case_id，逗号分隔；没有时传空串。'}]
    start.update(InputSchema=schema, OutputSchema=copy.deepcopy(schema))
    flow.engine('InitSelection', ['Start'], 'init_selection',
        [flow.ref(k, 'Start', k) for k in ['task_id', 'reported_group_text', 'session_seed', 'exclude_case_ids']])
    flow.message('Welcome', ['InitSelection'],
        '{{intro}}', [flow.ref('intro', 'InitSelection', 'display_text')])
    flow.condition('GroupGate', 'InitSelection', [('if01', [('action', 'need_group')])])
    flow.nodes['GroupGate']['Depends'] = [flow.edge('Welcome')]
    groups = json.loads((PKG/'config/major_groups.json').read_text(encoding='utf-8'))['groups']
    group_ids = list(groups)
    group_options = []
    for index, (gid, group) in enumerate(groups.items(), 1):
        label = group['display_name']
        if gid == 'boqin_info':
            label = '卓越拔尖计划伯芩班（计算机、智能科学、光电组）'
        elif gid == 'boqin_science':
            label = '卓越拔尖计划伯芩班（物理、量子信息、化学、生物组）'
        group_options.append(('class%02d'%index, gid, label))
    group_options += [('class09', 'unknown', '不清楚，或者暂不提供'),
                      ('class10', 'finish', '先不做了')]
    flow.buttons('Group', [('GroupGate', 'if01')],
        '## 先记一下你当前的大类\n\n你现在属于下面哪一个大类？这只用于区分类内选择和跨类兴趣，并决定待会给你看哪些情境。\n\n*不清楚也能继续体验，不会据此判断你适合什么。*', group_options, [])
    group_picks = []
    for index, gid in enumerate(group_ids+['unknown'], 1):
        group_picks.append(_v4_copy(flow, 'GroupPick'+str(index),
            ('Group', 'class%02d'%index), 'InitSelection', [('selection_json', 0)], {'group_id': gid}))
    flow.merge('GroupPickMerge', group_picks, [('selection_json', 0), ('group_id', 0)])
    flow.engine('SetGroup', ['GroupPickMerge'], 'set_group',
        [flow.ref(k, 'GroupPickMerge', k) for k in ['selection_json', 'group_id']])
    known = _v4_copy(flow, 'KnownGroup', ('GroupGate', 'else'), 'InitSelection')
    flow.merge('ProfileReady', ['SetGroup', known], _V4_FIELDS)
    _v4_exit(flow, 'GroupFinish', ('Group', 'class10'), 'InitSelection', selection=True)
    _v4_exit(flow, 'GroupOther', ('Group', 'class_other'), 'InitSelection', selection=True)
    flow.engine('PrepareCases', ['ProfileReady'], 'prepare_cases',
        [flow.ref('selection_json', 'ProfileReady', 'selection_json')])
    flow.condition('ActivityGate', 'PrepareCases', [('if01', [('action', 'need_activity')])])
    flow.condition('ActivityGroupSwitch', 'PrepareCases',
        [('if%02d'%i, [('group_id', gid)]) for i, gid in enumerate(group_ids, 1)])
    flow.nodes['ActivityGroupSwitch']['Depends'] = [flow.edge('ActivityGate', 'if01')]
    menu_specs = group_ids + ['unknown']
    activity_picks = []
    for index, gid in enumerate(menu_specs, 1):
        dep = ('ActivityGroupSwitch', 'if%02d'%index) if gid != 'unknown' else ('ActivityGroupSwitch', 'else')
        fams = GROUP_FAMILIES.get(gid, DEFAULT_MENU_FAMILIES)
        node_name = 'Activity' if gid == 'unknown' else 'Activity_' + gid
        options = [('class%02d'%j, fam, FAMILY_LABELS[fam]) for j, fam in enumerate(fams, 1)]
        options.append(('class%02d'%(len(fams)+1), 'random', '随机挑一类'))
        options.append(('class%02d'%(len(fams)+2), 'finish', '先不做了'))
        question = ('## 想从哪种小问题开始？\n\n下面只列出和你大类直接相关的方向；选一个你愿意试试的就好。'
                    '它不是专业选择，想试别的方向也可以直接告诉我名字。\n\n*不需要基础；随机挑一类的话，系统会从这些方向里替你抽一个。*'
                    if gid != 'unknown' else
                    '## 想从哪种小问题开始？\n\n你还没有确认大类，先给你看各类里最常见的几个方向；选一个愿意试试的就好。\n\n*不需要基础；随机挑一类的话，系统会替你抽一个。*')
        flow.buttons(node_name, [dep], question, options, [])
        for j, fam in enumerate(fams, 1):
            activity_picks.append(_v4_copy(flow, 'ActivityPick_%s_%s' % (gid, fam),
                (node_name, 'class%02d'%j), 'PrepareCases', [('selection_json', 0)], {'task_id': fam}))
        activity_picks.append(_v4_copy(flow, 'ActivityPick_%s_random' % gid,
            (node_name, 'class%02d'%(len(fams)+1)), 'PrepareCases', [('selection_json', 0)], {'task_id': 'random'}))
        _v4_exit(flow, 'ActivityFinish_%s' % gid, (node_name, 'class%02d'%(len(fams)+2)), 'PrepareCases', selection=True)
        _v4_exit(flow, 'ActivityOther_%s' % gid, (node_name, 'class_other'), 'PrepareCases', selection=True)
    flow.merge('ActivityPickMerge', activity_picks, [('selection_json', 0), ('task_id', 0)])
    flow.engine('SetActivity', ['ActivityPickMerge'], 'set_activity',
        [flow.ref(k, 'ActivityPickMerge', k) for k in ['selection_json', 'task_id']])
    selected = _v4_copy(flow, 'ActivityAlreadySelected', ('ActivityGate', 'else'), 'PrepareCases')
    flow.merge('MenuReady', ['SetActivity', selected], _V4_FIELDS)
    flow.condition('MenuGate', 'MenuReady', [('if01', [('ok', True)])])
    _v4_exit(flow, 'MenuError', ('MenuGate', 'else'), 'MenuReady', selection=True)
    flow.buttons('CaseSelect', [('MenuGate', 'if01')],
        '{{menu}}\n\n这次只做其中一个情境；之后可以再试其他的。',
        [('class01', 'case1', '{{case1}}'), ('class02', 'case2', '{{case2}}'),
         ('class03', 'case3', '{{case3}}'), ('class04', 'random', '随机挑一个'),
         ('class05', 'finish', '先不做了')],
        [flow.ref('menu', 'MenuReady', 'prompt')] +
        [flow.ref('case'+str(i), 'MenuReady', 'case'+str(i)) for i in range(1, 4)])
    case_picks = []
    for index in range(3):
        case_picks.append(_v4_copy(flow, 'CasePick'+str(index+1),
            ('CaseSelect', 'class0'+str(index+1)), 'MenuReady', [('selection_json', 0)], {'case_index': index}))
    case_picks.append(_v4_copy(flow, 'CasePickRandom',
        ('CaseSelect', 'class04'), 'MenuReady', [('selection_json', 0)], {'case_index': -1}))
    flow.merge('CasePickMerge', case_picks, [('selection_json', 0), ('case_index', 1)])
    flow.engine('StartCase', ['CasePickMerge'], 'select_case',
        [flow.ref(k, 'CasePickMerge', k) for k in ['selection_json', 'case_index']])
    flow.condition('StartGate', 'StartCase', [('if01', [('ok', True)])])
    _v4_exit(flow, 'CaseFinish', ('CaseSelect', 'class05'), 'MenuReady', selection=True)
    _v4_exit(flow, 'CaseOther', ('CaseSelect', 'class_other'), 'MenuReady', selection=True)
    _v4_exit(flow, 'StartError', ('StartGate', 'else'), 'MenuReady', selection=True)
    if with_kb:
        context = add_knowledge(flow, 'KBBridge', [('StartGate', 'if01')], 'StartCase', 'knowledge_query')
        checked = add_grounded_answer(flow, 'Bridge', [context], 'StartCase',
            'knowledge_query', 'KBBridge', context, True)
        flow.message('BridgeMessage', [checked], '{{text}}', [flow.ref('text', checked, 'final_text')])
    else:
        flow.message('BridgeMessage', [('StartGate', 'if01')],
            '*这是一个合成教学情境，只体验专业可能用到的一种方法。做完后可以继续了解相关专业的课程和实际工作。*', [])
    base, base_message, _ = add_phase(flow, 'B', 'StartCase', before='BridgeMessage')
    flow.buttons('AfterFirst', [base_message],
        '## 还想继续看看吗？\n\n接下来会改变一个条件，看看原来的做法还是否合适。也可以就到这里，整理已经完成的记录。',
        [('class01', 'continue', '换个条件，再试一次'),
         ('class02', 'finish', '到这里，去整理记录')], [])
    flow.engine('Advance', [('AfterFirst', 'class01')], 'advance',
        [flow.ref('state_json', base, 'state_json')])
    flow.condition('AdvanceGate', 'Advance', [('if01', [('ok', True)])])
    flow.message('ChangeFeedback', [('AdvanceGate', 'if01')],
        '## 条件变了\n\n{{feedback}}', [flow.ref('feedback', 'Advance', 'feedback')])
    _v4_exit(flow, 'AfterFirstFinish', ('AfterFirst', 'class02'), base)
    _v4_exit(flow, 'AfterFirstOther', ('AfterFirst', 'class_other'), base,
        '这次先到这里，下面是已经完成的记录。')
    _v4_exit(flow, 'AdvanceError', ('AdvanceGate', 'else'), base,
        '后续条件暂时没有展开，已完成的尝试仍会保留。')
    revised, revised_message, _ = add_phase(flow, 'V', 'Advance', before='ChangeFeedback')
    # VDoneExit is registered as a state exit, so it must expose the same fields
    # StateExitMerge aggregates from every exit. The empty constant is deliberately
    # omitted from InputVariables (the platform rejects "" constants); the adapter
    # code already returns "" for it, keeping the aggregator group non-empty.
    _v4_copy(flow, 'VDoneExit', revised_message, revised, [('state_json', 0)],
             {'finish_notice': ''})
    flow._v4_state_exits.append('VDoneExit')

    flow.merge('SelectionExitMerge', flow._v4_selection_exits,
        [('selection_json', 0), ('user_text', 0)])
    flow.engine('SelectionFinish', ['SelectionExitMerge'], 'selection_finish',
        [flow.ref(k, 'SelectionExitMerge', k) for k in ['selection_json', 'user_text']])
    flow.buttons('SelectionGate', ['SelectionFinish'],
        '## 要结束这次体验吗？\n\n还没有开始具体情境。确认的话，我会把这份只有大类信息的记录给你；也可以先不结束。',
        [('class01', 'confirm', '确认结束，把记录给我'),
         ('class02', 'hold', '我再想想')], [])
    flow.terminal('SelectionTerminal', ('SelectionGate', 'class01'), 'SelectionFinish', 'display_text')
    flow.code('SelectionHoldTerminal', [('SelectionGate', 'class02'), ('SelectionGate', 'class_other')],
        [flow.val('text', '好的，那先不结束。想继续体验时，随时告诉我一声就好。'),
         flow.val('fallback', '好的，随时继续。')],
        SUPPORT+'\ndef handler(params):\n    return terminal_text(params)\n', [('final_text', 0)])
    flow.merge('StateExitMerge', flow._v4_state_exits,
        [('state_json', 0), ('finish_notice', 0)])
    flow.engine('StateFinish', ['StateExitMerge'], 'finish',
        [flow.ref(k, 'StateExitMerge', k) for k in ['state_json', 'finish_notice']])
    gate_terminals = _add_report_gate(flow)
    flow.end_merge(['SelectionTerminal', 'SelectionHoldTerminal'] + gate_terminals)
    flow.description = ('专业体验v4：收到请求直接进入；复用本人已明确的大类，未知时只问一次。'
        '大类确定后，活动菜单只列出与该大类直接相关的方向（另有随机入口；明确点名的其他方向仍可从对话进入）。'
        '14类42个合成情境：9类原数量方法 + 叙事两难、价值排序、优先级听证、一天拼图、失败复盘5类非算术情景，'
        '支持情境表面细节随种子确定性地变化。任何结束出口都先经过明确的“是否整理记录”确认门，'
        '想法记录入口在确认门中显式提供；只保留本人确认方案的结果，不打分、不排名、不判断适合程度。'
        + ('包含知识库方法解释。' if with_kb else '离线固定情境版。'))
    return flow.save(name+'.yaml')


def build_knowledge_workflow(draft=False):
    flow=Flow('WF_KB_Practice_Draft_v2' if draft else 'WF_Major_Knowledge_v2',True)
    config=flow.add('Start','Start')
    schema=[{'Name':'query','Type':0,'Required':True,'Desc':'具体专业、相近专业比较、概念解释或开放练习需求；不传学生身份或可信状态。'}]
    config.update(InputSchema=schema,OutputSchema=copy.deepcopy(schema))
    context=add_knowledge(flow,'Knowledge',['Start'],'Start','query')
    if draft:
        flow.llm('DraftLLM',[context],DRAFT_SYSTEM,'练习需求：{{query}}\n命中正文：{{context}}\n检索状态：{{note}}',
                 [flow.ref('query','Start','query'),flow.ref('context',context,'context'),flow.ref('note',context,'retrieval_note')],2200)
        flow.code('DraftCheck',['DraftLLM'],[flow.ref('draft','DraftLLM','raw_output'),flow.ref('hits','Knowledge','outputList')],
                  SUPPORT+'\ndef handler(params):\n    return validate_practice_draft(params)\n',[('ok',2),('final_text',0),('draft_json',0)])
        last='DraftCheck'
    else:
        last=add_grounded_answer(flow,'Answer',[context],'Start','query','Knowledge',context)
    config=flow.add('End','End',[last])
    config.update(OutputType='Variable',InputVariables=[flow.ref('final_text',last,'final_text')])
    flow.description=('根据实际知识库概念生成开放练习草稿；代码检查结构、检索原文与来源，不自动评分、不进入固定题库，学科正确性待审核。' if draft else
                      '专业日常、相近专业比较、概念与学习资料问答；保留来源年级，回答经命中引文/URL检查，不判个人分流资格或适配分数。')
    return flow.save('WF_KB_Practice_Draft_v2.yaml' if draft else 'WF_Major_Knowledge_v2.yaml')


if __name__=='__main__':
    files=[build_explore(True),build_explore(False),build_knowledge_workflow(False),build_knowledge_workflow(True)]
    print(json.dumps([{'file':p.name,'bytes':p.stat().st_size} for p in files],ensure_ascii=False))
