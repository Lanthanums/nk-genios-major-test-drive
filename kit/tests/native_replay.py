"""Independent evaluator for native workflow YAML (not a platform emulator).

Reads the actual exported graph and embedded Python. Models/retrieval and user
actions are explicit fixtures. It never imports a workflow builder. The real
button sample proves CondID port routing and OptionID/OptionContent structure;
the UI screenshot documents lowercase optionId/optionContent output fields.
USER_RESPONSE for buttons is modelled as the rendered label, not the option ID.
The platform's runtime response envelope still needs a live import check.
"""
from dataclasses import dataclass
from pathlib import Path
import copy
import json
import re
import yaml


@dataclass
class Button:
    """Explicit click by native OptionID or CondID; never guess from user prose."""
    option_id: str = ''
    cond_id: str = ''


@dataclass
class FreeText:
    text: str


def refs(value):
    if isinstance(value, dict):
        if value.get('RefType') == 'node_field':
            yield value
        for child in value.values():
            yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


def output_fields(node):
    kind, c = node['Type'], node['Configs'][node['Type']]
    if kind == 'InformationGathering':
        extracted = {x['Name'] for x in c.get('ExtractSchema', [])}
        # The supplied UI documents only these option fields. Platform probe
        # WF_Probe_OptionText (2026-10-17) confirmed the Others branch does NOT
        # expose the typed text, so graphs must never read button USER_RESPONSE.
        return extracted | ({'optionId', 'optionContent'} if c['AnswerType'] == 'option' else {'USER_RESPONSE'})
    if kind == 'VariableMerge':
        return {x['Name'] for x in c['Groups']}
    if kind in {'Message', 'Condition'}:
        return set()
    if kind == 'End':
        return {x['Name'] for x in c.get('InputVariables', [])}
    return {x['Name'] for x in c.get('OutputSchema', [])}


class Workflow:
    def __init__(self, path):
        self.path = Path(path)
        self.data = yaml.safe_load(self.path.read_text(encoding='utf-8'))
        self.nodes = {n['Code']: n for n in self.data['Nodes']}
        self.named = {n['Name']: n for n in self.nodes.values()}
        assert len(self.nodes) == len(self.data['Nodes']) == len(self.named)
        self.order, self.ancestors = [], {}
        pending, seen = dict(self.nodes), set()
        while pending:
            ready = [n for n in pending.values() if all(d['NodeCode'] in seen for d in n.get('Depends', []))]
            assert ready, 'Cycle or unknown dependency'
            for n in ready:
                self.order.append(n)
                seen.add(n['Code'])
                pending.pop(n['Code'])
                ancestors = set()
                for d in n.get('Depends', []):
                    ancestors |= {d['NodeCode']} | self.ancestors[d['NodeCode']]
                self.ancestors[n['Code']] = ancestors
        self.functions = {}
        for n in self.nodes.values():
            if n['Type'] == 'Code':
                namespace = {'__name__': 'independent_native_node'}
                exec(compile(n['Configs']['Code']['Code'], n['Name'], 'exec'), namespace)
                self.functions[n['Code']] = namespace['handler']

    def check(self):
        assert self.data['DLVersion'] == 'v2'
        assert sum(n['Type'] == 'Start' for n in self.nodes.values()) == 1
        assert sum(n['Type'] == 'End' for n in self.nodes.values()) == 1
        for n in self.nodes.values():
            kind, c = n['Type'], n['Configs'][n['Type']]
            for d in n.get('Depends', []):
                upstream = self.nodes[d['NodeCode']]
                if 'PortID' in d:
                    if upstream['Type'] == 'Condition':
                        u = upstream['Configs']['Condition']
                        ports = {b['ID'] for b in u['IfBranches']} | {u['ElseBranch']['ID']}
                    else:
                        assert upstream['Type'] == 'InformationGathering', (n['Name'], 'invalid port source')
                        u = upstream['Configs']['InformationGathering']
                        assert u['AnswerType'] == 'option'
                        ports = {o['CondID'] for o in u['OptionConfig']['Options']}
                    assert d['PortID'] in ports, (n['Name'], d)
            for ref in refs(c):
                assert ref['NodeCode'] in self.ancestors[n['Code']], (n['Name'], 'reference not upstream', ref)
                assert ref['Path'].split('.')[0] in output_fields(self.nodes[ref['NodeCode']]), (n['Name'], 'bad output reference', ref)
            if kind in {'InformationGathering', 'Message', 'LLM'}:
                if kind == 'InformationGathering':
                    text = c['QuestionTemplate']
                    if c['AnswerType'] == 'option':
                        text += '\n' + '\n'.join(o['OptionContent'] for o in c['OptionConfig']['Options'])
                    variables = c.get('TemplateVars', [])
                elif kind == 'Message':
                    text, variables = c['Content'], c.get('InputVariables', [])
                else:
                    text, variables = c.get('SystemPrompt', '') + c['Prompt'], c.get('InputVariables', [])
                assert set(re.findall(r'{{\s*([\w]+)\s*}}', text)) == {v['Name'] for v in variables}, (n['Name'], 'template binding mismatch')
            if kind == 'InformationGathering' and c['AnswerType'] == 'option':
                assert c['OptionConfig']['OptionType'] == 'solid'
                opts = c['OptionConfig']['Options']
                assert len({o['CondID'] for o in opts}) == len(opts)
                assert len({o['OptionID'] for o in opts}) == len(opts)
                assert any(o['CondID'] == 'class_other' for o in opts)
                assert all(o.get('OptionContent') for o in opts)
        return True


class Replay:
    def __init__(self, workflow, answers, start=None, knowledge=None, models=None):
        self.workflow, self.answers = workflow, answers
        self.start, self.knowledge = start or {}, knowledge or []
        self.models = models or {}
        self.values, self.ports, self.trace = {}, {}, []

    def resolve(self, variable):
        if variable['RefType'] == 'value':
            return json.loads(variable['JsonValue'])
        value = self.values[variable['NodeCode']]
        path = variable['Path']
        if path in value:
            return value[path]
        for component in path.split('.'):
            value = value[int(component)] if isinstance(value, list) else value[component]
        return value

    def params(self, variables):
        return {v['Name']: self.resolve(v) for v in variables}

    def render(self, template, variables):
        values = self.params(variables)
        return re.sub(r'{{\s*(\w+)\s*}}', lambda m: str(values[m[1]]), template)

    def gathering(self, n, c, detail):
        name, code = n['Name'], n['Code']
        detail['question'] = self.render(c['QuestionTemplate'], c.get('TemplateVars', []))
        action = self.answers[name]
        if c['AnswerType'] != 'option':
            raw = action.text if isinstance(action, FreeText) else action
            assert isinstance(raw, str), (name, action)
            return {'USER_RESPONSE': raw, 'unused_ack': 'received'}
        opts = [{**o, 'OptionContent': self.render(o['OptionContent'], c.get('TemplateVars', []))}
                for o in c['OptionConfig']['Options']]
        detail['buttons'] = [o for o in opts if o['CondID'] != 'class_other']
        if isinstance(action, dict):
            action = Button(option_id=action.get('OptionID', action.get('option_id', '')),
                            cond_id=action.get('CondID', action.get('cond_id', ''))) if any(
                                k in action for k in ['OptionID','option_id','CondID','cond_id']) else FreeText(action['text'])
        if isinstance(action, Button):
            matches = [o for o in opts if ((not action.option_id or o['OptionID'] == action.option_id)
                                           and (not action.cond_id or o['CondID'] == action.cond_id))]
            assert len(matches) == 1, (name, action, opts)
            selected = matches[0]
            assert selected['CondID'] != 'class_other', 'Use FreeText for non-visible Others branch'
            raw = selected['OptionContent']
        else:
            raw = action.text if isinstance(action, FreeText) else action
            assert isinstance(raw, str), (name, action)
            selected = next(o for o in opts if o['CondID'] == 'class_other')
        self.ports[code] = selected['CondID']
        detail['selected_port'] = selected['CondID']
        detail['user_action'] = {'OptionID': selected['OptionID'], 'CondID': selected['CondID'], 'raw': raw}
        content = selected['OptionContent'] if selected['CondID'] != 'class_other' else raw
        return {'USER_RESPONSE': raw, 'optionId': selected['OptionID'], 'optionContent': content,
                'OptionID': selected['OptionID'], 'OptionContent': content, 'unused_ack': 'received'}

    def model(self, name, c):
        p = self.params(c.get('InputVariables', []))
        assert name in self.models, ('Model requires explicit fixture', name)
        fixture = self.models[name]
        out = fixture(p, self) if callable(fixture) else fixture
        return out if isinstance(out, dict) and 'raw_output' in out else {'raw_output': json.dumps(out, ensure_ascii=False) if isinstance(out, dict) else out}

    def run(self):
        for n in self.workflow.order:
            code, name, kind = n['Code'], n['Name'], n['Type']
            deps = n.get('Depends', [])
            active = [d for d in deps if d['NodeCode'] in self.values and ('PortID' not in d or self.ports.get(d['NodeCode']) == d['PortID'])]
            if kind != 'Start' and not (bool(active) if kind == 'VariableMerge' else len(active) == len(deps)):
                continue
            c, detail = n['Configs'][kind], {}
            try:
                if kind == 'Start':
                    out = {f['Name']: '' for f in c.get('InputSchema', [])}
                    out.update(self.start)
                elif kind == 'InformationGathering':
                    out = self.gathering(n, c, detail)
                elif kind == 'LLM':
                    detail['prompt'] = self.render(c['Prompt'], c.get('InputVariables', []))
                    out = self.model(name, c)
                elif kind == 'Knowledge':
                    detail['query'] = self.resolve(c['QueryVariable'])
                    out = {'outputList': copy.deepcopy(self.knowledge), 'filter': ''}
                elif kind == 'Code':
                    detail['input'] = self.params(c.get('InputVariables', []))
                    out = self.workflow.functions[code](detail['input'])
                    for f in c.get('OutputSchema', []):
                        assert f['Name'] in out, (name, 'missing output', f['Name'])
                        value, typ = out[f['Name']], f['Type']
                        assert (isinstance(value, str) if typ == 0 else type(value) is bool if typ == 2 else type(value) is int if typ == 1 else True), (name, f, value)
                elif kind == 'Message':
                    detail['message'] = self.render(c['Content'], c.get('InputVariables', []))
                    out = {}
                elif kind == 'Condition':
                    port = c['ElseBranch']['ID']
                    for b in c['IfBranches']:
                        checks = []
                        for cond in b['Conditions']:
                            assert cond['Operator'] == 'EQ', cond
                            checks.append(self.resolve(cond['Left']) == self.resolve(cond['Right']))
                        if (all(checks) if b['ConditionLogic'] == 'AND' else any(checks)):
                            port = b['ID']
                            break
                    self.ports[code] = port
                    detail['selected_port'] = port
                    out = {}
                elif kind == 'VariableMerge':
                    out = {}
                    for group in c['Groups']:
                        available = [v for v in group['Variables'] if v['NodeCode'] in self.values]
                        assert len(available) == 1, (name, group['Name'], 'available', len(available))
                        out[group['Name']] = self.resolve(available[0])
                elif kind == 'End':
                    out = self.params(c.get('InputVariables', []))
                else:
                    raise AssertionError(('Unsupported node type', kind))
            except Exception as exc:
                raise AssertionError(('Node execution failed', name, kind, str(exc))) from exc
            self.values[code] = out
            self.trace.append({'node': name, 'type': kind, **detail, 'output': copy.deepcopy(out)})
        end = next(n for n in self.workflow.nodes.values() if n['Type'] == 'End')
        assert end['Code'] in self.values, ('End not reached', [x['node'] for x in self.trace])
        self.final = self.values[end['Code']].get('final_text', '')
        assert isinstance(self.final, str) and self.final.strip(), 'Empty final_text'
        return self

    def result(self, name):
        return self.values[self.workflow.named[name]['Code']]

    def rendered_texts(self):
        return [x[k] for x in self.trace for k in ['question','message'] if k in x] + [self.final]
