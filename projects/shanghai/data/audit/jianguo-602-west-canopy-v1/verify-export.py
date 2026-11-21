"""Trace the actual decoded steps, folded canopy and open gates of the west entrance.

Coordinates are X along the wall to the right, +Y inside and Z up. Each
walk-through segment ends within the photographed vestibule.
"""
import argparse
import json
import math
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
inspect = runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
STONE='Grey dressed granite'
GROOVE='Cut stone grooves'
SEAM='Dark green folded steel'
EDGE='Green enamel edges'
SHEET='Green painted sheet metal'
IRON='Deep green iron gate'
JAMB='Cream moulded portal'


def cases():
    tests=[]

    def ray(name, point, direction, reach, material=None, span=None):
        norm=math.sqrt(sum(v*v for v in direction))
        tests.append(dict(name=name,origin=list(point),direction=[v/norm for v in direction],
                          length=reach,allowed=[material] if material else None,range_m=span))

    def down(name, point, height, material, start=.67):
        travel=start-height
        ray(name,(*point,start),(0,0,-1),travel+.02,material,[travel-.005,travel+.005])

    radius=1.17
    cusp=.49*radius
    cy=-.318*cusp
    inner=.220*cusp
    phase=math.radians(-.97)
    pitch=math.radians(8.38)

    def polar(a,r):
        return (r*math.sin(a),cy-r*math.cos(a))

    # On the stone circle, raised visibility of a groove is only 1.52 mm. Test
    # material as well as first intersection, with bare neighbouring points.
    down('Disc / plain stone centre',(0,cy),.28,STONE)
    # Additional first hits across the photographed fracture and the neighbouring polished granite.
    for i, (x,y) in enumerate(((.092541,-.174882),(.048419,-.175799),(-.010318,-.164965),(-.054516,-.162222))):
        down(f'Stone fissure / observed dark core {i}',(x,y),.28072,'Weathered granite fissure')
        down(f'Stone fissure / adjacent unbroken grain {i}',(x,y+.009),.28,STONE)
    for deg in (-135,-85,-30,0,37,86,128):
        a=math.radians(deg)
        down(f'Disc / engraved ring {deg}',polar(a,inner),.281521,GROOVE)
        down(f'Disc / plain stone inside ring {deg}',polar(a,inner-.024),.28,STONE)
    for i in range(-10,11):
        a=phase+pitch*i
        down(f'Fan / engraved radial line {i}',polar(a,.67*cusp),.281521,GROOVE)
        down(f'Fan / plain stone between lines {i}',polar(a+.35*pitch,.67*cusp),.28,STONE)
    for i in range(-9,9):
        a=phase+pitch*(i+.5)
        down(f'Fan / rounded petal tip {i}',polar(a,1.038*cusp),.281521,GROOVE)
        longer=i%2==1
        down(f'Fan / alternate outer field {i}',polar(a,.74*radius),.281521 if longer else .28,GROOVE if longer else STONE)
    for sign in (-1,1):
        down(f'Stair / lower exposed tread {sign}',(sign*.51,-1.31),.145,STONE)
        down(f'Stair / upper exposed tread {sign}',(sign*.88,-.68),.28,STONE)
    ray('Stair / clear of lower curved nose',(.97,-1.51,.51),(0,0,-1),.48)

    # The observed radius of the sheet is different at each elevation. Shoot
    # horizontally, radially in or out, through the eave and across the folds.
    def radial(name,a,source,target,z,material=None,r_bounds=None):
        x,y=1.17*math.cos(a),-1.22*math.sin(a)
        length=math.hypot(x,y)
        direction=1 if target>source else -1
        span=sorted(abs(source-r)*length for r in r_bounds) if r_bounds else None
        ray(name,(source*x,-.014+source*y,z),(direction*x,direction*y,0),abs(target-source)*length,material,span)

    for i in range(36):
        radial(f'Eave / underside of pendant {i+1:02}',(i+.5)*math.pi/36,1.075,.965,3.844,EDGE,[.997,1.005])
        if i:
            radial(f'Eave / open notch between pendants {i:02}',i*math.pi/36,1.075,.963,3.844)
    for z,r in [(4.265,.588),(4.888,.290)]:
        for i in range(9):
            radial(f'Canopy / standing seam {i+1} at {z}',i*math.pi/8,r+.13,r-.11,z,SEAM,[r-.020,r+.045])
        for i in range(8):
            a=(i+.5)*math.pi/8
            radial(f'Canopy / painted outer sheet {i+1} at {z}',a,r+.14,r-.10,z,SHEET,[r-.035,r+.043])
            radial(f'Canopy / reverse of sheet {i+1} at {z}',a,r-.13,r+.10,z,SHEET,[r-.055,r+.035])
    for x,y in [(0,-.71),(.51,-.41),(-.73,-.34)]:
        ray(f'Canopy / sheltered soffit {x}',(x,y,3.44),(0,0,1),.60,'Shadowed metal soffit',[.44,.46])
    ray('Canopy / air beyond the bowed eave',(.68,-1.15,3.44),(0,0,1),.86)
    # The projecting parapet cap masks the finial from directly above.
    ray('Terrace / parapet above the finial',(0,-.020,5.93),(0,0,-1),.51,JAMB,[.016,.025])
    ray('Terrace / lower cornice over crown',(0,-.020,5.70),(0,0,-1),.21,JAMB,[.073,.077])
    ray('Canopy / exposed half finial seen from street',(0,-.600,5.540),(0,1,0),.61,EDGE,[.520,.526])
    ray('Door head / segment recessed behind plaster',(0,-.62,3.73),(0,1,0),1.01,'Recessed ochre door head',[.748,.762])
    for sign in (-1,1):
        x=sign*1.045
        # The rising strut crosses the middle of the shoe; sample its open shoulder separately.
        ray(f'Bracket / rising strut in front of shoe {sign}',(x,-.49,3.70),(0,1,0),.55,SEAM,[.235,.253])
        ray(f'Bracket / stepped horizontal shoe {sign}',(x+sign*.050,-.49,3.70),(0,1,0),.55,EDGE,[.292,.314])
        ray(f'Bracket / rising strut {sign}',(x,-.49,3.625),(0,1,0),.55,SEAM,[.295,.445])

    # Follow the leaf itself in plan. The near hinge stile and its remote latch
    # stile are two distinct first hits from the central open passage.
    width=.697
    turn=math.radians(78)
    for sign in (-1,1):
        for name,t,z in [('hinge stile',.022,1.76),('latch stile',width-.022,1.76),
                         ('middle picket',width/2,1.88),('solid kick plate',width*.32,.49),
                         ('horizontal rail',width*.38,1.17)]:
            x=.683-t*math.cos(turn)
            y=.085+t*math.sin(turn)
            ray(f'Gate {sign} / {name}',(0,y,z),(sign,0,0),x+.065,IRON,[x-.041,x+.012])
        y=.085+width*.331*math.sin(turn)
        ray(f'Gate {sign} / opening in grille',(0,y,1.93),(sign,0,0),.708)
        for off,front in [(.022,.045),(.071,-.016),(.133,-.056)]:
            ray(f'Jamb {sign} / stepped mould {off}',(sign*(.72+off),-.63,1.56),(0,1,0),.81,JAMB,[.63+front-.007,.63+front+.007])
        ray(f'Jamb {sign} / square plinth block',(sign*.817,-.63,.62),(0,1,0),.8,JAMB,[.54,.565])
    for x in (-.445,-.20,0,.20,.445):
        for z in (.46,1.18,2.10):
            ray(f'Entrance / open passage {x},{z}',(x,-1.38,z),(0,1,0),2.45)
    for x in (-.27,.13,.51):
        ray(f'Transom / recessed pane {x}',(x,-.65,2.99),(0,1,0),1.1,'Smoky interior transom',[.948,.968])
    for x in (-.3816,0,.3816):
        ray(f'Transom / metal mullion {x}',(x,-.65,2.99),(0,1,0),1.1,IRON,[.897,.914])
    down('Entrance / dark threshold strip',(.21,-.015),.294,'Dark steel hardware')
    down('Entrance / red clay paver',(.20,.23),.2835,'Old square clay tiles')
    down('Entrance / ochre clay paver',(.52,.36),.2835,'Yellow clay tile')
    for x in (-1.68,1.58):
        ray(f'Facade / ochre stucco {x}',(x,-.57,2.44),(0,1,0),.66,'Pale ochre cement render',[.562,.578])
        ray(f'Facade / contrasting plinth {x}',(x,-.57,.31),(0,1,0),.6,'Grey cement plinth',[.515,.533])
    return tests


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for role in ('raw','full','lod','output'):
        parser.add_argument(role,type=Path)
    args=parser.parse_args()
    probes=cases()
    results={role:inspect(getattr(args,role),probes) for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=1)+'\n')
    for role,row in results.items():
        failed=[(p['name'],p['first_hit']) for p in row['cases'] if not p['passed']]
        print(role,len(probes),'failures',len(failed),failed,flush=True)
    return 0 if all(result['passed'] for result in results.values()) else 1


if __name__=='__main__':
    raise SystemExit(main())
