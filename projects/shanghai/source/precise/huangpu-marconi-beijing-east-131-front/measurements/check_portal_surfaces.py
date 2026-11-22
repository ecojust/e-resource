"""Cast source-image pixels against the first outward face of each released portal."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene,first_hit
from marconi_photo_plane import CALIBRATION
import marconi_arched_portal as m
GROUPS={'wedge':[*m.BRICK,m.MOULD,m.LIP],'arch facing':[*m.BRICK,m.MOULD,m.MORTAR,m.LIP],
        'soffit':[m.SOFFIT,*m.SOFFIT_BRICK],'lunette':[*m.LUNETTE,m.LUNETTE_JOINT],
        'pier':[*m.BRICK,m.MORTAR],'capital':[m.MOULD,m.LIP],'glass':[m.GLASS],'timber':[m.TIMBER,m.BEAD],
        'inner shadow':[m.DARK],'letter':[m.WHITE],'iron':[m.GREEN],'enamel':[m.ENAMEL]}
def inspect(file):
    s=SerialScene(file)
    cases=json.loads((HERE/'portal-surface-witnesses.json').read_text())['samples']
    hits=[]
    for cam,matrix in CALIBRATION['camera_matrices'].items():
        mat=np.array(matrix); inv=np.linalg.inv(mat[:,:3]); eye=-inv@mat[:,3]
        proj=s.tri@mat[:,:3].T+mat[:,3]
        den=proj[:,:,2];uv=proj[:,:,:2]/np.where(np.abs(den)>1.e-10,den,1.)[:,:,None]
        front=den.min(1)>0.;cross=(den.min(1)<=0.)&(den.max(1)>0.)
        lo,hi=uv.min(1),uv.max(1)
        for row in cases:
            if row['camera']!=cam:continue
            xy=np.asarray(row['original_px']);r=row['radius_px'];allow=GROUPS[row['material_group']]
            ids=np.flatnonzero(cross|(front&(lo<=xy+r+.01).all(1)&(hi>=xy-r-.01).all(1)))
            def at(dx,dy):
                direction=inv@np.r_[xy+[dx,dy],1.];direction/=np.linalg.norm(direction)
                faces=ids[s.cross[ids]@direction<0]
                if not len(faces):return None
                j,t,_=first_hit(s.tri[faces],eye,direction)
                return s.materials[s.mi[faces[j]]] if np.isfinite(t) else None
            initial=at(0,0)
            offset=[0,0] if initial in allow else None
            if offset is None:
                for _,x,y in sorted((x*x+y*y,x,y) for x in range(-r,r+1) for y in range(-r,r+1) if 0<x*x+y*y<=r*r):
                    if at(x,y) in allow:offset=[x,y];break
            hits.append(dict(**row,first=initial,matching_offset_px=offset))
    return dict(asset=s.asset,triangles=len(s.tri),total=len(hits),
                exact=sum(r['matching_offset_px']==[0,0] for r in hits),
                within_radius=sum(r['matching_offset_px'] is not None for r in hits),samples=hits)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();report=inspect(a.model);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
    print(report['asset']['file'],report['triangles'],report['total'],report['exact'],report['within_radius'])
