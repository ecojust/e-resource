"""Compare native source pixels with the three front roof windows and their hipped caps."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from wing_frame import WingFrame
from roof_dormers import dormer_layout
from service_materials import FRAME, GLASS, PLASTER, TILE
from glb_triangles import SerialScene

def check(path,component=None):
    frame=WingFrame();scene=SerialScene(path);tests=[];registered=[]
    reference=SerialScene(component) if component else None
    samples={'design':[
      ('left glazed lights',GLASS,[(191,154),(202,157),(212,160),(223,166)]),
      ('left muntins',FRAME,[(197,160),(208,161),(218,160)]),
      ('central lights',GLASS,[(268,160),(276,162),(286,163),(295,165)]),
      ('central muntins',FRAME,[(272,161),(281,161),(290,163)]),
      ('right lights',GLASS,[(333,163),(340,162),(347,166),(354,162)]),
      ('right muntins',FRAME,[(336,160),(343,162),(350,164)]),
      ('three cap planes',TILE,[(206,137),(282,127),(343,148)]),
      ('three plaster fields',PLASTER,[(273,147),(283,141),(292,146)]),
      ('two bowed timbers',FRAME,[(279,145),(287,145)])],
      'album':[
      ('left dark opening',[GLASS,FRAME],[(438,552),(451,553),(463,554)]),
      ('central dark opening',[GLASS,FRAME],[(515,552),(524,553),(534,553)]),
      ('right dark opening',[GLASS,FRAME],[(577,555),(587,555),(597,555)]),
      ('flanking hipped caps',TILE,[(445,531),(580,533)]),
      ('central white gable',PLASTER,[(515,535),(523,530),(533,537)])]}
    for name,groups in samples.items():
        cam=getattr(frame,name);radius=2 if name=='design' else 6
        offsets=sorted([(x*x+y*y,x,y)for x in range(-radius,radius+1)for y in range(-radius,radius+1)if x*x+y*y<=radius**2])
        for field,expect,points in groups:
            materials=[expect]if isinstance(expect,str)else expect
            for u,v in points:
                hits=None;direct=None;depth_change=None
                for distance,dx,dy in offsets:
                    q=scene.ray(cam.C,cam.ray((u+dx,v+dy)),length=500)
                    if distance==0:
                        direct=q['material']if q else None
                        if reference:
                            original=reference.ray(cam.C,cam.ray((u,v)),length=500)
                            if original and q:
                                depth_change=round(q['distance_m']-original['distance_m'],6)
                    if q and q['material'] in materials:hits=float(np.sqrt(distance));break
                tests.append(dict(station=name,field=field,pixel=[u,v],expected=materials,first_hit=direct,nearest_px=hits,assembly_first_surface_distance_change_m=depth_change))
        for m in dormer_layout(frame):
            corners=[[x,m['y'],z]for x,z in [(m['l'],m['z1']),(m['r'],m['z1']),(m['r'],m['z0']),(m['l'],m['z0'])]]
            at=np.array([cam.pixel(p)for p in corners]);observed=np.array(m['observation'][name])
            registered.append(dict(station=name,opening=m['name'],pixels=at.tolist(),measured=observed.tolist(),differences_px=np.linalg.norm(at-observed,axis=1).tolist()))
    return dict(input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),modelled_epoch='2014 architectural design perspective; positions of the three dormers checked against the separate 1937 archive photograph',limits_px={'design':2,'album':6},observations=tests,corner_registration=registered,count=len(tests),direct=sum(x['nearest_px']==0 for x in tests),bounded=sum(x['nearest_px']is not None for x in tests))

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('glb',type=Path);cli.add_argument('out',type=Path);cli.add_argument('--component',type=Path,help='Optional same-level component GLB to test actual nearest-surface depth after assembly');a=cli.parse_args()
    result=check(a.glb,a.component);a.out.write_text(json.dumps(result,indent=2)+'\n');print(result['direct'],result['bounded'],result['count'])
