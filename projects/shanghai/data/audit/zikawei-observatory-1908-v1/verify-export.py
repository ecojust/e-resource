"""Trace the documented registers, openings and solid supports through the exported observatory."""
import argparse
import json
import math
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
GREY='Observatory grey brick'
STONE='Warm grey carved stone'
RED='Oxide red trim brick'
GLASS='Smoked window glass'
IVORY='Limestone and limewashed joinery'
DIAL='Weathered ivory clock dial'
METAL='Dark metal clock and rail'


def cases():
    checks=[]
    def test(name,p,d,material=None,dist=None,length=1.3):
        checks.append(dict(name=name,origin=p,direction=d,length=length,
                           allowed=[material] if isinstance(material,str) else material,range_m=dist))
    def front(name,x,face,z,material,dist,length=1.3):
        test(name,[x,face-.68,z],[0,1,0],material,dist,length)
    def above(name,x,y,z,material,dist,length=2):
        test(name,[x,y,z],[0,0,-1],material,dist,length)
    for block,x0,x1,y,eave,fraction,off in [('West pavilion',-22.60,-13.,0.,11.77,.25,.14),
            ('West link',-13.,-3.80,3.40,11.41,.23,0.),
            ('East link',3.90,13.10,3.40,11.41,.23,0.),
            ('East pavilion',13.10,23.80,0.,11.77,.207,.45)]:
        width=x1-x0;middle=(x0+x1)/2
        for hand in [-1,1]:
            x=middle+off+hand*width*fraction;tag=f'{block} {hand}'
            for sill,spring,winw,storey in [(.35,1.26,1.42,'Base'),(3.43,4.72,1.80,'Lower'),(7.76,9.45,1.80,'Upper')]:
                # Sample away from the quarter-width glazing mullions at both detail levels.
                front(f'{tag} {storey} glass',x+.29,y,sill+.35,GLASS,[.974,.986])
                front(f'{tag} {storey} vertical window bar',x,y,sill+.25,IVORY,[.823,.833])
                front(f'{tag} {storey} arched crown',x,y,spring+winw/2+.091,
                      STONE if storey=='Base' else RED,[.568,.582])
                front(f'{tag} {storey} windowsill',x+.24,y,sill-.08,STONE,[.330,.35])
            front(tag+' recessed tablet centre',x,y,6.72,GREY,[.532,.544])
            front(tag+' tablet frame',x+.02,y,6.72+.40,RED,[.463,.479])
            front(tag+' wall outside opening',x-hand*1.85,y,7.12,GREY,[.676,.684])
        for hand in [-1,1]:
            x=middle+hand*(width/2-.27)
            front(block+' red brick pilaster '+str(hand),x,y,5.55,RED,[.451,.510])
        front(block+' upper cornice',middle,y,eave-.12,STONE,[.404,.417])
        above(block+' hipped roof',middle,y+2.5,eave+2.80,'Dark pitched roof',[.50,2.8],3.0)

    width=7.70;cx=.05;cy=-1.52+width*.52
    clockfront=cy-width*.47
    for z,mat,name in [(18.49,DIAL,'pale clock upper face'),(16.92,DIAL,'pale clock lower face'),
                        (17.63,METAL,'clock central pin')]:
        front(name,cx+(.23 if mat==DIAL else 0),clockfront,z,mat,[.425,.536])
    for ang in (0,30,60,90,120,150,180,210,240,270,300,330):
        a=math.radians(ang);r=min(width*.186,1.43)-.14
        front('Hour index '+str(ang),cx+r*math.sin(a),clockfront,17.63+r*math.cos(a),METAL,[.504,.514])
    for ang in (28,77,119,172,245,281,319):
        a=math.radians(ang);r=min(width*.186,1.43)+.075
        front('Outer bezel '+str(ang),cx+r*math.sin(a),clockfront,17.63+r*math.cos(a),METAL,[.45,.466])
    front('Clock room sash',cx+.20,clockfront,12.91,GLASS,[.974,.986])
    lookout=cy-width*.392
    front('Upper lookout sash',cx+.27,lookout,27.12,GLASS,[.974,.986])
    for level in (22.48,23.95,25.03):
        front('Solid shoulder above clock '+str(level),cx,cy-width*.405,level,
              [GREY,RED,STONE],[.35,.69])
    front('Rounded masonry moulding over pediment crown',cx,cy-width*.405,24.54,
          STONE,[.091,.110])
    for x in [-2.35,-1.66,-.64,.64,1.66,2.35]:
        front('Shoulder across upper room base '+str(x),cx+x,cy-width*.405,25.03,
              GREY,[.674,.686])
    for hand in [-1,1]:
        for x in [.64,1.58,2.50]:
            above(f'Top of neck {hand} {x}',cx+hand*x,cy,26.00,STONE,[.31,.34])
    # The two stair flights rise from the wings towards the entrance landing.
    y=-1.52-1.21
    for hand in [-1,1]:
        for i in (1,4,7,11,15,19,21):
            x=hand*(3.25+6.18*(i+.5)/22)
            expected=3.18*(22-i)/22
            above(f'Tread {hand} {i+1}',x,y,expected+.40,STONE,[.395,.405],.50)
    for x in [-1.9,-.83,.83,1.9]:
        above('Upper landing '+str(x),x,y,3.51,STONE,[.325,.335])
    for hand in (-1,1):
        front(f'Entrance ashlar jamb {hand}',hand*1.91-.23,-1.52,3.98,IVORY,[.423,.468])
    for angle in (24,47,78,103,146,164):
        a=math.radians(angle)
        front(f'Radiating entrance stone {angle}',1.82*math.cos(a),-1.52,5.42+1.82*math.sin(a),
              [STONE,IVORY],[.398,.498])
    front('Deep recess behind the door',0,-1.52,4.15,'Deep opening shadow',[2.71,2.75],2.90)
    # These bounds distinguish the free-standing first-stage tower from the later iron frame.
    for x in [-8.5,-6.3,6.6,8.2]:
        test('Clear space beside upper lookout '+str(x),[x,-2.9,28.2],[0,1,0],None,None,11.)
    return checks


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):parser.add_argument(key,type=Path)
    a=parser.parse_args();result={r:inspect(getattr(a,r),cases())for r in ('raw','full','lod')}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for role,scan in result.items():print(role,len(scan['cases']),[(r['name'],r['first_hit'])for r in scan['cases']if not r['passed']])
    raise SystemExit(int(not all(k['passed']for k in result.values())))
