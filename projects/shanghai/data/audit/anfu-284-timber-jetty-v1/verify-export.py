"""Check the solid boards, independent pebble panels, bracket, exposed joists and set-back window pairs."""
from pathlib import Path
from math import cos, pi, sin
import argparse
import json
import runpy

HERE=Path(__file__).resolve().parent
trace=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    dims=json.loads((HERE.parents[2]/'source/precise/xuhui-anfu-284-timber-jetty/measurements/two-face-proportions.json').read_bytes())['adopted_m']
    wide=dims['east_panel_width'];depth=dims['return_depth'];base=dims['projected_footing_above_ground'];storey=dims['lower_timber_panel_height']
    half=wide/2
    tests=[]
    def ray(name,origin,direction,mat=None,limits=None):
        tests.append(dict(name=name,origin=list(origin),direction=list(direction),length=5.5,
                          allowed=[mat]if isinstance(mat,str)else mat,range_m=limits))
    def front(name,x,z,mat=None,limits=None):
        ray(name,(x,-3,z),(0,1,0),mat,limits)
    for i in range(8):
        u=-half+i*wide/7
        front(f'Lower vertical stud {i}',u,base+.75*storey,'Weathered chestnut studs',[1.81,1.83])
    for i in range(7):
        u=-half+(i+.5)*wide/7
        front(f'Lower dark pebble field {i}',u,base+.73*storey,'Dark washed pebble aggregate',[1.89,1.91])
        front(f'Middle red rail {i}',u,base+0.64*storey,'Oxide red rails',[1.79,1.81])
    for i in range(6):
        u=-half+i*wide/5
        front(f'Upper stud {i}',u,base+storey+1.32,'Weathered chestnut studs',[1.81,1.84])
    front('Lighter repaired panel above the horizontal band',-half+3.5*wide/5,base+storey+.42,
          'Pale repaired infill',[1.87,1.89])
    for side in (-1,1):
        a=side*(half-.067);b=side*(half-1.76*wide/7)
        # A vertical timber crosses the brace at midspan and stands 13.5 mm proud of it.
        front(f'Post in front of lower brace {side}',(a+b)/2,base+(.10+.64*storey-.035)/2,
              'Weathered chestnut studs',[1.812,1.825])
        for ratio in (.30,.70):
            front(f'Exposed diagonal {side} at {ratio}',a+(b-a)*ratio,base+.10+ratio*(.64*storey-.135),
                  'Oxide red rails',[1.825,1.840])
    for i in range(1,3):
        y=-depth*i/3
        ray(f'Painted return stud {i}',(-3,y,base+.72*storey),(1,0,0),'Weathered chestnut studs',[1.74,1.77])
    for yy in (-.24,-.59,-.85):
        # The independent quarter-section calculation predicts the underside of the one curved bracket.
        from math import sqrt
        aa=-.11+.40-depth+.08
        bb=2*(-.20+.11)
        cc=-.11-yy
        t=(-bb-sqrt(bb*bb-4*aa*cc))/(2*aa)
        top=base-.231
        z=(1-t)**2*(top-.86)+2*(1-t)*t*(top-.21)+t*t*(top-.095)
        ray(f'Concave south bracket at y={yy}',(-half+.095,yy,1.75),(0,0,1),'Oxide red rails',[z-1.75-.015,z-1.75+.015])
    for i in range(1,7):
        xx=-half+i*wide/6
        ray(f'Underside of projecting joist {i}',(xx,-.54,2),(0,0,1),'Oxide red rails',[base-.271-2,base-.266-2])
    for i in range(1,6):
        xx=-half+(i+.5)*wide/6
        ray(f'Boarding inside joist gap {i}',(xx,-.54,2),(0,0,1),'Dark timber end grain',[base-.150-2,base-.145-2])
    for u in (-.71,0,.71):
        front('Set-back wall under projection '+str(u),u,1.68,'Dark washed pebble aggregate',[2.99,3.01])
    for row,(low,high) in enumerate([(.65,2.0),(3.84,5.62),(6.94,8.48)]):
        sash_top=high-.21 if row==1 else high
        for side in (-1,1):
            mid=half+1.10+side*.47
            for j in range(4):
                u=mid-.355+(j+.5)*.71/4
                h=low+1.5*(sash_top-low)/5
                front(f'Window {row}/{side} four-column light {j}',u,h,['Pale reflected sky','Grey green glass'],[2.05,2.08])
                if row==1:
                    front(f'Middle transom divided light {side}/{j}',u,high-.10,'Grey green glass',[2.06,2.09])
            front(f'Window {row}/{side} centre stile',mid,low+1.5*(sash_top-low)/5,'Red brown sash frames',[1.97,2.01])
            # Three interior samples distinguish the recessed head rail, the narrow masonry strip and its projecting stone cap.
            front(f'Window {row}/{side} head rail',mid+.055,high-.012,'Red brown sash frames',[1.97,2.01])
            front(f'Window {row}/{side} masonry over aperture',mid+.055,high+.009,'Dark washed pebble aggregate',[1.89,1.91])
            front(f'Window {row}/{side} projecting lintel',mid+.055,high+.064,'Grey stone window sills',[1.69,1.72])
    for fraction in (.22,.47,.84):
        front(f'Upper red crossbar at {fraction}',-half+fraction*wide,base+storey+1.47,'Oxide red rails',[1.79,1.82])
    for u in (half-.36,half+.31,half+.84,half+1.80):
        front(f'Horizontal gable plate continuing over the paired windows at {u:.2f}',u,base+storey+2.89,'Oxide red rails',[1.80,1.83])
    front('Stone pier between the middle double casements',half+1.10,4.67,'Dark washed pebble aggregate',[1.89,1.91])
    for xx in (-half-.34,half+3.22):
        front('Outer limit '+str(round(xx,2)),xx,4)
    return tests

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('raw','full','lod','output'):
        parser.add_argument(key,type=Path)
    args=parser.parse_args()
    result={role:trace(getattr(args,role),cases())for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    for role,row in result.items():
        print(role,len(row['cases']),[(v['name'],v['first_hit']) for v in row['cases']if not v['passed']],flush=True)
    raise SystemExit(not all(row['passed']for row in result.values()))
