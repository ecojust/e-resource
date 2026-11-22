"""Check the identical photo and roof controls on authored, close and far assets."""
import json,sys
from pathlib import Path
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parents[2]/'source/precise/hongkou-st-lukes-hospital-changzhi-nanxun-corner/measurements'))
from check_street_surfaces import check
if __name__=='__main__':
    results={key:check(Path(filename))for key,filename in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(results,ensure_ascii=False,indent=1)+'\n')
    for role,r in results.items():print(role,r['hits'],r['total'],r['groups'],flush=True)
    raise SystemExit(int(not all(r['structural_controls_passed']for r in results.values())))
