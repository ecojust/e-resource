"""Cast held-out photo rays into a released GLB in its reconstructed coordinate system."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
PICKS=json.loads((HERE/'arcade-material-holdouts.json').read_bytes())['photos']
def matches(h,w):
    if h is None:return w=='parapet-opening'
    allowed={'grey':['filled grey brick'],'inside':['shaded passage wall','gallery flooring','roof soffit'],'cream':['perforated cream balustrade'],'red':['red arch brick'],'roof':['dark roof tiles'],'parapet-opening':['dark roof tiles','shaded passage wall','roof soffit']}
    return any(h['material'].endswith(v)for v in allowed[w])
def check(path):
    scene=runpy.run_path(str(HELPER))['SerialScene'](path)
    cams=json.loads((HERE/'arcade-registration.json').read_bytes())['stations']
    report={'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'coordinate_frame':'Native source-photo pixels. Eight-pixel neighbourhood checked independently of the exact first intersections.','views':{}}
    for key,tests in PICKS.items():
        c=cams[key];k,r,eye=[np.array(c[n])for n in ('K','R','C')]
        def hit(uv):
            v=r.T@np.linalg.solve(k,[*uv,1]);return scene.ray(eye,v/np.linalg.norm(v),500)
        rows=[]
        for name,xy,w in tests:
            first=hit(xy);ok=matches(first,w);nearest=[0,0]if ok else None
            if not ok:
                offsets=sorted(((i,j)for i in range(-8,9,1)for j in range(-8,9,1)if 0<i*i+j*j<=64),key=lambda p:p[0]**2+p[1]**2)
                # Batch at the original source resolution. Fourteen native pixels
                # correspond to about 2.2–2.4 pixels in the marked study image.
                for i,j in offsets:
                    if matches(hit([xy[0]+i,xy[1]+j]),w):nearest=[i,j];break
            rows.append({'target':name,'pixel':xy,'expected':w,'direct':ok,'actual':first,'nearest_within_8_native_px':nearest})
        report['views'][key]={'direct':sum(v['direct']for v in rows),'within_8_native_px':sum(v['nearest_within_8_native_px'] is not None for v in rows),'count':len(rows),'checks':rows}
    return report
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    a=cli.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(check(a.mesh),indent=2)+'\n')
