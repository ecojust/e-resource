"""Probe the actual exported historic balcony locally, then project the recorded 2018 pixels."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import street_balcony as b

def inspect(path):
    scene=SerialScene(path)
    physical,photo=[],[]
    def item(kind,ok,result,**extra):
        return dict(feature=kind,passed=bool(ok),first_material=result['material'] if result else None,**extra)
    def local(k,face,u,z,expected):
        xy=b.loc(face,u,0.);n=b.INWARD[face];hit=scene.ray(np.r_[xy-.135*n,z],np.r_[n,0.],.365)
        mat=hit['material']if hit else None
        physical.append(item(k,mat in expected,hit,face=face+1,u=round(u,4),z=round(z,4)))
    for idx,(face,u,z) in enumerate(b.MOTIFS):
        local('centre boss',face,u,z,[b.FACE])
        for a in np.arange(4)*np.pi/2:
            rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
            for uu,zz in [(-.047,.201),(0.,.249),(.047,.201),(0.,.115)]:
                du,dz=rot@[uu,zz]
                local('open petal',face,u+du,z+dz,[None])
            for length in [.11,.17,.23]:
                du,dz=rot@[length,length]
                local('diagonal stone rib',face,u+du,z+dz,[b.FACE])
    for face,length in enumerate(b.LENGTH):
        for frac in (.18,.39,.61,.82):
            for z,mats in [(-.171,[b.FINISH,b.CUT]),(-.069,[b.PLINTH]),(.024,[b.FINISH,b.BEAD]),(.934,[b.FINISH,b.BEAD])]:
                local('sill and coping',face,frac*length,z,mats)
    doc=json.loads((HERE/'historic-balcony-cameras.json').read_text())['gao2018']
    P=np.array(doc['P']);eye=np.array(doc['eye_m'])
    controls=json.loads((HERE/'modern-pierced-parapet-controls.json').read_text())['controls']
    for row in controls:
        face,u,z=b.MOTIFS[row['panel']-1]
        direction=np.linalg.solve(P[:,:3],[*row['uv_native'],1.]);direction/=np.linalg.norm(direction)
        n=b.INWARD[face];along=(b.PATH[face]-eye[:2])@n/(direction[:2]@n)
        behind=along+(b.FRONT_INSET+b.SCREEN_DEPTH+.025)/(direction[:2]@n)
        hit=scene.ray(eye,direction,behind)
        mat=hit['material'] if hit else None
        if row['feature']=='aperture':
            valid=mat is None or not mat.startswith(b.PREFIX)
        else:
            valid=mat==b.FACE
        photo.append(item(row['feature'],valid,hit,panel=row['panel'],native_uv=row['uv_native']))
    def count(rows):
        return dict(total=len(rows),passed=sum(r['passed']for r in rows),rays=rows)
    return dict(asset=scene.asset,physical=count(physical),original_pixels=count(photo))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('asset',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();result=inspect(args.asset)
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    for name in ('physical','original_pixels'):
        r=result[name];print(name,r['passed'],r['total'],[q for q in r['rays']if not q['passed']][:12])
