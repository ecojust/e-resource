#!/usr/bin/env python3
"""Compare the reviewed effective31 runtime in MAIN, an actual ZIP and its extraction."""
import argparse
import hashlib
import json
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
RUNTIME_DIR = HERE.parent / 'integration/runtime-delta-v1'
sys.path.insert(0, str(RUNTIME_DIR))
import runtime_delta
BASELINE = RUNTIME_DIR / 'effective-runtime31.json'
BASELINE_SHA = '4c10056024d33543ea624087bcd8ed5ff13f7e40b41fd3c96e6ed51e7934bd9b'
RUNTIME_HELPER_SHA = '871d86372cbd9db9d7732f98b42a30977030775e74f53786ac6a20e72c171808'
LIMIT = 100_000_000


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_bytes())


def meta(path):
    path = Path(path)
    with path.open('rb') as stream:
        sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': sha}


def descriptor(path):
    return {'source': str(Path(path).resolve()), **meta(path)}


def baseline():
    need(meta(runtime_delta.__file__)['sha256'] == RUNTIME_HELPER_SHA, 'Reviewed runtime helper changed')
    need(meta(BASELINE)['sha256'] == BASELINE_SHA, 'The exact reviewed effective31 runtime baseline is required')
    inputs, delta, value = runtime_delta.load_inputs()
    need(inputs['effective_runtime_baseline'] == descriptor(BASELINE), 'Runtime evidence uses another baseline')
    rows = value['files']
    need(value['schema'] == 'modern-app-immutable-runtime-baseline-v11'
         and len(rows) == len({row['file'] for row in rows}) == 31,
         'Expected the actual31-file runtime baseline')
    return value


def runtime_tree(root, value):
    root = Path(root).resolve()
    rows = value['files']
    actual_names = {p.relative_to(root).as_posix() for p in (root / 'src').rglob('*') if p.is_file()}
    need(actual_names == {row['file'] for row in rows}, 'Runtime filename inventory changed')
    for row in rows:
        need(meta(root / row['file']) == {key: row[key] for key in ('bytes', 'sha256')},
             'Runtime bytes changed: ' + row['file'])


def archive_identity(archive, proof_path):
    proof = read(proof_path)
    need(proof.get('passed') is True and proof.get('publishable') is True
         and proof.get('candidate_only') is False and proof.get('landmarks') == 30
         and proof.get('paths_safe_for_extraction') is True
         and proof.get('manifest_byte_sha256_match') is True
         and proof.get('zip_crc_streams_verified', 0) == proof.get('extraction', {}).get('files_verified', -1),
         'Actual30 ZIP/extraction proof required')
    identity = meta(archive)
    need(0 < identity['bytes'] < LIMIT
         and identity == {'bytes': proof['archive_bytes'], 'sha256': proof['archive_sha256']},
         'Actual ZIP bytes differ from archive proof')
    return proof


def validate_runtime_proof(path, archive, archive_proof, extracted):
    """Read-only smoke preflight; rebind the actual prior comparison and current files."""
    report = read(path)
    need(report.get('schema') == 'sihang30-actual-runtime-archive-match-v12-runtime-delta'
         and report.get('passed') is True and report.get('runtime_files_verified') == 31
         and report.get('all_three_runtime_trees_identical') is True,
         'Actual31 runtime archive comparison is required before launcher smoke')
    need(report['checker'] == descriptor(__file__)
         and report['runtime_baseline'] == descriptor(BASELINE)
         and report['archive'] == descriptor(archive)
         and report['archive_proof'] == descriptor(archive_proof),
         'Runtime report inputs or checker changed')
    proof = archive_identity(archive, archive_proof)
    actual_extracted = Path(proof['extraction']['path']).resolve() / 'shanghai'
    need(Path(extracted).resolve() == actual_extracted == Path(report['extracted']).resolve(),
         'Runtime report belongs to another extraction')
    value = baseline()
    need(report.get('reviewed_runtime_delta') == runtime_delta.evidence_record()
         and report.get('runtime_files_unchanged_from_v11') == 30, 'Runtime review binding changed')
    runtime_tree(actual_extracted, value)
    runtime_tree(report['project'], value)
    return {'report': descriptor(path), 'runtime_baseline': descriptor(BASELINE),
            'archive': descriptor(archive), 'archive_proof': descriptor(archive_proof),
            'runtime_files_verified': 31, 'extracted_runtime_rechecked_before_smoke': True,
            'reviewed_runtime_delta': runtime_delta.evidence_record(),
            'runtime_files_unchanged_from_v11': 30,
            'scope': 'Actual archive and extracted file bytes; served31 HTTP bytes are not separately requested by this single-load smoke.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'archive', 'archive-proof', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    need(output.is_relative_to(HERE) and output != HERE and not output.exists()
         and not args.output.is_symlink(), 'Use a NEW V12 launcher report')
    value = baseline()
    proof = archive_identity(args.archive, args.archive_proof)
    extracted = Path(proof['extraction']['path']).resolve() / 'shanghai'
    runtime_tree(args.project, value)
    runtime_tree(extracted, value)
    with zipfile.ZipFile(args.archive) as archive:
        for row in value['files']:
            body = archive.read('shanghai/' + row['file'])
            need({'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
                 == {key: row[key] for key in ('bytes', 'sha256')},
                 'Archived runtime bytes changed: ' + row['file'])
    archive_identity(args.archive, args.archive_proof)
    report = {'schema': 'sihang30-actual-runtime-archive-match-v12-runtime-delta', 'passed': True,
              'runtime_files_verified': 31, 'archive': descriptor(args.archive),
              'archive_proof': descriptor(args.archive_proof), 'runtime_baseline': descriptor(BASELINE),
              'checker': descriptor(__file__), 'project': str(args.project.resolve()),
              'extracted': str(extracted), 'all_three_runtime_trees_identical': True,
              'browser_run': False, 'runtime_modified': True,
              'reviewed_runtime_delta': runtime_delta.evidence_record(),
              'runtime_files_unchanged_from_v11': 30}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'report': descriptor(output), 'runtime_files_verified': 31, 'browser_run': False}, indent=2))


if __name__ == '__main__':
    main()
