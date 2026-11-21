"""Compare a candidate's public catalog response with the scene reviewed for the same release."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
PREFIX = PROJECT.relative_to(REPO).as_posix() + '/'
CATALOG = 'data/candidate-city-integrations.json'


def compare_catalog(report, reviewed_digest):
    catalog, = [r for r in report['records'] if r['path'] == PREFIX + CATALOG]
    result = dict(reviewed_sha256=reviewed_digest, committed_sha256=catalog['expected_sha256'],
                  public_sha256=catalog['response'].get('sha256'))
    result['passed'] = (catalog['matches_commit'] and result['public_sha256'] == reviewed_digest
                        and result['committed_sha256'] == reviewed_digest)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('publication', type=Path, help='JSON written by check_candidate_publication.py')
    parser.add_argument('--output', type=Path, help='Write the publication report with its catalog comparison')
    args = parser.parse_args()
    report = json.loads(args.publication.read_bytes())
    commit = report['commit']
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=REPO)
    if git('rev-parse', '--verify', commit + '^{commit}').decode().strip() != commit:
        raise ValueError('Publication must identify the full model commit')
    rows = json.loads(git('show', commit + ':' + PREFIX + 'data/model-todo/queue.json'))['production_queue']
    job, = [row for row in rows if row['id'] == report['model']]
    snapshot = Path(job['evidence']).with_name('production-snapshot.json').as_posix()
    if git('ls-tree', '--name-only', commit, '--', snapshot).decode().strip() == snapshot:
        frozen = json.loads(git('show', commit + ':' + snapshot))
        comparison = compare_catalog(report, frozen['files'][CATALOG])
        comparison['snapshot'] = snapshot
        comparison['checker_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report['reviewed_city_catalog'] = comparison
        report['passed'] = report['passed'] and comparison['passed']
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'model': report['model'], 'passed': report['passed'],
                      'reviewed_city_catalog': report.get('reviewed_city_catalog')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
