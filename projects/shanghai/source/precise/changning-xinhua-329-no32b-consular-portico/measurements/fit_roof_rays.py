"""Intersect independent observations of roof, dormer and stair-tower points in the two court photos."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).absolute().parent
def ray(station,pixel):
    K,R,C=[np.array(station[k])for k in ('K','R','C')]
    vector=R.T@np.linalg.solve(K,[*pixel,1.])
    return C,vector/np.linalg.norm(vector)
def project(station,xyz):
    K,R,C=[np.array(station[k])for k in ('K','R','C')]
    p=K@R@(xyz-C)
    return p[:2]/p[2]
if __name__=='__main__':
    wide=json.loads((HERE/'portico-camera-pair.json').read_bytes())['stations']['wide']
    scaffold=json.loads((HERE/'scaffold-camera.json').read_bytes())
    output=[]
    for feature,a,b in json.loads((HERE/'roof-station-marks.json').read_bytes()):
        first,v=ray(wide,a);second,w=ray(scaffold,b)
        t=np.linalg.lstsq(np.column_stack([v,-w]),second-first,rcond=None)[0]
        p,q=first+t[0]*v,second+t[1]*w
        xyz=(p+q)/2
        separation=float(np.linalg.norm(p-q))
        errors=[float(np.linalg.norm(project(s,xyz)-pix)) for s,pix in [(wide,a),(scaffold,b)]]
        output.append(dict(feature=feature,wide_px=a,scaffold_px=b,xyz_m=xyz.round(4).tolist(),
            ray_separation_m=round(separation,4),intersection_angle_deg=round(float(np.rad2deg(np.arccos(np.clip(v@w,-1,1)))),3),
            reprojection_px=[round(x,3)for x in errors]))
    (HERE/'roof-ray-comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    for r in output:print(r['feature'],r['xyz_m'],r['reprojection_px'],r['intersection_angle_deg'])
