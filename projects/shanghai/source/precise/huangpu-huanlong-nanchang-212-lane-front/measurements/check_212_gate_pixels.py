"""Compare photographed 212 entrance materials to the first face in a real GLB."""
import argparse
from pathlib import Path
import json
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene,first_hit
from huanlong_photo_plane import CALIBRATION
import iron_entrance as gate
EXPECT={'iron':{gate.IRON,gate.EDGE},'stone':{gate.STONE},'lantern':{gate.RED,gate.RIB},'gold':{gate.GOLD,gate.RIB},'cream':{gate.CREAM},'trim':{gate.BLUE,gate.STONE},'plinth':{gate.BASE},'green':{gate.GREEN},'ivory':{gate.IVORY},'sign':{gate.SIGN},'ink':{gate.INK},'relief':{gate.PALE,gate.DEEP,gate.STONE}}
def check(path):
    scene=SerialScene(path);tri=scene.tri;out=[]
    points=json.loads((HERE/'212-gate-pixel-witnesses.json').read_bytes())['samples']
    for cam in dict.fromkeys(q['camera']for q in points):
        P=np.array(CALIBRATION['camera_matrices'][cam]);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
        p=tri@P[:,:3].T+P[:,3];den=p[:,:,2]
        uv=p[:,:,:2]/np.where(np.abs(den)>1e-12,den,1e-12)[:,:,None];lo=uv.min(1);hi=uv.max(1)
        near_cross=(den.min(1)<=1e-8)&(den.max(1)>1e-8);visible=den.min(1)>1e-8
        for row in [q for q in points if q['camera']==cam]:
            px=np.array(row['native_pixel']);radius=row['tolerance_px']
            candidates=np.flatnonzero(near_cross|(visible&(lo<=px+radius+.00001).all(1)&(hi>=px-radius-.00001).all(1)))
            def first(offset):
                ray=inv@np.r_[px+offset,1.];ray/=np.linalg.norm(ray)
                local=candidates[scene.cross[candidates]@ray<0]
                if len(local)==0:return None
                j,dist,_=first_hit(tri[local],eye,ray)
                return scene.materials[scene.mi[local[j]]] if np.isfinite(dist) else None
            surface=first(np.array([0,0]));match=surface in EXPECT[row['surface']]
            found=[0,0] if match else None
            if found is None:
                offsets=sorted((dx*dx+dy*dy,dy,dx)for dy in range(-radius,radius+1)for dx in range(-radius,radius+1)if 0<dx*dx+dy*dy<=radius**2)
                for _,dy,dx in offsets:
                    if first(np.array([dx,dy]))in EXPECT[row['surface']]:
                        found=[dx,dy];break
            out.append({**row,'first_surface':surface,'exact':match,'nearest_matching_offset':found})
    return dict(asset=scene.asset,triangles=len(tri),count=len(out),exact=sum(p['exact']for p in out),within=sum(p['nearest_matching_offset']is not None for p in out),observations=out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=check(a.model);a.output.write_text(json.dumps(r,indent=1,ensure_ascii=False)+'\n');print(r['asset']['file'],r['count'],r['exact'],r['within'])
