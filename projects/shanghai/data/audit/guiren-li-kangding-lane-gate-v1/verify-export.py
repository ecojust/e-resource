"""Check the visible carved gate features on all three public mesh variants."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
MEASUREMENTS = ROOT / 'source/precise/jingan-guiren-li-kangding-lane-gate/measurements'
sys.path.insert(0, str(MEASUREMENTS))
sys.path.insert(0, str(ROOT / 'tools'))
from check_gable_relief import check
from package_architectural_model import glb_stats

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models', nargs=3, type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = {}
    for role, path in zip(('raw', 'full', 'lod'), args.models):
        observed = check(path)
        report[role] = dict(sha256=observed['model_sha256'], triangles=glb_stats(path)['triangles'],
                            passed=observed['passed'], cases=observed['samples'])
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    if not all(row['passed'] for row in report.values()):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
