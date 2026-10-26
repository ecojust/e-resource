"""Exact reviewed per-building selections; no fallback to another building's tools."""
from pathlib import Path
import json
import re


def need(value, message):
    if not value:
        raise ValueError(message)


def validate_selection(document, targets):
    need(document.get('schema') == 'app-selected-modern-registrar-tools-per-model-v11'
         and document.get('status') == 'FROZEN_REVIEWED_PER_MODEL',
         'Reviewed per-building modern tool selection remains pending or uses the old global schema')
    selected = document.get('selected_freezes')
    need(isinstance(selected, dict) and set(selected) == set(targets)
         and len(targets) == len(set(targets)), 'Exact reviewed modern tool target set required')
    need('selected_freeze' not in document, 'Global modern tool fallback is forbidden')
    for ident, value in selected.items():
        need(isinstance(value, dict) and set(value) == {'source', 'bytes', 'sha256'}
             and isinstance(value['source'], str) and Path(value['source']).is_absolute()
             and type(value['bytes']) is int and 0 < value['bytes'] < 100_000_000
             and isinstance(value['sha256'], str) and re.fullmatch('[0-9a-f]{64}', value['sha256']),
             'Actual reviewed modern tool descriptor required: ' + ident)
    return selected


def load_selection(path, targets, *, actual):
    selected = validate_selection(json.loads(Path(path).read_bytes()), targets)
    for ident, value in selected.items():
        freeze = json.loads(actual(value).read_bytes())
        need(freeze.get('schema') == 'modern-packaging-tool-source-freeze-v11'
             and freeze.get('status') == 'frozen', 'Actual modern tool freeze required: ' + ident)
        rows = freeze.get('files')
        need(isinstance(rows, list) and rows, 'Frozen modern tool dependencies missing: ' + ident)
        sources = []
        for row in rows:
            sources.append(str(actual(row).resolve()))
        need(len(sources) == len(set(sources)), 'Duplicate modern tool dependency: ' + ident)
    return selected


def check_dependencies(dependencies, selected):
    need('modern_tool_source_freeze' not in dependencies,
         'Global modern dependency selection is forbidden')
    need(dependencies.get('modern_tool_source_freezes') == selected,
         'Ready dependencies selected an unreviewed per-building modern tool freeze')


def check_model(model, ident, selected):
    need(ident in selected and model.get('modern_tool_source_freeze') == selected[ident],
         'Model package/registrar tool freeze differs from reviewed building selection: ' + ident)
