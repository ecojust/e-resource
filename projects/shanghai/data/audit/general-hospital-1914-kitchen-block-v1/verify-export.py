"""Run the same field controls against the original, decoded close model and decoded far model."""
import json,sys
from pathlib import Path
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parents[2]/'source/precise/hongkou-general-hospital-1914-kitchen-block/measurements'))
from check_frontage import check
if __name__=='__main__':
    rows={k:check(Path(v))for k,v in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(rows,ensure_ascii=False,indent=1)+'\n')
    for k,r in rows.items():print(k,r['hits'],r['total'],flush=True)
    raise SystemExit(int(not all(r['passed'] for r in rows.values())))
