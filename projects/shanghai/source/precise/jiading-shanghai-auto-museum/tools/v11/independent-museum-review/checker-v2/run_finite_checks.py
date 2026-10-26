#!/usr/bin/env python3
"""Run frozen finite requests against actual raw; decoded adapters use same API."""
from pathlib import Path
import argparse, json
from modern_mesh import load_raw, filemeta, require
from finite_checks import run_checks

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--geometry', type=Path)
    ap.add_argument('--requests', type=Path, required=True)
    ap.add_argument('--source-structure-report', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    output = a.output.resolve()
    require(output.is_relative_to(HERE) and not output.exists(),
            'Output must be a new immutable file under independent-modern-review')
    asset = load_raw(a.raw, a.geometry)
    requests = json.loads(a.requests.read_bytes())
    report = run_checks(asset, requests, source_structure_report_path=a.source_structure_report)
    report['requests_file'] = filemeta(a.requests)
    report['checker_files'] = [filemeta(HERE/n) for n in ['modern_mesh.py', 'finite_checks.py', 'run_finite_checks.py']]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'report': str(output), 'finite_checks_passed': report['finite_checks_passed']}))
    raise SystemExit(0 if report['finite_checks_passed'] else 1)


if __name__ == '__main__':
    main()
