"""Check the entrance in the serialized mesh using sections and archived camera pixels."""
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
import porch_columns as architecture

def inspect(mesh,anchor,far):
    a=architecture;scene=SerialScene(mesh);records=[];photographs=[];anchor=np.asarray(anchor,float)
    def cast(label,start,direction,length,mats,collection,meta=None):
        hit=scene.ray(np.asarray(start)+anchor,np.array(direction,float),length)
        row={'label':label,'expected':list(mats),'actual':hit['material'] if hit else None,
             'start_local_m':np.round(start,5).tolist(),'direction':np.round(direction,5).tolist()}
        row['passed']=row['actual'] in mats
        if meta:row.update(meta)
        collection.append(row)
    for hand,cx in [('left',-.345),('right',3.291)]:
        for z,rad,mat in [(-2.14,.344,a.GRANITE),(-2.025,.337,a.GRANITE),(-1.921,.329,a.GRANITE),
                          (-1.827,.296,a.GRANITE),(-1.65,.251,a.CUT),(-1.27,.246,a.CUT),
                          (-.91,.24,a.CUT),(-.57,.234,a.CUT),(-.439,.270,a.CUT)]:
            for angle in np.linspace(-1.54,.02,7):
                normal=np.array([math.cos(angle)*(1 if hand=='left' else -1),math.sin(angle),0])
                origin=np.array([cx,.354,z])+normal*(rad+.030)
                cast(hand+' turned profile '+str(z),origin,-normal,.065,[mat],records)
        for z,half in [(-.030,.348),(-.090,.287),(-.160,.261),(-.194,.255)]:
            for u in np.linspace(-.6,.6,5):
                cast(hand+' square cap at '+str(z),[cx+u*half,.354-half-.024,z],[0,1,0],.061,[a.CUT],records)
        for x,y,rx,ry,z in [(-.642,.161,.095,.166,-.931),(-.626,.175,.079,.142,-.648),(-.613,.182,.065,.124,-.518)]:
            actual_x=x if hand=='left' else 2.946-x
            cast(hand+' secondary stone post',[actual_x,y-ry-.030,z],[0,1,0],.092,[a.GRANITE],records)
    cx,rx,rz,base=1.4925,1.6034,.9752,.0175
    bands=[(0,.147,.211),(.147,.158,.154),(.158,.180,.144),(.180,.222,.158),
           (.222,.265,.161),(.265,.313,.089),(.313,.376,.088),(.376,.437,.066),(.437,.496,.049)]
    for b,(a0,a1,y) in enumerate(bands):
        n=33 if far else round((3.96+math.pi*(a0+a1)/2)/(.129 if b<4 else .073))
        for j in range(n):
            t=(j+.5)*math.pi/n
            if abs(t-math.pi/2)<.178:continue
            c,s=math.cos(t),math.sin(t);l=math.hypot(rz*c,rx*s);r=(a0+a1)/2
            x=cx+rx*c+r*rz*c/l;z=base+rz*s+r*rx*s/l
            mat=a.TERRA if b in (0,1,3) else a.ARCH_BRICK[(b*3+j+j//6)%4]
            cast('arch ring '+str(b+1)+' block '+str(j+1),[x,y-.035,z],[0,1,0],.09,[mat],records)
    for k in range(6):
        t=math.pi*(k+.55)/6;c,s=math.cos(t),math.sin(t);l=math.hypot(rz*c,rx*s)
        nor=np.array([rz*c/l,0,rx*s/l]);q=np.array([cx+rx*c,.450,base+rz*s])
        cast('brick intrados '+str(k+1),q-.030*nor,nor,.061,a.ARCH_BRICK,records)
    for u,z in [(1.476,1.470),(1.350,1.220),(1.595,1.130),(1.453,1.582)]:
        cast('central tapered keystone',[u,-.081,z],[0,1,0],.13,[a.TERRA,a.RUSSET],records)
    for x in [1.05,1.96]:
        for z in [-1.77,-.53]:cast('raised centre door panel',[x,1.74,z],[0,1,0],.16,[a.PANEL],records)
    floor=json.loads((HERE/'tiled-pavement.json').read_text())
    for col in range(-1,7):
        for row in [-2,-1,0]:
            x=.226+.486*col;y=1.181+.466*row
            if not (x>.366 and x<2.678 or y>1.0):continue
            for dx,dy,mat in [(0,0,a.BROWN if not far else a.OCHRE),(.12,0,a.GREEN),(.10,.08,a.BROWN)]:
                if not (.366<x+dx<2.678 or y+dy>.997):continue
                cast('flower '+str((col,row))+' offset '+str((dx,dy)),[x+dx,y+dy-.028*(x+dx),a.FLOOR+.036],[0,0,-1],.07,[mat],records)
    controls=json.loads((HERE/'porch-reference-pixels.json').read_text())
    for name,groups in controls.items():
        p=np.array(json.loads((HERE/name).read_text())['P']);inv=np.linalg.inv(p[:,:3]);eye=-inv@p[:,3]
        for g in groups:
            for uv in g['uv']:
                cast(g['feature'],eye,inv@[*uv,1],30,g['materials'],photographs,{'camera':name,'native_pixel':uv})
    s=lambda rows:sum(q['passed'] for q in rows)
    return dict(asset=scene.asset,physical={'passed':s(records),'total':len(records),'probes':records},
                photographed={'passed':s(photographs),'total':len(photographs),'probes':photographs})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--lod',action='store_true');p.add_argument('--standalone',action='store_true')
    q=p.parse_args();report=inspect(q.mesh,[0,0,0] if q.standalone else [-1.54,-.04,1.86],q.lod)
    q.output.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
    for g in ['physical','photographed']:
        d=report[g];print(g,d['passed'],d['total'],[(o['label'],o.get('native_pixel'),o['actual']) for o in d['probes'] if not o['passed']][:24])
    raise SystemExit(int(report['physical']['passed']!=report['physical']['total']))
