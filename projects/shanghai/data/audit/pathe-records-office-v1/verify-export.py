"""Trace the four photographed façades of the former Pathé offices in three decoded meshes.

The points use the survey frame in building-dimensions.json. Positive X points
to the viewer's right from the north entrance. Positive Y points into the house.
Each bounded empty segment stops in front of the next documented surface.
"""
import argparse
import json
import math
from pathlib import Path
import runpy


HERE = Path(__file__).resolve().parent
trace = runpy.run_path(HERE.parent / 'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
STONE = 'Warm dressed stone'
WHITE = 'Warm white enamel'
BRICK = 'Pathe red stretchers'
GLASS = 'Daylit glazing'
FRAME = 'Dark window frames'
IRON = 'Forged metal'
CLAY = 'Old roof clay'


def cases():
    tests = []

    def ray(name, position, direction, reach, material=None, interval=None):
        allowed = [material] if isinstance(material, str) else material
        tests.append(dict(name=name, origin=list(position), direction=list(direction),
                          length=reach, allowed=allowed, range_m=interval))

    def north(name, x, z, material, distance, tol=.016, y=-2.50):
        ray('North / '+name, (x, y, z), (0, 1, 0), distance+tol+.02,
            material, [distance-tol, distance+tol])

    def south(name, u, z, material, front, y=16.75, tol=.018):
        distance = y-13.65-front
        ray('Garden / '+name, (-u, y, z), (0, -1, 0), distance+tol+.02,
            material, [distance-tol, distance+tol])

    def south_air(name, u, z, end_d, start_y=16.75):
        ray('Garden / '+name, (-u, start_y, z), (0, -1, 0), start_y-13.65-end_d)

    def transverse(name, x, y, z, outside_x, material, tol=.018):
        sign = 1 if outside_x < x else -1
        gap = abs(x-outside_x)
        ray(name, (outside_x,y,z), (sign,0,0), gap+tol+.015, material, [gap-tol, gap+tol])

    def down(name, x, y, z, surface_z, material, tol=.02):
        ray(name,(x,y,z),(0,0,-1),z-surface_z+tol+.02,material,
            [z-surface_z-tol,z-surface_z+tol])

    # The 2013 and 2021 north photographs show the tall stair light rising
    # over the bowed canopy, two much smaller sidelights, and paired door leaves.
    tower = .24
    for n,(x,w) in enumerate(((-4.75,.705),(-2.4,.41),(2.76,.38),(4.32,.38)),1):
        for floor,base,height in (('lower',1.74,1.47),('upper',5.01,1.50)):
            label=f'{floor} window {n}'
            north(label+' pane',x+w*.125,base+.39*height,GLASS,2.647)
            north(label+' meeting bar',x,base+.39*height,FRAME,2.583)
            north(label+' stone sill',x+w*.13,base-.044,STONE,2.3625)
    for z in (3.91,4.36,5.02,6.81,7.35,8.03):
        if z in (4.36,6.81,8.03):
            north(f'stair horizontal bar at {z:.2f}',tower+.086,z,FRAME,2.215)
            north(f'stair pane above bar at {z:.2f}',tower+.086,z+.060,GLASS,2.301)
        else:
            north(f'stair glazing at {z:.2f}',tower+.086,z,GLASS,2.301)
        north(f'stair central iron at {z:.2f}',tower,z,FRAME,2.215)
    for z in (3.22,5.80):
        north(f'inclined stair behind iron at {z:.2f}',tower-.11,z,'Stair flight behind the light',2.196)
    for sign in (-1,1):
        light=tower+sign*1.19
        north(f'sidelight pane {sign}',light+.088,1.23,GLASS,2.262)
        north(f'sidelight vertical {sign}',light,1.23,FRAME,2.181)
        leaf=tower+sign*.355
        north(f'timber entrance leaf {sign}',leaf,.59,'Panelled entrance doors',2.354)
        north(f'entrance leaf glazing {sign}',leaf+.055,1.87,'Entrance glazing',2.388)
        north(f'apex of iron diamond {sign}',leaf,1.61,IRON,2.325,.022)
        north(f'wall lantern cage {sign}',tower+sign*.99+.035,2.48,IRON,1.75,.02)
        north(f'wall lantern glass {sign}',tower+sign*.99-.037,2.48,'Lantern glass',1.76,.04)
    north('door handle',tower+.065,1.055,'Bronze details',2.286,.012)
    north('painted number plaque',tower-1.72+.076,2.52,'Green enamel plaque',2.061)
    down('North / bowed threshold',tower+.12,-.70,.80,.181,STONE)
    down('North / front of shell canopy',tower+.30,-1.74,3.4,3.045,WHITE)
    down('North / side of shell canopy',tower+1.63,-.80,3.4,3.045,WHITE)
    ray('North / sky just beyond rounded canopy corner',(tower+1.72,-1.72,3.25),(0,0,-1),.56)
    ray('North / central radiating stone rib',(tower,-1.39,2.40),(0,0,1),.55,STONE,[.38,.50])
    ray('North / covered air above approach',(tower-.42,-2.45,2.36),(0,1,0),1.65)

    # Lower colonnade and upper terrace. These limits separately test each
    # member and its neighbouring air gap. No ray is filtered by material.
    left=-7.
    width=9.75
    front=1.63
    column_d=1.455
    axes=[left+width*f for f in (.166,.350,.537,.878)]
    for ix,axis in enumerate(axes,1):
        for level,z in [('ground',1.58),('upper',4.83)]:
            south(f'{level} opening {ix} glass',axis+.093,z,GLASS,-.180,y=14.37)
            south_air(f'{level} opening {ix} reveal',axis+.093,z,-.155,start_y=14.37)
    for i,center in enumerate((left+width*.033,left+width*.690),1):
        for hand in (-1,1):
            u=center+hand*.151
            south(f'paired Ionic shaft {i}/{hand}',u,2.21,WHITE,column_d+.109,tol=.020)
            south(f'shaft abacus {i}/{hand}',u,3.436,WHITE,column_d+.155)
        south_air(f'space between paired shafts {i}',center,2.21,.92)
    stair=axes[1]
    fractions=[(.98,.155),(.70,.310),(.46,.465),(.14,.620)]
    for i,(d,h) in enumerate(fractions,1):
        down(f'Garden / curved stair tread {i}',-stair+.053,13.65+front+d,1.38,h,STONE)
    for u in (-.42,0.,.42):
        south_air(f'clear stair approach {u}',stair+u,1.18,.26)
    half=width*.113
    intervals=[(-7.06,stair-half-.11),(stair+half+.11,2.75-.04)]
    for strip,(lower,upper) in enumerate(intervals,1):
        n=round((upper-lower)/.212)
        for k in range(n):
            u=lower+(k+.5)*(upper-lower)/n
            if (strip==1 and k==n-1) or (strip==2 and k==0):
                south(f'front stair newel overlapping rail {strip}',u,1.080,STONE,column_d+.17)
                visible_u=u+(-1 if strip==1 else 1)*(upper-lower)/n
                south(f'nearest visible stair baluster {strip}',visible_u,1.14,WHITE,column_d+.05,tol=.04)
            else:
                south(f'lower baluster {strip}/{k+1}',u,1.080,WHITE,column_d+.04,tol=.04)
            if k+1<n:
                # Clear of the two broad newels at the stair and both end piers.
                u=lower+(k+1)*(upper-lower)/n
                if min(abs(u-x)for x in (stair-half-.16,stair+half+.16))>.19:
                    south_air(f'lower baluster gap {strip}/{k+1}',u,1.080,column_d-.08)
    piers=[left+width*f for f in (.044,.239,.478,.689,1.)]
    for strip,(p,q) in enumerate(zip(piers,piers[1:]),1):
        a=p+.13
        span=q-p-.26
        n=round(span/.235)
        for i in range(1,n):
            u=a+i*span/n
            south(f'upper grille upright {strip}/{i}',u,4.25,STONE,front-.09+.049)
        for i in range(n):
            south_air(f'upper grille opening {strip}/{i+1}',a+(i+.5)*span/n,4.25,front-.09-.095)
    for i,center in enumerate((stair-half-.16,stair+half+.16),1):
        south(f'stair newel {i}',center,1.24,STONE,column_d+.17)
    wing=4.875
    for i,z in enumerate((2.07,5.34),1):
        south(f'projecting arched pane {i}',wing+.19,z,GLASS,1.55-.180)
        south(f'central arched mullion {i}',wing,z,FRAME,1.55-.115)
    south('curved balcony top rail',wing,4.80,IRON,1.55+.386,tol=.035)
    south_air('curved balcony open center',wing,4.55,1.65)
    south('attic glazed face',wing+.11,7.57,GLASS,1.55-.012-.180)
    south('right wing masonry',wing+1.53,5.66,BRICK,1.55)

    for u in (-4.64,-2.64,.44,2.52):
        south(f'sheltered render at {u}',u,2.41,STONE,0.,y=14.22)
        south(f'exposed second-storey brick above {u}',u,4.95,BRICK,0.,y=14.22)
    for z in (3.65,3.74,3.83):
        south(f'pale apron between arched windows {z}',wing+.38,z,STONE,1.55+.0935)
    for off in (-.63,-.26,.31,.68):
        fraction=off/(2.01875*.535)
        edge=1.55+.096+.29*(1-fraction*fraction)+.045
        south(f'bowed balcony stone edge {off}',wing+off,3.935,STONE,edge)
    for j,edge_u in enumerate((2.75,7.)):
        for k in (5,6,13,14):
            span=.29 if k%2==0 else .155
            sign=1 if j==0 else -1
            south(f'east bay corner {j} ashlar course {k}',edge_u+sign*span*.72,.16+k*.285,
                  STONE,1.55+.055)
    for k in (2,3,6,7):
        south(f'west upper corner course {k}',-7.+.07,3.75+.145+k*.285,
              STONE,.055,y=14.22)

    # Visible side apertures are measured from two views per elevation.
    length=13.65
    east_x=-7.
    for number,f in enumerate((.298,.535,.706,.891),1):
        y=(1-f)*length+.073
        transverse(f'East / upper glazing {number}',east_x+.180,y,5.29,-8.8,GLASS)
        if number!=2:
            transverse(f'East / lower glazing {number}',east_x+.180,y,1.94,-8.8,GLASS)
        else:
            transverse('East / solid brick below narrow opening',east_x,y,2.,-8.8,BRICK)
    transverse('East / stone parapet below arched window',east_x-.48,(1-.298)*length,.69,-8.8,STONE)
    for i,f in enumerate((.269,.536),1):
        transverse(f'West / upper opening {i}',7-.180,f*length+.073,5.48,10.30,GLASS)
    transverse('West / solid main wall above annex',7,.76*length,5.44,10.3,BRICK)
    for i,(f,z) in enumerate(((.105,1.48),(.384,2.34),(.565,2.34),(.825,1.69)),1):
        transverse(f'West annex / opening {i}',9.30-.180,-.70+f*11.19+.073,z,10.80,GLASS)
    north('west annex slit',7.29+.084+.057,1.88,GLASS,1.98)
    for i,(frac,count,h) in enumerate(((.105,2,.34),(.825,4,.62)),1):
        y=-.70+frac*11.19
        for k in range(count):
            x=9.30+(count-k-.52)*.25+.04
            down(f'West annex / door {i} step {k+1}',x,y+.055,1.13,(k+1)*h/count,STONE)
    down('West annex / shallow roof return',8.75,5.84,5.5,4.035,CLAY,.065)
    down('Roof / eastern eave',-7.37,7.02,8.12,7.28,['Weathered tile troughs',CLAY],.07)
    down('Roof / ridge of main hip',1.22,6.825,12.0,10.72,['Weathered tile troughs',CLAY],.07)
    down('Roof / western chimney cap',5.03,3.04,12.1,11.215,STONE,.02)
    ray('Roof / sky between chimney and hip', (4.20,3.05,11.6),(0,0,-1),.74)
    return tests


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for role in ('raw','full','lod','output'):
        parser.add_argument(role,type=Path)
    args=parser.parse_args()
    probes=cases()
    results={role:trace(getattr(args,role),probes) for role in ('raw','full','lod')}
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=1)+'\n')
    for role,result in results.items():
        failed=[(r['name'],r['first_hit']) for r in result['cases'] if not r['passed']]
        print(role,len(probes),'failures',len(failed),failed,flush=True)
    return 0 if all(result['passed'] for result in results.values()) else 1


if __name__=='__main__':
    raise SystemExit(main())
