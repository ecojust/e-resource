"""Check the files bound to a rendered map snapshot against a production checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
QUEUE = 'data/model-todo/queue.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def queue_contents(raw):
    queue = json.loads(raw)
    commits = {}
    for row in queue['production_queue']:
        if 'published_commit' in row:
            commits[row['id']] = row.pop('published_commit')
    canonical = json.dumps(queue, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    return sha(canonical), commits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('receipt', type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_bytes())
    matched = []
    recorded = {}
    for name, expected in snapshot['files'].items():
        path = (PROJECT / name).resolve()
        assert PROJECT in path.parents, name
        data = path.read_bytes()
        if sha(data) == expected:
            matched.append(name)
            continue
        assert name == QUEUE, f'Browser snapshot drift: {name}'
        digest, commits = queue_contents(data)
        assert digest == snapshot['queue_without_publication_commits_sha256'], name
        old = snapshot['queue_publication_commits']
        assert all(commits.get(model) == commit for model, commit in old.items()), name
        changes = {k:v for k,v in commits.items() if k not in old}
        assert changes, name
        for model, commit in changes.items():
            assert re.fullmatch('[0-9a-f]{40}', commit)
            row, = [r for r in json.loads(data)['production_queue'] if r['id'] == model]
            if 'refines_existing_model' in row:
                base = PROJECT / 'assets/models/candidates' / row['refines_existing_model']
                manifest = REPO / row['manifest']
                assert manifest.parent == base and re.fullmatch(r'manifest-[a-z0-9-]+\.json',manifest.name), model
            else:
                manifest = PROJECT / 'assets/models/candidates' / model / 'manifest.json'
            content = subprocess.check_output(['git', 'show', f'{commit}:{manifest.relative_to(REPO)}'], cwd=REPO)
            assert content == manifest.read_bytes(), model
        recorded = changes
    result = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(), passed=True, exact_file_matches=len(matched),
                  total_inputs=len(snapshot['files']), snapshot_sha256=sha(args.snapshot.read_bytes()),
                  catalog_sha256=snapshot['files']['data/candidate-city-integrations.json'],
                  release_commits_added_to_queue=recorded)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
