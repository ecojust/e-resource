"""Check the first actual GLB triangle in the public lane and at the two street fronts."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene


def check(path,period):
    scene=SerialScene(path)
    layout=json.loads((HERE.parent/'source/gatehouse-layout.json').read_bytes())
    f=layout['front_y'];cases=[]
    def sample(tag,origin,ray,length,allowed=(),contains=None):
        hit=scene.ray(origin,ray,length)
        actual=hit['material'] if hit else None
        ok=(actual is None) if not allowed and not contains else (actual is not None and (actual in allowed or (contains and contains in actual)))
        cases.append({'check':tag,'origin':origin,'direction':ray,'range_m':length,'hit':hit,'expected':list(allowed) or contains,
                      'passed':bool(ok)})
    for x in (2.12,2.62,3.12,3.62,4.07):
        for z in (.45,.90,1.45,1.83,2.20):
            sample('clear path street to north', [x,-.33,z],[0,1,0],16.90)
            sample('clear path north to street', [x,16.57,z],[0,-1,0],16.90)
    lookup=json.loads((HERE/'registered-east-shopfronts.json').read_bytes())['periods'][period]
    for n,(left,low,right,high,finish) in enumerate(lookup['fascias']):
        for u,v in ((.18,.26),(.56,.68),(.81,.37)):
            sample(f'shop {n+1} fascia', [left+(right-left)*u,-.60,low+(high-low)*v],
                   [0,1,0],1.4,['Hengchang shop | '+finish,'Hengchang shop | joint'])
    old=period=='2018'
    for x in (.34,5.93):
        for z in (.89,1.35,2.71,3.31,4.28):
            sample('front pier facing',[x,-.8,z],[0,1,0],1.3,
                   ['Gatehouse | warm mineral render'] if old else ['Gatehouse | grey reclaimed brick'])
    # Trace the two dates' upper openings from the upright Commons source.
    source=json.loads((HERE/'upper-sashes-and-street-sign-line.json').read_bytes())
    for name,win in source['windows'].items():
        H=np.asarray(layout['native_to_xz'][win['face']])
        if name=='tower' and not old:
            recent=json.loads((HERE/'refurbished-tower-window.json').read_bytes())['west_2021']
            H=np.asarray(recent['native_to_xz'])
            a,b,c,d=np.asarray([v['uv'] for v in recent['upper_window_four_corners_clockwise']])
        elif 'sash_quad' in win:
            a,b,c,d=np.asarray(win['sash_quad'])
        else:
            a,b=np.asarray(win['transom']);d,c=np.asarray(win['sill'])
        for u in (.14,.37,.69,.87):
            uv=(1-.59)*((1-u)*a+u*b)+.59*((1-u)*d+u*c)
            q=H@[*uv,1];x,z=(q[:2]/q[2]).tolist()
            y=f[win['face']]
            sample(name+' sash at dated photo coordinate',[x,y-.11,z],[0,1,0],.49,contains='Hengchang windows |')
    return {'input':scene.asset,'period':period,'rays':cases,'counts':{group:{
        'passed':sum(c['passed']for c in cases if c['check']==group),'total':sum(c['check']==group for c in cases)}
        for group in dict.fromkeys(c['check']for c in cases)}}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=Path);p.add_argument('--period',required=True,choices=['2018','2022'])
    p.add_argument('--out',required=True,type=Path);args=p.parse_args();result=check(args.file,args.period)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(sum(v['passed']for v in result['rays']),len(result['rays']))
