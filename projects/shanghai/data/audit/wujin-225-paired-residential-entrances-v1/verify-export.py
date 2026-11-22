"""Check a raw mesh and both decoded models using the two 2015 courtyard views."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).absolute().parent
sys.path.insert(0, str(HERE.parents[2] / "source/precise/hongkou-wujin-225-paired-residential-entrances/measurements"))
from check_paired_front import check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs=3, type=Path, metavar="MODEL")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    results = {role: check(path) for role, path in zip(("raw", "full", "lod"), args.models)}
    args.output.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n")
    for role, result in results.items():
        print(role, result["hits"], "/", result["total"], result["mesh_sha256"])
    return int(any(not result["passed"] for result in results.values()))


if __name__ == "__main__":
    sys.exit(main())
