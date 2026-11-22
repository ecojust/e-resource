import sys,json
from pathlib import Path
S=Path(__file__).resolve().parents[3]/'source/precise/jingan-cheng-family-residence-historic-balcony/measurements'
sys.path.insert(0,str(S));from check_window_front import check
out={}
for name,f in zip(('raw','full','lod'),sys.argv[1:4]):
 r=check(Path(f));out[name]=dict(sha256=r['asset_sha256'],triangles=r['triangles'],passed=r['passed']==r['rays'],cases=r['observations'])
Path(sys.argv[4]).write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
assert all(v['passed']for v in out.values())
