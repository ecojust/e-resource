"""Test independently read building features against the first actual material in each delivered mesh."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def check(mesh):
    Scene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
    scene=Scene(mesh);reg=json.loads((HERE/'river-registration.json').read_bytes());measured=json.loads((HERE/'river-material-checks.json').read_bytes())
    res=dict(sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),radius_native_px=5,views={})
    for station,checks in measured.items():
        cam=reg['stations'][station];R=np.array(cam['R']);inv=np.linalg.inv(cam['K']);eye=cam['eye'];out=[]
        for name,uv,expected in checks:
            for di,dj in [(0,0)]+sorted([(i,j)for i in range(-5,6)for j in range(-5,6)if 0<i*i+j*j<=25],key=lambda v:v[0]**2+v[1]**2):
                vec=R.T@inv@[uv[0]+di,uv[1]+dj,1];hit=scene.ray(eye,vec/np.linalg.norm(vec),1000)
                mat=hit['material']if hit else None
                if (di,dj)==(0,0):first=mat
                if mat and any(mat.endswith(m) for m in expected):nearest=[di,dj];break
            else:nearest=None
            out.append(dict(label=name,uv=uv,expected=expected,first_material=first,nearest_offset=nearest,direct=nearest==[0,0]))
        res['views'][station]=dict(total=len(out),direct=sum(r['direct']for r in out),within_five=sum(r['nearest_offset']is not None for r in out),checks=out)
    return res
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path);a=cli.parse_args();a.output.write_text(json.dumps(check(a.mesh),ensure_ascii=False,indent=2)+'\n')
