"""Run the original and revised vector checks against two frozen production catalogs."""
import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from apply import apply

HERE = Path(__file__).resolve().parent
CHECKER = Path('tools/check-sourced-candidate-runtime.mjs')
CONTRACT = 'final-placement-contract.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(project, checker, case, out, expected_failure=None):
    result = subprocess.run(['node', str(checker), str(case)], capture_output=True, text=True,
                            env={**os.environ, 'SHANGHAI_PROJECT_ROOT': str(project), 'QA_OUTPUT_DIR': str(out)})
    record = dict(case_sha256=digest(case), checker_sha256=digest(checker), exit_code=result.returncode,
                  catalog_sha256=digest(project/'data/candidate-city-integrations.json'))
    if expected_failure:
        assert result.returncode and expected_failure in result.stderr, result.stderr
        return {**record, 'matched_failure': expected_failure}, None
    assert result.returncode == 0, result.stderr
    summary = json.loads((out/'runtime-placement.json').read_bytes())
    return {**record, 'shader': json.loads(result.stdout), 'city_rows': summary['catalogRows']}, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-project', required=True, type=Path)
    parser.add_argument('--target-project', required=True, type=Path)
    parser.add_argument('--revised-case', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    lp, tp, case, out = (p.resolve() for p in [args.legacy_project, args.target_project, args.revised_case, args.out])
    out.mkdir(parents=True, exist_ok=True)
    legacy = lp/'data/audit/guohua-bank-v1/map-case.json'
    target = tp/'data/audit/chekiang-first-bank-v1/map-case.json'
    old = tp/CHECKER
    with tempfile.TemporaryDirectory() as scratch:
        w = Path(scratch)
        new = w/old.name
        shutil.copyfile(old, new)
        apply(new)
        before = old.read_text().splitlines(keepends=True)
        after = new.read_text().splitlines(keepends=True)
        (out/'checker.diff').write_text(''.join(difflib.unified_diff(before, after,
                                               fromfile='a/'+str(CHECKER), tofile='b/'+str(CHECKER))))
        records = {}
        records['legacy_original'], original = invoke(lp, old, legacy, w/'legacy-original')
        records['legacy_revised'], fixed = invoke(lp, new, legacy, w/'legacy-revised')
        assert original['sha256'].pop('checker') == digest(old)
        assert fixed['sha256'].pop('checker') == digest(new)
        assert original == fixed
        records['legacy_result_equal_except_checker_hash'] = True
        records['target_original'], _ = invoke(tp, old, target, w/'target-original', 'true !== false')
        records['target_revised'], fixed = invoke(tp, new, case, w/'target-revised')
        spec = json.loads(case.read_bytes())
        original_office = next(p for p in fixed['ground'] if p['name']=='retained offices at author origin')
        cut = next(p for p in fixed['ground'] if p['name']=='closed bank door')
        assert not original_office['candidate'] and not original_office['cut'] and cut['candidate'] and cut['cut']
        owner = json.loads((case.parent/CONTRACT).read_bytes())['owner']['feature_local_id']
        vectors = [v for v in fixed['vector'] if v['owner']==owner]
        assert len(vectors)==2 and {v['source']for v in vectors}=={'openmaptiles','overture-buildings'}
        assert all(v['hidden'] and v['residuals']==1 for v in vectors)
        records['target_witnesses'] = dict(author_frame_removed_xy=spec['residualCutProbe'],removed=cut,
                                            retained_author_origin=original_office,owner_vectors=vectors)
        invalid = w/'wrong-case'; invalid.mkdir()
        shutil.copyfile(case.parent/CONTRACT, invalid/CONTRACT)
        spec['residualCutProbe']=[0,0]
        bad_case = invalid/'map-case.json'
        bad_case.write_text(json.dumps(spec))
        records['target_negative_control'], _ = invoke(tp, new, bad_case, w/'negative', 'Removed probe outside replacement cut')
        shutil.copyfile(w/'target-revised/runtime-placement.json',out/'runtime-placement.json')
        (out/'regression-results.json').write_text(json.dumps(records,indent=2)+'\n')


if __name__=='__main__':
    main()
