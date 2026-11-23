"""Read actual triangles, material identities, portal clearance, gallery reveals and roof profiles."""
from pathlib import Path
from math import cos,pi,sin
import argparse,json,runpy

HERE=Path(__file__).resolve().parent
inspect_mesh=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1'/'verify-export.py')['inspect']
WALL='Washed grey pebbles'
BRICK=['Russet moulded brick','Dark red brick joints']
GLASS=['Grey green glazing','Warm reflected pane']
STONE=['Light grey cast stone','Weathered cement sill']
WOOD=['Dark red timber joinery','Oxblood shutter boards']
TILES=['Terracotta field tile','Weathered terracotta tile','Sunburnt terracotta tile']
W=8.854035
D=5.451996


def probes():
    series=[]
    def check(name,origin,direction,length,allowed=None,limits=None):
        series.append(dict(name=name,origin=origin,direction=direction,length=length,
                           allowed=([allowed]if isinstance(allowed,str)else allowed),range_m=limits))
    for y in (-4.61,-3.37,-2.59):
        for z in (.48,1.64,3.38,5.22,8.23,9.41):
            check(f'east pebble wall {y} / {z}',(12,y,z),(-1,0,0),3.21,WALL,(3.14,3.16))
    for theta in (.20,.42,.63,.84,1.12,1.39,1.59,1.85,2.09,2.32,2.54,2.79,2.99):
        for r in (.77,1.023):
            y=4.19+r*cos(theta);z=5.25+r*sin(theta)
            check(f'brick arch {theta} / {r}',(12,y,z),(-1,0,0),3.21,BRICK,(2.925,3.08))
    for y in (3.81,4.06,4.34,4.57):
        for z in (3.39,3.69,4.29,4.79,5.18):
            check(f'open red entrance {y} / {z}',(10.32,y,z),(-1,0,0),4.49)
            check(f'back of red passage {y} / {z}',(10.32,y,z),(-1,0,0),5.34,
                  ['Dark red timber joinery','Grey green glazing','Recess shade'],(4.75,4.895))
    for i in range(10):
        x=W-.13-i*.258;z=1.41+(3.01-1.41)*(i+1)/10
        check(f'inner stone stair tread {i+1}',(x,4.27,3.30),(0,0,-1),2,STONE,(3.29-z,3.31-z))
    for i in range(7):
        t=(i+.5)/7;a=-t*pi/2
        for r in (.45,1.38):
            z=.31+(1.41-.31)*(i+1)/7
            check(f'outer fan step {i+1} / {r}',(W+r*cos(a),5.18+r*sin(a),2.90),
                  (0,0,-1),2.90,STONE,(2.89-z,2.91-z))
        r=1.92;high=.31+1.10*t+.98
        check('curved stone coping '+str(i),(W+r*cos(a),5.18+r*sin(a),3),(0,0,-1),2.4,STONE,
              (3-high-.035,3-high+.035))
    check('approach sill north of villa',(W+.83,6.05,.40),(0,0,-1),.40,STONE,(.325,.34))
    for x in (-2.66,-2.00,-1.27,1.23,1.98,2.62):
        for z in (1.18,1.85,2.30):
            check(f'open flower porch {x} / {z}',(x,-7.55,z),(0,1,0),3.78)
        check(f'porch metal guard {x}',(x,-7.60,.965),(0,1,0),.55,'Blackened iron',(.286,.318))
    # The paving must be present throughout both covered bays in every export.
    for x in (-2.88,-2.29,-1.73,-.95,.89,1.62,2.21,2.77):
        for y in (-6.88,-6.12,-5.37,-4.59,-3.68):
            check(f'flower porch paving {x} / {y}',(x,y,.48),(0,0,-1),.55,
                  STONE+['Coarse grey plinth'],(.404,.440))
    for x in (-2.49,-1.57,-.93,1.02,1.57,2.45):
        for z in (4.17,5.18,5.94,7.89,8.71,9.27):
            check(f'glazed garden gallery {x} / {z}',(x,-8,z),(0,1,0),1.23,GLASS+['Dark red timber joinery'],(.94,1.08))
    for z in (1.11,1.67,2.12,4.21,5.99,7.91,9.45):
        check('front central gallery pier '+str(z),(0,-8,z),(0,1,0),1.10,WALL,(.86,.88))
    for x in (-6.13,6.13):
        for face,y,dire in (('garden',-D,-1),('street',D,1)):
            check(f'{face} round sill {x}',(x+.292,y+.32*dire,11.57),(0,-dire,0),.50,
                  'Light grey cast stone',(.232,.255))
            check(f'{face} attic vent slit {x}',(x+.086,y+.30*dire,11.604),(0,-dire,0),.52,
                  'Recess shade',(.432,.469))
    for sgn in (-1,1):
        axis=sgn*6.12
        for dx in (-.66,.54,.79):
            check(f'second-floor garden arched pane {axis} / {dx}',(axis+dx,-6.29,4.51),(0,1,0),1.15,GLASS,(.98,1.02))
        check(f'second-floor casement astragal {axis}',(axis+.36,-6.29,4.51),(0,1,0),1.15,'Dark red timber joinery',(.925,.95))
    for level,series_of_jambs in enumerate((((675,720),(773,821),(948,993)),((328,393),(696,739),(960,1006)),
                                              ((283,351),(540,583),(696,739),(866,917),(985,1053)))):
        for a,b in series_of_jambs:
            x=(((a+b)*.5)-668)*.0200067+.104
            z=(1.18,4.83,8.26)[level]
            # Start just inside the outer plane: North ivy and returned shutters
            # are independent surfaces ahead of the recessed glass.
            check(f'north floor {level+1} window {a}',(x,D-.027,z),(0,-1,0),.30,GLASS,(.117,.151))
    # The terrace curb and cap hold a pierced stone frieze. Each round eye is open to the sky.
    for j in (1,3,6,8):
        left=-3.48+.128;right=-.128;width=right-left;n=round(width/.318)
        u=left+(j+.5)*width/n
        check('terrace open diamond eye '+str(j),(u,-7.65,11.055),(0,1,0),.95)
        check('terrace stone spindle '+str(j),(u,-7.65,10.935),(0,1,0),.70,'Pale terrace stone',(.44,.46))
    roof=[
        ('garden ridge',-6.13,-4.91,12.984,['Terracotta ridge roll']),
        ('street ridge',6.13,4.8,12.984,['Terracotta ridge roll']),
        ('main cross ridge',2.03,1.04,14.774,['Terracotta ridge roll']),
        ('garden field',1.54,-1.77,12.05,TILES),('street field',2.08,3.14,12.61,TILES),
        ('west field',-7.45,-3.01,11.73,TILES),('east field',7.25,2.57,11.91,TILES),
        ('terrace paving',1.27,-5.088,10.39,['Attic terrace paving']),
        ('dormer roof',.011,-3.68,13.67,['Terracotta ridge roll']),
        ('rooflight',.01,2.01,13.78,['Attic doorway glazing'])]
    for label,x,y,z,mat in roof:
        check(label,(x,y,18),(0,0,-1),10,mat,(18-z-.04,18-z+.04))
    for x,yy,openings,level in [(-3.68,[-1.44169,-1.10102,-.76034,-.41966,-.07898,.26169],[1]*6,16.65),
                              (-8.82,[2.455,2.85,3.245],[1]*3,14.40),(8.82,[-1.2725,-.8775,-.4825,-.0875],[0,1,0,0],14.08)]:
        for i,(y,opened)in enumerate(zip(yy,openings)):
            z=level-(.27 if opened else 0)
            check(f'flue {x} / {i+1}',(x,y,18),(0,0,-1),7,'Flue interior' if opened else 'Fired clay flue pot',
                  (18-z-.022,18-z+.022))
    for x,y in ((12,-2),(11.3,8.3),(-11.4,-5.3),(-6.2,-9.3),(3,7),(-4,8.2)):
        check('outside the 517 villa '+str((x,y)),(x,y,18),(0,0,-1),18.1)
    return series


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for field in ('raw','full','lod','output'):parser.add_argument(field,type=Path)
    opts=parser.parse_args()
    result={}
    for role in ('raw','full','lod'):
        result[role]=inspect_mesh(getattr(opts,role),probes())
    opts.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    failed=[(role,test['name'],test['first_hit'])for role,report in result.items()for test in report['cases']if not test['passed']]
    print({role:(len(report['cases']),report['passed']) for role,report in result.items()})
    for item in failed[:45]:print(item)
    raise SystemExit(bool(failed))
