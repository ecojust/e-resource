"""Intersect unfiltered decoded city geometry with the native source pixels and local wall sections."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from continental_street_wall import Bay, SCHEDULE, LAYOUT, parapet, BRICK, STONE, EDGE, SHADE, FLOWER
from glb_triangles import SerialScene

def inspection(path):
    scene=SerialScene(path);physical=[];photo=[];stonework={BRICK,STONE,EDGE,SHADE,FLOWER}
    def ray_at(b,u,z,d0,d1,selection=None):
        start=np.array(b.point(u,d0,z));end=np.array(b.point(u,d1,z));return scene.ray(start,end-start,np.linalg.norm(end-start),selection.__contains__ if selection is not None else None)
    def append(rows,kind,expect,hit,**fields):
        material=hit['material'] if hit else None
        rows.append(dict(feature=kind,passed=material in expect,first_surface=material,**fields))
    for record in SCHEDULE:
        b=Bay(record['bay'])
        for row in record['floors']:
            low,high=row['sill_z'],row['head_z'];face=row['face_depth_m']
            for idx,(l,r) in enumerate(row['openings_u_m']):
                u=(l+r)/2
                for frac in [.25,.72]:
                    hit=ray_at(b,u,low+(high-low)*frac,face-.15,1.04,stonework)
                    append(physical,'pierced sash opening',[None],hit,bay=b.index,floor=row['floor'],opening=idx)
                hit=ray_at(b,u,low-.045,face-.36,1.,stonework)
                append(physical,'window sill',[STONE,EDGE,BRICK],hit,bay=b.index,floor=row['floor'],opening=idx)
        width=b.width
        section,centres=parapet(b)
        low,high=section['base_and_coping_top_m']
        for n,u in enumerate(centres):
            for z,kind,classes in [((low+high)/2,'clear notch',[None]),(low-.06,'notch sill',[STONE]),(section['strip_centre_z_m'] or high-.025,'upper crossing strip',[SHADE]if b.index<7 else[None])]:
                append(physical,kind,classes,ray_at(b,u,z,.0,.94),bay=b.index,notch=n+1)
        for l,r in zip(centres,centres[1:]):
            append(physical,'raised merlon',[BRICK,STONE],ray_at(b,(l+r)/2,(low+high)/2,0,.95),bay=b.index)
        if b.index in (1,2,3,4,7,8,9):
            append(physical,'diamond flower relief',[FLOWER,EDGE],ray_at(b,width/2,8.26,0,.8),bay=b.index)
    cams=json.loads((HERE/'street-photo-registration.json').read_text())['photos']
    observations=json.loads((HERE/'parapet-source-pixels.json').read_text())['points']
    for row in observations:
        cam=cams[row['photo']];eye=np.array(cam['eye_local_m']);P=np.array(cam['P_native'])
        direction=np.linalg.solve(P[:,:3],[*row['uv_native'],1.]);direction/=np.linalg.norm(direction)
        hit=scene.ray(eye,direction,170.)
        kinds={'sky':[None],'coping':[STONE,EDGE,BRICK],'solid merlon':[STONE,EDGE,BRICK],'top strip':[SHADE]}
        append(photo,row['feature'],kinds[row['feature']],hit,bay=row['bay'],photo=row['photo'],uv_native=row['uv_native'],pattern=row['pattern'])
    def wrap(rows):return dict(passed=sum(bool(x['passed'])for x in rows),total=len(rows),rays=rows)
    return dict(asset=scene.asset,physical=wrap(physical),photo=wrap(photo))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('glb',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=inspection(args.glb)
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    for k in ['physical','photo']:print(k,result[k]['passed'],result[k]['total'],[r for r in result[k]['rays']if not r['passed']][:7])
