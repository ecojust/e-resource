#!/usr/bin/env python3
"""Bind actual delta QA dependencies and completed static evidence; no browser."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
QA = HERE.parent / 'qa'
IDS = ['jingan-sihang-warehouse']
SCHEMA = 'sihang-one-start-keyboard-runtime-delta-source-binding-v12'
OWN_FILES = ('keyboard_smoke.py', 'snapshot.js', 'prepare_source_binding.py',
             'README.md', 'upstream.json', 'patches/keyboard_smoke.py.patch')
RUNTIME_INTERFACES = ('src/walk-controller.js', 'src/map-scene.js',
                      'src/walker-model.js', 'src/app.js')


def need(value, message):
    if not value:
        raise ValueError(message)


def descriptor(path):
    path = Path(path).resolve(strict=True)
    need(path.is_file(), 'Actual regular file required: ' + str(path))
    size = path.stat().st_size
    need(0 < size < 100_000_000, 'File must be nonempty and below 100 MB')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'source': str(path), 'bytes': size, 'sha256': digest}


def actual(row):
    need(isinstance(row, dict) and isinstance(row.get('source'), str),
         'Missing actual file descriptor')
    path = Path(row['source'])
    need(path.is_absolute() and type(row.get('bytes')) is int
         and isinstance(row.get('sha256'), str)
         and re.fullmatch('[0-9a-f]{64}', row['sha256']),
         'Invalid actual file descriptor')
    need(descriptor(path) == {key: row[key] for key in ('source', 'bytes', 'sha256')},
         'Actual source bytes/SHA changed: ' + str(path))
    return path


def read(path):
    return json.loads(Path(path).read_bytes())


def dependencies(path):
    path = Path(path).resolve(strict=True)
    need(path == QA / 'required-dependencies.json',
         'Use this revision exact QA dependency manifest')
    doc = read(path)
    rows = doc.get('files') if isinstance(doc, dict) else None
    need(isinstance(rows, list) and rows, 'Explicit actual QA files are required')
    normalized = [descriptor(actual(row)) for row in rows]
    need(len({row['source'] for row in normalized}) == len(normalized),
         'Duplicate actual QA dependency')
    names = {row['source'] for row in normalized}
    for required in (QA / 'browser-next-v3.py', HERE.parent / 'runtime_delta.py'):
        need(str(required.resolve(strict=True)) in names,
             'Required QA/runtime gate is absent: ' + str(required))
    return sorted(normalized, key=lambda row: row['source'])


def module(path, name):
    before = descriptor(path)
    spec = importlib.util.spec_from_file_location(name, actual(before))
    need(spec is not None and spec.loader is not None, 'Cannot import reviewed gate')
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    actual(before)
    return result


def inspect_inputs(candidate, qa_manifest, expectations, static_browser):
    candidate = Path(candidate).resolve(strict=True)
    need(candidate.is_dir(), 'Actual isolated candidate directory required')
    dependency_rows = dependencies(actual(qa_manifest))
    # These reviewed APIs reject absent/pending vendor proof or root review.
    runtime = module(HERE.parent / 'runtime_delta.py', 'sihang_keyboard_runtime_delta')
    runtime_evidence = runtime.evidence_record()
    effective = runtime.effective_runtime()
    runtime.check_candidate(candidate)
    runtime_files = effective.get('files')
    need(isinstance(runtime_files, list) and len(runtime_files) == 31
         and len({row['file'] for row in runtime_files}) == 31,
         'Exactly 31 effective runtime files are required')
    sys.path.insert(0, str(QA))
    qa = module(QA / 'browser-next-v3.py', 'sihang_keyboard_delta_qa')
    profile = qa.expectations.load_profile(actual(expectations), IDS)
    binding = qa.validate_profile_binding(profile)
    need(qa.check_runtime_binding(binding['runtime_baseline'])['files'] == runtime_files,
         'Profile does not bind the reviewed effective runtime')
    browser_path = actual(static_browser)
    browser = read(browser_path)
    need(browser.get('passed') is True and browser.get('technical_passed') is True
         and isinstance(browser.get('finished_at'), str) and browser['finished_at'],
         'A completed actual static browser pass is required before keyboard smoke')
    need(browser.get('targets') == IDS and browser.get('expected_record_count') == 30
         and browser.get('single_browser') is True and browser.get('reset_only') is False,
         'Actual full static Sihang 30-record scope is required')
    need(browser.get('script_sha256') == descriptor(QA / 'browser-next-v3.py')['sha256'],
         'Static evidence used another browser runner')
    need(browser.get('expectations_sha256') == expectations['sha256']
         and browser.get('expectations') == profile,
         'Static evidence used another exact profile')
    need(browser.get('sihang_input_binding') == binding == profile.get('sihang_input_binding'),
         'Static/profile/runtime/model binding differs')
    need(browser.get('runtime_baseline_sha256') == binding['runtime_baseline']['sha256']
         and browser.get('actual_runtime_file_audit') == {'passed': True, 'files': runtime_files},
         'Actual served 31-file runtime audit differs')
    for key in ('page_errors', 'shader_errors', 'asset_errors', 'request_failures',
                'console_errors', 'external_http_errors'):
        need(browser.get(key) == [], 'Static browser errors: ' + key)
    captures = browser.get('captures')
    need(isinstance(captures, list) and len(captures) == 7,
         'All seven actual static captures are required')
    screenshots = []
    names = set()
    for capture in captures:
        name = capture.get('image')
        shot = capture.get('screenshot_complete') or {}
        need(capture.get('capture_completed') is True and isinstance(name, str)
             and Path(name).name == name and name not in names and shot.get('file') == name,
             'Incomplete, duplicate or unsafe actual static screenshot')
        names.add(name)
        current = descriptor(browser_path.parent / name)
        need({key: current[key] for key in ('bytes', 'sha256')}
             == {key: shot.get(key) for key in ('bytes', 'sha256')},
             'Actual static screenshot bytes/SHA differ')
        screenshots.append(current)
    interfaces = [descriptor(candidate / name) for name in RUNTIME_INTERFACES]
    runtime.check_candidate(candidate)
    need(runtime.evidence_record() == runtime_evidence
         and runtime.effective_runtime() == effective,
         'Reviewed runtime evidence changed during binding')
    need(dependencies(actual(qa_manifest)) == dependency_rows,
         'QA dependency set changed during binding')
    actual(expectations)
    actual(static_browser)
    return {'qa_dependency_files': dependency_rows,
            'runtime_evidence': runtime_evidence, 'effective_runtime_files': runtime_files,
            'runtime_interface_sources': interfaces, 'sihang_input_binding': binding,
            'static_screenshots': screenshots}


def required_files(qa_manifest, expectations, static_browser, observed):
    paths = [HERE / name for name in OWN_FILES]
    paths += [actual(qa_manifest), actual(expectations), actual(static_browser),
              HERE.parent / 'runtime-inputs.actual.json']
    for key in ('qa_dependency_files', 'runtime_interface_sources', 'static_screenshots'):
        paths += [actual(row) for row in observed[key]]
    return [descriptor(path) for path in sorted({Path(path).resolve(strict=True) for path in paths})]


def verify_binding(path, arguments=None):
    path = Path(path).resolve(strict=True)
    need(path == HERE / 'source-binding.json', 'Exact immutable keyboard binding required')
    binding = read(path)
    need(binding.get('schema') == SCHEMA and binding.get('targets') == IDS
         and binding.get('expected_navigation_count') == 30
         and binding.get('expected_attempt_count') == 1,
         'Wrong single-start keyboard binding scope')
    need(binding.get('source_only') is True and binding.get('actual_browser_run') is False
         and binding.get('movement_observed') is False
         and binding.get('technical_pass_claimed') is False,
         'Preparation binding cannot claim keyboard acceptance')
    if arguments is not None:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--expectations', required=True, type=Path)
        selected, _ = parser.parse_known_args(arguments)
        need(descriptor(selected.expectations) == binding['expectations'],
             'Keyboard CLI profile differs from the completed static prerequisite')
    for row in binding.get('required_files', []):
        actual(row)
    observed = inspect_inputs(binding['candidate_root'], binding['qa_dependencies'],
                              binding['expectations'], binding['static_browser'])
    for key, value in observed.items():
        need(binding.get(key) == value, 'Frozen keyboard prerequisite changed: ' + key)
    need(binding.get('required_files') == required_files(binding['qa_dependencies'],
         binding['expectations'], binding['static_browser'], observed),
         'Required keyboard dependency closure differs')
    return binding


def prepare(candidate, qa_dependencies, expectations, static_browser):
    output = HERE / 'source-binding.json'
    need(not output.exists() and not output.is_symlink(), 'Do not overwrite frozen inputs')
    candidate = Path(candidate).resolve(strict=True)
    manifest = descriptor(qa_dependencies)
    profile = descriptor(expectations)
    static = descriptor(static_browser)
    observed = inspect_inputs(candidate, manifest, profile, static)
    binding = {'schema': SCHEMA, 'targets': IDS, 'expected_navigation_count': 30,
               'expected_attempt_count': 1, 'candidate_root': str(candidate),
               'qa_dependencies': manifest, 'expectations': profile, 'static_browser': static,
               **observed, 'required_files': required_files(manifest, profile, static, observed),
               'source_only': True, 'actual_browser_run': False, 'movement_observed': False,
               'technical_pass_claimed': False}
    with output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(binding, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    verify_binding(output)
    return descriptor(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', required=True, type=Path)
    parser.add_argument('--qa-dependencies', type=Path, default=QA / 'required-dependencies.json')
    parser.add_argument('--expectations', required=True, type=Path)
    parser.add_argument('--static-browser', required=True, type=Path)
    args = parser.parse_args()
    result = prepare(args.runtime_root, args.qa_dependencies, args.expectations, args.static_browser)
    print(json.dumps({'source_binding': result, 'browser_run': False,
                      'movement_observed': False, 'technical_pass_claimed': False}, indent=2))


if __name__ == '__main__':
    main()
