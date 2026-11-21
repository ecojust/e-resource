"""Compare matching releases before and after the West Park Mansions navigation correction."""
import argparse
import hashlib
import json
from pathlib import Path

MODEL = 'changning-west-park-mansions'
PLACEMENT = 'data/global-models/additional-placement.json'
CATALOG = 'data/candidate-city-integrations.json'
CONTRACT = 'data/audit/west-park-mansions-v1/final-placement-contract.json'
OLD = '在院内查看抬高的方柱木廊、中央绿窗与几组翘檐老虎窗。'
NEW = '从南侧庭院可见三组宽浅拱、住户围合的阳台与两端屋顶花架。'

def metadata(path):
    b = path.read_bytes()
    return {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def unique(rows, field, value):
    matches = [row for row in rows if row[field] == value]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one {field}={value} in the signed source')
    return matches[0]

def check(before, after):
    for name in (CONTRACT, PLACEMENT, CATALOG):
        previous = json.loads((before/name).read_bytes())
        current = json.loads((after/name).read_bytes())
        if name == CONTRACT:
            row = previous
        else:
            row = unique(previous['records' if name == PLACEMENT else 'models'], 'id', MODEL)
            dependency = CONTRACT if name == PLACEMENT else PLACEMENT
            group = previous['source_contracts' if name == PLACEMENT else 'input_files']
            bound = unique(group, 'file', dependency)
            assert bound == {'file': dependency, **metadata(before/dependency)}
            bound.update(metadata(after/dependency))
        assert row['id'] == MODEL
        assert row['navigation'] == {'listed': False, 'status': OLD}
        row['navigation']['status'] = NEW
        if previous != current:
            raise ValueError(f'A field outside the navigation sentence and its two input bindings changed in {name}')
    return {'corrected_model': MODEL, 'original_sha256': metadata(before/CATALOG)['sha256'],
            'corrected_sha256': metadata(after/CATALOG)['sha256'], 'passed': True}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before_project', type=Path)
    parser.add_argument('after_project', type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.before_project, args.after_project), indent=2))
