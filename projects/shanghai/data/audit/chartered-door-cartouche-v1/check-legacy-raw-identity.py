"""Exercise the archived Bund 18 identity and reject changes to its location or links."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
RAW = 'data/bund/models/bund18.json'
CHECKER = PROJECT / 'tools/check_bund_revision.py'
check = runpy.run_path(str(CHECKER))['check_raw_registration']


def rejected(before, after, model):
    try:
        check(before, after, model)
    except AssertionError:
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline')
    args = parser.parse_args()
    prefix = PROJECT.relative_to(PROJECT.parents[1]).as_posix()
    original = subprocess.check_output(['git', 'show', f'{args.baseline}:{prefix}/{RAW}'], cwd=PROJECT)
    current = (PROJECT / RAW).read_bytes()
    old, new = json.loads(original), json.loads(current)
    assert old['id'] == 'bund18-chartered-bank' and 'candidateId' not in old and new['candidateId'] == 'bund18'
    check(old, new, 'bund18')
    check(new, new, 'bund18')
    tests = {
        'different canonical landmark': rejected(old, {**new, 'candidateId': 'bund07'}, 'bund18'),
        'unrelated raw model': rejected({**old, 'id': 'another-legacy-model'}, {**new, 'id': 'another-legacy-model'}, 'bund18'),
        'lost alias': rejected(new, old, 'bund18'),
        'different source footprint': rejected(old, {**new, 'source_footprint': None}, 'bund18'),
        'changed original ID': rejected(old, {**new, 'id': 'bund18'}, 'bund18'),
    }
    assert all(tests.values()), tests
    digest = lambda data: hashlib.sha256(data).hexdigest()
    result = dict(passed=True, baseline=args.baseline, original_sha256=digest(original),
                  revised_sha256=digest(current), checker_sha256=digest(CHECKER.read_bytes()), rejected=tests)
    (AUDIT / 'legacy-raw-identity.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
