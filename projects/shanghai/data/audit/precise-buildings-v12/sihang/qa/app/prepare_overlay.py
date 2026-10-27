#!/usr/bin/env python3
"""Prepare an isolated read-only-linked project; never install a candidate plan."""
import argparse
import json
import os
from pathlib import Path
import shutil
from prepare_sihang import HERE, BASE_APP, INTEGRATION, runtime_delta, context, encoded, meta, need, read, referenced


def descriptor(path):
    return {'source': str(Path(path).resolve()), **meta(path)}

WRITABLE_METADATA = ('data/precise-buildings/', 'data/precise-candidates/')
WRITABLE_FILES = {'data/landmarks.json', 'data/precise-buildings-v6.json', 'data/districts.json'}
IMMUTABLE_DIRECTORY_LINKS = {'assets/city', 'assets/city-detail'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--create', action='store_true')
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    output = args.output.resolve()
    report_path = args.report.resolve()
    need(output.is_relative_to(HERE) and output != HERE and output.parent.is_dir()
         and not output.exists() and not args.output.is_symlink()
         and not output.is_relative_to(project),
         'Overlay must be a NEW isolated child of V12 integration/app-v1 outside the source project')
    need(report_path.parent.is_relative_to(HERE) and not report_path.is_relative_to(output)
         and not report_path.is_relative_to(project) and not report_path.exists()
         and not args.report.is_symlink(), 'Report must be a NEW path inside app stage outside the source project')
    plan = read(args.plan)
    need(plan.get('schema') == 'sihang-candidate30-plan-v1'
         and plan.get('status') == 'prepared_static_browser_pending', 'Actual Sihang candidate30 plan required')
    referenced(plan['spec'])
    lock, *_ = context(project)
    baseline_lock = meta(BASE_APP / 'inputs.lock.json')
    need(plan['baseline_lock'] == baseline_lock, 'Candidate baseline differs')
    need(plan['qa_tools_lock'] == meta(HERE / 'qa-tools.lock.json'), 'Candidate QA lock differs')
    baseline = read(INTEGRATION / 'minimal-tools-v1/baseline-lock.json')
    runtime_source = baseline['runtime_baseline_source']
    runtime = read(referenced(runtime_source))
    need(runtime['files'] == lock['runtime_files'] and len(runtime['files']) == 31,
         'Actual31 runtime baseline differs')
    need(plan.get('runtime_delta') == runtime_delta.evidence_record(), 'Candidate runtime evidence differs')
    need([row for row in plan['files'] if row['file'].startswith('src/')]
         == [runtime_delta.plan_entry(project)], 'Candidate must contain only the exact reviewed map-scene delta')
    for row in plan['files']:
        referenced({key: row[key] for key in ('source', 'bytes', 'sha256')})
        rel = Path(row['file'])
        need(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe candidate path')
        target = project / rel
        previous = meta(target) if target.is_file() else None
        need(previous == row['old_main'],
             'Actual MAIN destination differs: ' + row['file'])
    directories, directory_links, file_rows = [], [], []
    for base, dirs, files in os.walk(project, followlinks=False):
        dirs.sort()
        files.sort()
        for name in list(dirs):
            source = Path(base) / name
            rel = source.relative_to(project).as_posix()
            if rel in IMMUTABLE_DIRECTORY_LINKS:
                need(source.resolve(strict=True).is_dir(), 'Missing immutable city asset tree: ' + rel)
                directory_links.append((rel, source))
                dirs.remove(name)  # Prune both real and linked large city trees.
            else:
                need(not source.is_symlink(), 'Unexpected project directory symlink: ' + rel)
                directories.append(rel)
        for name in files:
            source = Path(base) / name
            rel = source.relative_to(project).as_posix()
            need(source.is_file(), 'Unexpected non-regular project leaf: ' + rel)
            writable = rel in WRITABLE_FILES or rel.startswith(WRITABLE_METADATA) or rel.startswith('src/')
            file_rows.append((rel, source, writable))
    need({rel for rel, _ in directory_links} == IMMUTABLE_DIRECTORY_LINKS,
         'Both immutable city directories must remain untraversed links')
    need({rel for rel, _, _ in file_rows if rel.startswith('src/')}
         == {row['file'] for row in lock['runtime_files']}, 'Actual runtime filename inventory differs')
    need(all(any(rel == required and writable for rel, _, writable in file_rows)
             for required in WRITABLE_FILES), 'Required separate metadata files missing')
    copied_bytes = sum(source.stat().st_size for _, source, writable in file_rows if writable)
    need(copied_bytes < 10_000_000, 'Unexpected metadata materialization size')
    report = {'schema': 'sihang-isolated-overlay-v12', 'passed': True,
              'created': args.create, 'main_written': False, 'candidate_plan_installed': False,
              'browser_run': False, 'model_acceptance_claimed': False,
              'project': str(project), 'output': str(output), 'candidate_plan': descriptor(args.plan),
              'helper': descriptor(__file__), 'baseline_lock': baseline_lock,
              'runtime_baseline': runtime_source, 'runtime_delta': runtime_delta.evidence_record(),
              'real_directory_count': len(directories),
              'immutable_directory_links': [rel for rel, _ in directory_links],
              'linked_file_count': sum(not writable for _, _, writable in file_rows),
              'materialized_writable_file_count': sum(writable for _, _, writable in file_rows),
              'materialized_writable_file_bytes': copied_bytes,
              'scope': 'All ordinary directories are real overlay directories. Only two immutable external city asset trees retain directory links. Existing navigation/registry/districts, ordinary catalog/candidate metadata and all31 unchanged runtime files are separate copies. This helper does not install the plan. Other immutable leaves link to MAIN; the reviewed installer replaces changed leaves atomically. Never run an in-place editor against linked leaves.'}
    if args.create:
        output.mkdir()
        for rel in sorted(directories, key=lambda value: (len(Path(value).parts), value)):
            (output / rel).mkdir()
        for rel, source in directory_links:
            (output / rel).symlink_to(source, target_is_directory=True)
        for rel, source, writable in file_rows:
            target = output / rel
            if writable:
                shutil.copyfile(source, target)
                need(not target.is_symlink() and meta(target) == meta(source), 'Copied metadata differs: ' + rel)
            else:
                target.symlink_to(source)
        for row in plan['files']:
            if row['file'].startswith('data/'):
                target = output / row['file']
                for parent in target.parents:
                    if parent == output:
                        break
                    if parent.exists():
                        need(not parent.is_symlink(), 'Writable metadata parent is linked: ' + str(parent))
        context(project)
        need(meta(BASE_APP / 'inputs.lock.json') == baseline_lock
             and plan['qa_tools_lock'] == meta(HERE / 'qa-tools.lock.json'),
             'Frozen locks changed while creating overlay')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_bytes(encoded(report))
        print(json.dumps({'report': descriptor(report_path), 'created': True}, indent=2))
    else:
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
