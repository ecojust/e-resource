"""Exercise count validation against the full frozen Taiwan Bank city and legacy receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('project', type=Path)
parser.add_argument('snapshot', type=Path)
parser.add_argument('checker', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
original = json.loads(args.snapshot.read_bytes())
catalog_path = 'data/candidate-city-integrations.json'
catalog = json.loads((args.project / catalog_path).read_bytes())
assert original['resulting_count'] == catalog['resulting_city_count'] == 153
rows = {}
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    project = root / 'projects/shanghai'
    project.mkdir(parents=True)
    for name, digest in original['files'].items():
        src = args.project / name
        with src.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
        dest = project / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.hardlink_to(src)
    checker_name = 'tools/check_catalog_snapshot.py'
    checker = project / checker_name
    checker.unlink()
    shutil.copyfile(args.checker, checker)
    original['files'][checker_name] = hashlib.sha256(checker.read_bytes()).hexdigest()
    for case, count, success in [('reported_count_matches', 153, True),
                                 ('earlier_incorrect_count', 145, False),
                                 ('legacy_receipt_without_count', None, True)]:
        snapshot = dict(original)
        if count is None:
            snapshot.pop('resulting_count')
        else:
            snapshot['resulting_count'] = count
        inp = root / (case + '-input.json')
        out = root / (case + '-receipt.json')
        inp.write_text(json.dumps(snapshot))
        check = subprocess.run([sys.executable, '-B', checker, inp, out],
                               capture_output=True, text=True)
        assert (check.returncode == 0) == success, (case, check.stderr)
        if success:
            receipt = json.loads(out.read_bytes())
            assert receipt['exact_file_matches'] == len(snapshot['files'])
        else:
            assert 'Snapshot has 145 city entries, catalog has 153' in check.stderr
            assert not out.exists()
        rows[case] = {'reported_count': count, 'exit_code': check.returncode,
                      'receipt_written': out.exists()}
args.output.write_text(json.dumps({
    'passed': True, 'catalog_sha256': original['files'][catalog_path],
    'verified_source_files': len(original['files']), 'city_entries': 153,
    'checker_sha256': original['files'][checker_name], 'cases': rows
}, ensure_ascii=False, indent=2) + '\n')
