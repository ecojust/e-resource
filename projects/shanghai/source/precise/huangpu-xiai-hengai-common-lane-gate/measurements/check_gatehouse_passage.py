"""Intersect independent photograph samples and centre-lane rays with an exported GLB."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
import shared_lane_passage as room
import gatehouse_signs as sign
from gatehouse_fabric import SEAM
from material_names import MATERIAL
from yongjia_photo_plane import matrix

def read(name):
    return json.loads((HERE/name).read_text())

def check(path):
    h=runpy.run_path(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    tri, ids, names, asset=h['load_triangles'](path)
    expected={'red':{sign.RED},'cream':{sign.CREAM},'green':{sign.GREEN},'pipe':{sign.PIPE,sign.BAND},
              'wall':{MATERIAL,SEAM,room.WALL},'beam':{room.BEAM,room.ARRIS},
              'glass':{room.GLASS,room.GLASS2},'transom':{room.LIGHT},
              'dado':{room.BASE,room.GROOVE},'paving':{room.PAVE},'cover':{room.LID},'ring':{room.RING}}
    projections={}
    for side,v in read('gatehouse-sign-readings.json')['views'].items():
        key='name-'+('left' if side=='west' else 'right')+'-2020'
        projections[key]=np.linalg.solve(v['to_reference'],matrix(v['reference']))
    for key,v in read('gatehouse-passage-readings.json')['source_views'].items():
        projections[key]=np.linalg.solve(v['to_reference'],matrix(v['reference']))
    points=read('gatehouse-passage-witnesses.json')['points'];result=[]
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    for name,m in projections.items():
        inv=np.linalg.inv(m[:,:3]);eye=-inv@m[:,3]
        q=tri@m[:,:3].T+m[:,3];uv=q[:,:,:2]/q[:,:,2:];lo=uv.min(1);hi=uv.max(1)
        def first(px):
            ray=inv@np.r_[px,1.];ray/=np.linalg.norm(ray)
            idx=np.flatnonzero((lo<=px+.00001).all(1)&(hi>=px-.00001).all(1)&(normals@ray<0))
            if not len(idx):return None
            j,dist,_=h['first_hit'](tri[idx],eye,ray)
            return names[ids[idx[j]]] if np.isfinite(dist) else None
        for witness in (v for v in points if v['camera']==name):
            xy=np.array(witness['uv']);targets=expected[witness['kind']];radius=witness['radius_px']
            nominal=first(xy);matched=None
            if nominal in targets:matched=[0,0]
            else:
                offsets=sorted(((dx,dy) for dx in range(-radius,radius+1) for dy in range(-radius,radius+1)
                                if 0<dx*dx+dy*dy<=radius*radius),key=lambda p:p[0]**2+p[1]**2)
                for dx,dy in offsets:
                    if first(xy+[dx,dy]) in targets:
                        matched=[dx,dy];break
            result.append({**witness,'first_surface':nominal,'direct':nominal in targets,'match_offset_px':matched})
    lane=[]
    for x in [-1.2,-.8,-.4,0.,.4,.8,1.2]:
        for z in [.3,.8,1.3,1.8,2.3,2.6]:
            _,dist,_=h['first_hit'](tri,np.array([x,-.5,z]),np.array([0.,1.,0.]))
            lane.append({'x_m':x,'z_m':z,'open':not bool(np.isfinite(dist))})
    return dict(asset=asset,count=len(result),direct=sum(v['direct']for v in result),
                near=sum(v['match_offset_px'] is not None for v in result),open_cross_section=sum(v['open']for v in lane),
                lane=lane,photo_checks=result)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();r=check(args.glb)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
    print(r['count'],r['direct'],r['near'],r['open_cross_section'])
