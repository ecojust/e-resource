#!/usr/bin/env python3
"""Bind separately observed actual fixtures; never infer IDs or run a browser."""
from pathlib import Path
import argparse
import json
from osm_evidence_set import meta, need, read_fixture, read_fixture_set


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, action='append', required=True)
    parser.add_argument('--targets', nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    need(len(args.targets) == len(set(args.targets)), 'Duplicate selected targets')
    rows = {}
    for source in args.fixture:
        source = source.resolve()
        target = json.loads(source.read_bytes()).get('landmark_id')
        need(target in args.targets and target not in rows, 'Unexpected or duplicate actual target fixture')
        read_fixture(source, target)
        rows[target] = {'source': str(source), **meta(source)}
    need(set(rows) == set(args.targets), 'A selected target lacks actual fixture evidence')
    need(not args.output.exists(), 'Preserve existing fixture sets')
    document = {'schema': 'actual-osm-component-set-qa-v1', 'inputs_ready': True,
                'targets': rows, 'scope': 'Explicit actual per-target OSM observations; no model/browser acceptance or new source observations performed by this preparer.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    read_fixture_set(args.output, args.targets)
    print(json.dumps({'output': str(args.output.resolve()), **meta(args.output),
                      'prepared': True, 'browser_passed': False, 'targets': args.targets}))


if __name__ == '__main__':
    main()
