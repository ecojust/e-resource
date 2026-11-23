"""Cast held-out photo rays into a released GLB in its reconstructed coordinate system."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
PICKS=json.loads((HERE/'garden-gable-material-points.json').read_bytes())['photos']
def matches(h,w):
    if h is None:return False
    allowed={'field':['smoky leaded glass','dark lead'],'stone':['buff window stone'],'brick':['weathered russet brick']}
    return any(h['material'].endswith(v)for v in allowed[w])
def check(path):
    scene=runpy.run_path(str(HELPER))['SerialScene'](path)
    cams=json.loads((HERE/'church-registration.json').read_bytes())['stations']
    report={'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'coordinate_frame':'Native source-photo pixels. Fourteen-pixel neighbourhood checked independently of the exact first intersections.','views':{}}
    for key,tests in PICKS.items():
        c=cams[key];k,r,eye=[np.array(c[n])for n in ('K','R','C')]
        def hit(uv):
            v=r.T@np.linalg.solve(k,[*uv,1]);return scene.ray(eye,v/np.linalg.norm(v),160)
        rows=[]
        for name,xy,w in tests:
            first=hit(xy);ok=matches(first,w);nearest=[0,0]if ok else None
            if not ok:
                offsets=sorted(((i,j)for i in range(-14,15,2)for j in range(-14,15,2)if 0<i*i+j*j<=196),key=lambda p:p[0]**2+p[1]**2)
                # Batch at the original source resolution. Fourteen native pixels
                # correspond to about 2.2–2.4 pixels in the marked study image.
                for i,j in offsets:
                    if matches(hit([xy[0]+i,xy[1]+j]),w):nearest=[i,j];break
            rows.append({'target':name,'pixel':xy,'expected':w,'direct':ok,'actual':first,'nearest_within_14_native_px':nearest})
        report['views'][key]={'direct':sum(v['direct']for v in rows),'within_14_native_px':sum(v['nearest_within_14_native_px'] is not None for v in rows),'count':len(rows),'checks':rows}
    return report
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    a=cli.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(check(a.mesh),indent=2)+'\n')
