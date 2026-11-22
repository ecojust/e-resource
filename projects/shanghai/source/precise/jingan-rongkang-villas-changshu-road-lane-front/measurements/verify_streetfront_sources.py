"""Reproject the published street landmarks using the exact registered photograph matrices."""
from pathlib import Path
import json
import numpy as np
D=Path(__file__).resolve().parent
def run():
    j=json.loads((D/'streetfront-photo-controls.json').read_text());errors=[]
    for name,item in j['features'].items():
        samples=item['observations'];assert len(set(q['source']for q in samples))>=2,name
        for s in samples:
            cam=j['stations'][s['source']];P=np.array(cam['matrix']);p=P@[*item['local_xyz'],1]
            assert p[2]>0 and len(cam['photo_sha256'])==64
            q=np.array(s['native_pixel']);w,h=cam['size'];assert 0<=q[0]<w and 0<=q[1]<h
            err=p[:2]/p[2]-q;assert np.max(np.abs(err-np.array(s['predicted_minus_observed'])))<.08,(name,err)
            errors.append(float(np.linalg.norm(err)))
    fixed=json.loads((D/'commons-2017-street-registered.json').read_text())
    P=np.array(fixed['matrix']);c=-np.linalg.solve(P[:,:3],P[:,3]);assert 1.1<c[2]<2.3
    original=[]
    for k,q in fixed['fixed_background_references'].items():
        p=P@[*q['xyz'],1];err=p[:2]/p[2]-q['original_pixels']
        assert np.max(np.abs(err-q['predicted_minus_observed_pixels']))<.06,k
        original.append(float(np.linalg.norm(err)))
    print(f"{len(j['features'])} street landmarks, {len(errors)} measured rays, median {np.median(errors):.2f} px, max {max(errors):.2f} px. 2017 native camera: {len(original)} references, eye height {c[2]:.2f} m.")
if __name__=='__main__':run()
