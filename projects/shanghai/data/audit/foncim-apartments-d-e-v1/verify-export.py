"""Check facade openings, setbacks and the public passage on the actual decoded model."""
import argparse
import json
import math
from pathlib import Path
import runpy

import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
MODEL=PROJECT/'source/precise/xuhui-foncim-apartments-d-e'
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
south_cases=runpy.run_path(MODEL/'source/south_rays.py')['south_cases']

def cases():
    records=[]
    def ray(name,p,d,length,material=None,limits=None):
        direction=np.asarray(d,dtype=float);direction/=np.linalg.norm(direction)
        records.append(dict(name=name,origin=[float(v)for v in p],direction=direction.tolist(),
                            length=length,allowed=[material] if material else None,range_m=limits))
    dims=json.loads((MODEL/'measurements/d-north-plan.json').read_bytes())
    head=dims['ground_head_m'];pitch=dims['upper_storey_m'];sill=head+.79
    for floor in range(4):
        for x,w,n in dims['street_window_centres_width_lights']:
            if floor==3 and x>24.60:continue
            y=-1.52 if abs(x)<13.22 else 0.
            z=sill+floor*pitch+.57
            balcony_door=2.4<abs(x)<4.1
            name=f'D floor {floor+2} street bay {x:+.2f}'
            ray(name+' glazing',(x+.175,y-.54,z),(0,1,0),.77,
                'D shaded glazing' if balcony_door else 'D desaturated window glass',[.681,.689])
            if balcony_door:continue
            pier_x=x+w/2+.12
            if x==-5.91:
                ray(name+' iron drainpipe',(pier_x,y-.54,z),(0,1,0),.60,'D iron drainpipe',[.458,.473])
                pier_x=x-w/2-.12
            ray(name+' plaster pier',(pier_x,y-.54,z),(0,1,0),.65,
                'Chestnut and warm ochre horizontal render',[.536,.544])
    for i in range(4):
        z=head+i*pitch
        for h in (-1,1):
            x=h*2.15
            ray(f'D balcony {i+1} front rail {h}',(x,-4.60,z+.83),(0,1,0),.80,'D dark terrace rail',[.655,.68])
            ray(f'D balcony {i+1} clear gap {h}',(x,-4.61,z+.735),(0,1,0),.85)
            ray(f'D balcony {i+1} warm base {h}',(x,-4.61,z+.26),(0,1,0),.77,'D buff cement',[.61,.64])
            ray(f'D balcony {i+1} cylindrical post {h}',(h*3.51,-3.5,z+1.44),
                (0,1,0),.8,'D buff cement',[.566,.59])
    for i,x in enumerate((-22.20,22.36,0)):
        y=0. if i!=2 else -1.52
        for j in range(4):
            ray(f'D stair {i+1} landing light {j+1}',(x+.625,y-1.31,head+.73+j*pitch),
                (0,1,0),.59,'D shaded glazing',[.49,.50])
        ray(f'D stair {i+1} entrance depth',(x+.20,y-1.20,1.19),(0,1,0),.73)
    for x,y,z,mat in [(-17.3,11,head+3*pitch,'D fine terrazzo'),
                        (29,7,head+3*pitch,'D fine terrazzo'),
                        (27.5,4,head+3*pitch,'D fine terrazzo'),
                        (2.2,5.2,head+4*pitch+.12,'D dark grey flat roof'),
                        (-16.9,5.2,head+4*pitch-.42,'D dark grey flat roof')]:
        ray('D top deck '+str((x,y)),(x,y,z+.47),(0,0,-1),.61,mat,[.46,.48])
    site=json.loads((MODEL/'measurements/site-frame.json').read_bytes())['old_floorplates']['E']
    origin=np.array(site['local_origin_xy']);angle=math.radians(site['local_rotation_degrees'])
    rot=np.array([[math.cos(angle),math.sin(angle)],[-math.sin(angle),math.cos(angle)]])
    for t in south_cases():
        x,y,z=t['origin'];u,v,h=t['direction'];start=np.array([x,y])@rot+origin
        a,b=np.array([u,v])@rot
        lo,hi=t['first_distance_m']
        ray(t['name'],[*start,z],(a,b,h),hi if t['material'] is None else hi+.03,
            t['material'],[lo,hi] if t['material'] else None)
    begin=np.array([0.,11.57]);end=np.array([0.,-1.64])@rot+origin
    near=end-begin;length=np.linalg.norm(near);near/=length;across=np.array([near[1],-near[0]])
    for i,t in enumerate(np.linspace(.64,length-.69,6)):
        a=begin+t*near
        for hand in (-1,1):
            d=hand*across
            ray(f'Court post pair {i+1} / {hand}',[*a,1.15],[*d,0],1.45,
                'Court russet round columns',[1.14,1.17])
        ray(f'Court underside pair {i+1}',[*a,1.45],[0,0,1],1.44,
            'Court ivory soffit',[1.375,1.385])
    for i,(x,z) in enumerate([(-.80,.54),(0.,.88),(.80,1.52),(.25,1.82),(-.52,2.15)]):
        a=begin+.55*near+x*across
        ray(f'Court uninterrupted pass to E door {i+1}',[*a,z],[*near,0],length-.80)
    for i in range(5):
        t=.64+(i+.5)*(length-1.33)/5
        a=begin+t*near
        for hand in (-1,1):
            ray(f'Court side gap {i+1} / {hand}',[*a,1.25],[*(hand*across),0],2.10)
    for x,y in [(7.85,23.5),(8.10,23.62)]:
        ray('Table disc '+str((x,y)),(x,y,1.05),(0,0,-1),.31,'Court aged timber',[.233,.241])
    for a in (.77,1.44,3.62,5.2):
        x=7.85+1.24*math.cos(a);y=23.5+1.24*math.sin(a)
        ray('Bench ring '+str(a),(x,y,.70),(0,0,-1),.30,'Court aged timber',[.218,.227])
    return records

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['raw','full','lod','output']:p.add_argument(name,type=Path)
    args=p.parse_args();tests=cases()
    result={v:inspect(getattr(args,v),tests) for v in ['raw','full','lod']}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in result.items():
        errors=[(t['name'],t['first_hit']) for t in r['cases'] if not t['passed']]
        print(role,len(tests),'failures',len(errors),errors,flush=True)
    return int(not all(v['passed']for v in result.values()))
if __name__=='__main__':raise SystemExit(main())
