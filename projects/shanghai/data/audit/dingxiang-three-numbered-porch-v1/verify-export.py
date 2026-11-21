"""Check each tread, the numbered brass plate, timber slots, off-centre doorway and rings of twisted iron."""
from pathlib import Path
from math import cos, pi, sin
import argparse
import json
import runpy

HERE=Path(__file__).resolve().parent
trace=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    from math import hypot, sin, pi
    out=[]
    def ray(name,origin,direction,material=None,limits=None,length=5.5):
        out.append(dict(name=name,origin=list(origin),direction=list(direction),length=length,allowed=None if material is None else [material],range_m=limits))
    def front(name,x,z,material,limits=None): ray(name,(x,-3,z),(0,1,0),material,limits)
    for level in range(5):
        # The heights and centres are rounded independently from the stereo survey.
        heights=(.862,.680,.468,.253,.070)
        centres=(-.380,-.778,-1.100,-1.409,-1.822)
        bows=(.099,.274,.327,.254,.211)
        z=heights[level]
        yy=(-.2,-.56,-.91,-1.25,-1.59)[level]
        for xx in (-.38,.06,.62):
            ray(f'Curved step level {5-level} at {xx}',(xx,yy,2),(0,0,-1),'Grey granolithic treads',[2-z-.006,2-z+.006])
        for xx in (0,-1.2672,1.2672):
            expected=2.36+centres[level]+(bows[level] if xx else 0.)
            ray(f'Stereo bow of nose {level+1} at {xx}',(xx,-2.36,z-.027),(0,1,0),'Grey granolithic treads',[expected-.018,expected+.018])
    ray('Paving beyond the first tread',(0,-1.84,2),(0,0,-1))
    # Start below the hanging lamp and use separate pixels of both large floor fields, the border and the stone nosing.
    for x,y,finish,expected in ((-.41,.57,'Terracotta porch floor',.232),(.84,.34,'Burgundy entrance runner',.229),
                                (-.75,.032,'Grey granolithic treads',.238),(-1.44+5*.138,.1215,'Ochre border lozenges',.229)):
        ray(f'Porch floor finish {finish}',(x,y,1.10),(0,0,-1),finish,[expected-.003,expected+.003])
    for side in (-1,1):
        cx=side*1.745
        for j,offset in enumerate((-.30,-.10,.10,.30)):
            front(f'Screen {side}, post {j+1}',cx+offset,2.66,'Brown porch timber',[2.85,2.87])
        for j,offset in enumerate((-.20,0,.20)):
            front(f'Screen {side}, true opening {j+1}',cx+offset,2.66,'Warm exposed river pebbles',[4.55,4.57])
        front(f'Stone plinth under screen {side}',cx,.81,'Grey granolithic treads',[2.76,2.80])
        front(f'Outer pebbled jamb {side}',side*2.43,2.79,'Warm exposed river pebbles',[2.87,2.90])
        front(f'Square metal downpipe {side}',side*2.681,2.79,'Brown metal gutters',[2.77,2.80])
        front(f'Open air beyond the jamb {side}',side*3.00,2.77,None)
    front('Upper painted stroke of figure three',-1.745-.14,3.51+.118,'Shadow inside rear doorway',[2.82,2.84])
    front('Unpainted corner of address plate',-1.745+.215,3.51+.185,'Number and brass plates',[2.83,2.85])
    front('Small brass plaque on left post',-1.745,2.28,'Number and brass plates',[2.82,2.86])
    front('Shaded opening of the offset arched door',.78,2.34,'Shadow inside rear doorway',[4.79,4.82])
    front('Upper arc of the rear architrave',.78,3.041,'Dark stained doorframe',[4.50,4.53])
    # Probe from inside the opening at the front edge of the jamb, obliquely into both deep reveals.
    for side in (-1,1):
        ray(f'Continuous inner arch jamb {side}',(.78+side*.48,1.57,1.8),(side,0,0),'Dark stained doorframe',[.032,.043],.15)
        ray(f'Third tread in front of the pier {side}',(side*1.745,-1.0,.42),(0,1,0),'Grey granolithic treads',[.466,.488],1)
        ray(f'Solid stone plinth under a timber screen {side}',(side*1.745,-1.0,.80),(0,1,0),'Grey granolithic treads',[.768,.782],1)
        ray(f'Covered paving outside doorway width {side}',(side*2.06,.70,1.21),(0,0,-1),'Grey granolithic treads',[.34,.36],.6)
    front('Front wall above the rear arch',.78,3.14,'Warm exposed river pebbles',[4.55,4.57])
    front('Rear wall at left of the doorway',-.52,2.41,'Warm exposed river pebbles',[4.55,4.57])
    front('Wood backrest below open porch',-.76,.862+.49+2*.074,'Brown porch timber',[4.33,4.37])
    front('Front head beam in the middle',0,3.81,'Brown porch timber',[2.80,2.83])
    front('Green fascia below tile rolls',0,4.065,'Deep green eaves',[2.64,2.69])
    front('Brown gutter in front of fascia',0,4.147,'Brown metal gutters',[2.62,2.66])
    for side in (-1,1):
        def grip(t):
            flare=.24*t+.76*t*t
            return [side*(1.408+.6999*flare),-.4093-1.0117*t,1.6503-.6691*t]
        feet=[.704,.277,.024]
        stations=(0.,.5553,1.)
        for j,t in enumerate(stations):
            xx,yy,zz=grip(t)
            ray(f'Top of curved handrail {side}/{j}',(xx,yy,zz+.3),(0,0,-1),'Mahogany handrails',[.25,.28])
        for j,(ta,tb) in enumerate(zip(stations,stations[1:])):
            a=grip(ta);b=grip(tb);dx,dy=b[0]-a[0],b[1]-a[1];length=hypot(dx,dy);normal=(-dy/length,dx/length,0.)
            centre=[(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2]-.18+feet[j]+feet[j+1]+.24)/4]
            source=[centre[i]-.22*normal[i] for i in range(3)]
            ray(f'Open centre of iron ring {side}/{j}',source,normal,length=.44)
            source[2]+=.093
            ray(f'Upper rim of iron ring {side}/{j}',source,normal,'Black twisted iron',[.196,.242],.44)
    return out

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
