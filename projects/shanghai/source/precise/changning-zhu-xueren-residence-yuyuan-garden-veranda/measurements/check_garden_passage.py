"""Read the central arch, three measured passages and the curved stair from an exported mesh."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import first_hit,SerialScene
sys.path.insert(0,str(HERE.parent/'source'))
from zhu_garden_materials import GLASS,WOOD,STAIR,STONE


def read(path):
    return json.loads(path.read_bytes())


class Photograph:
    def __init__(self,scene,P):
        self.scene=scene
        self.inverse=np.linalg.inv(P[:,:3])
        self.eye=-self.inverse@P[:,3]
        screen=scene.tri@P[:,:3].T+P[:,3]
        assert screen[:,:,2].min()>0
        uv=screen[:,:,:2]/screen[:,:,2:]
        self.low,self.high=uv.min(axis=1)-.00001,uv.max(axis=1)+.00001

    def hit(self,u,v):
        mask=(self.low[:,0]<=u)&(self.high[:,0]>=u)&(self.low[:,1]<=v)&(self.high[:,1]>=v)
        candidates=np.flatnonzero(mask)
        if not len(candidates):return None
        d=self.inverse@[u,v,1];d/=np.linalg.norm(d)
        i,dist,p=first_hit(self.scene.tri[candidates],self.eye,d)
        if not np.isfinite(dist):return None
        return self.scene.materials[int(self.scene.mi[candidates[i]])],p


def inspect(path):
    scene=SerialScene(path)
    reg=read(HERE/'south-veranda-depth-and-third-camera.json')
    frame=Photograph(scene,np.array(reg['camera_08']))
    arch=[]
    for record in read(HERE/'south-garden-centre-arch.json')['arc_trace']:
        u,v=record['uv'];facade=[];rear=[]
        for k in range(-12,13):
            hit=frame.hit(u,v+k)
            facade.append(bool(hit and hit[1][1]<=-.832))
            rear.append(bool(hit and hit[1][1]<-.37))
        def crossing(sweep):
            edges=[k-12-.5 for k in range(1,len(sweep)) if sweep[k-1] and not sweep[k]]
            return min(edges,key=abs) if edges else None
        arch.append(dict(photo_pixel=[u,v],front_lip_offset_px=crossing(facade),
                         clear_through_full_wall_offset_px=crossing(rear)))
    stair=[]
    for level in read(HERE/'south-garden-five-curved-steps.json')['steps']:
        for u,v in level['photo_pixels']:
            hits=[]
            for k in range(-5,6):
                hit=frame.hit(u,v+k)
                if hit and hit[0]==STONE and abs(hit[1][2]-level['z'])<.030:hits.append(k)
            stair.append(dict(level=level['level'],photo_pixel=[u,v],closest_nosing_offset_px=min(hits,key=abs) if hits else None))
    approach=[]
    for step in read(HERE/'south-garden-five-curved-steps.json')['steps']:
        a,b,c=step['coefficients_y_of_x']
        for dx in (-.65,0,.65):
            x=step['arc_mid_x_m']+dx;y=(a*dx+b)*dx+c
            hit=scene.ray([x,y-.43,step['z']-.075],[0,1,0],.75)
            approach.append(dict(level=step['level'],x_m=x,expected_front_y_m=y,
                                 actual=hit,passed=bool(hit and hit['material']==STAIR and
                                 abs(y-hit['point_enu_m'][1])<.04)))
    doors=[]
    layout=read(HERE.parent/'source/garden-layout.json')
    for key in ('garden_ground_doors','garden_upper_doors'):
        for i,(lo,hi,bottom,top) in enumerate(layout[key]):
            for part,expected,frac in [('stile',WOOD,.5),('pane',GLASS,.25),('other pane',GLASS,.75)]:
                z=bottom+(top-bottom)*.46
                hit=scene.ray([lo+(hi-lo)*frac,1.4,z],[0,1,0],1.7)
                doors.append(dict(row=key,index=i+1,part=part,expected_material=expected,
                                  measured_depth_m=round(hit['point_enu_m'][1],4) if hit else None,
                                  passed=bool(hit and hit['material']==expected)))
    through=[]
    for direction in (-1,1):
        for z in (2.2,2.55,2.85):
            origin=[19.5 if direction<0 else -.7,1.75,z]
            hit=scene.ray(origin,[direction,0,0],20)
            through.append(dict(origin=origin,direction_x=direction,passed=hit is None,first=hit))
    def stats(data,key):
        vals=[abs(r[key])for r in data if r[key] is not None]
        return dict(points=len(data),traced=len(vals),within_3px=sum(x<=3 for x in vals),
                    median_px=round(float(np.median(vals)),2) if vals else None)
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),photo_sha256=reg['camera_sha256'],
                arch_summary=stats(arch,'front_lip_offset_px'),clear_through_wall=stats(arch,'clear_through_full_wall_offset_px'),steps_summary=stats(stair,'closest_nosing_offset_px'),
                door_summary=[sum(r['passed']for r in doors),len(doors)],
                passage_summary=[sum(r['passed']for r in through),len(through)],
                approach_summary=[sum(r['passed']for r in approach),len(approach)],
                arch=arch,steps=stair,rear_wall=doors,passage=through,approach=approach)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path)
    args=p.parse_args();report=inspect(args.mesh);raw=(json.dumps(report,ensure_ascii=False,indent=1)+'\n').encode()
    args.out.write_bytes(gzip.compress(raw,mtime=0) if args.out.suffix=='.gz' else raw)
    print(report['arch_summary'],report['steps_summary'],report['door_summary'],report['passage_summary'])
