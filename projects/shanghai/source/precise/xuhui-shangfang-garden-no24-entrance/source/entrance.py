"""The photographed lane wall and open, ventilated rain hood at Zhang Yuanji's residence."""
from math import cos, sin, pi
from pathlib import Path
from shapely import affinity
from shapely.geometry import box, Point
from photo_architecture import Facade
from sign_lettering import lettering_shapes

STUCCO = 'sandy yellow roughcast'
COPING = 'blue grey coping and sill'
ROOF = 'weathered corrugated steel'
CHANNEL = 'dark steel frame'
STONE = 'pale stone heritage plaque'
TYPE = 'dark brown inscription'
BRONZE = 'dark patinated bronze marker'
GOLD = 'aged brass lettering and studs'
BOX = 'weathered pale grey electrical cabinet'
METER = 'dark meter windows'
PIPE = 'grey surface conduit'
PALETTE = {
    STUCCO: dict(color=[.787,.735,.588],roughness=.94), COPING: dict(color=[.418,.468,.494],roughness=.78),
    ROOF: dict(color=[.301,.325,.317],metallic=.38,roughness=.70), CHANNEL: dict(color=[.179,.199,.191],metallic=.48,roughness=.77),
    STONE: dict(color=[.799,.764,.648],roughness=.84), TYPE: dict(color=[.200,.177,.147],roughness=.73),
    BRONZE: dict(color=[.177,.181,.157],metallic=.52,roughness=.58), GOLD: dict(color=[.645,.495,.309],metallic=.48,roughness=.64),
    BOX: dict(color=[.602,.658,.645],metallic=.28,roughness=.71), METER: dict(color=[.170,.190,.171],metallic=.18,roughness=.48),
    PIPE: dict(color=[.649,.660,.620],roughness=.70),
}
WIDTH = 4.08
DOOR = (-.88, 0, -.11, 2.01)
WALL = 2.39
DEPTH = 1.02
FONT = Path(__file__).parent/'fonts'/'ShangfangPlaqueSubset.otf'


def fit_plaques(f, low):
    u, z = -1.35, 1.65
    f.prism(box(u-.269,z-.172,u+.269,z+.172),.003,.043,STONE,'rectangular heritage plaque')
    for i, (char, letter) in enumerate(lettering_shapes('张元济故居', .371, .060, font=FONT)):
        contour = letter.simplify(.00035 if low else .00015, preserve_topology=True)
        f.prism(affinity.translate(contour,xoff=u,yoff=z),.0425,.045,TYPE,f'inscribed title {i+1} {char}')
    for side in (-1,1):
        for level in (-1,1):
            p = Point(u+side*.241,z+level*.145).buffer(.010,quad_segs=3 if low else 5)
            f.prism(p,.042,.050,BRONZE,'four dark plaque mounts')
    u,z = -1.35,1.225
    circle = Point(u,z).buffer(.164,quad_segs=10 if low else 20)
    f.prism(circle,.009,.039,BRONZE,'lower circular heritage marker')
    f.prism(circle.difference(circle.buffer(-.007)),.039,.043,GOLD,'worn round rim')
    # The small raised central device is visible, its surrounding minute inscription is unresolved.
    for x,bottom,top in [(u-.029,z-.052,z+.059),(u-.010,z-.075,z+.077),(u+.013,z-.045,z+.060)]:
        f.prism(box(x-.003,bottom,x+.003,top),.038,.043,GOLD,'raised central vertical motif')
    for dx,dz in [(-.03,.018),(.0,-.038)]:
        f.prism(box(u+dx,z+dz,u+.046,z+dz+.006),.039,.044,GOLD,'raised lateral motif')


def cabinet(f, low):
    x,z=.50,1.41
    f.prism(box(x-.379,z-.596,x+.379,z+.596),.003,.114,BOX,'wall-mounted cabinet body')
    f.prism(box(x-.35,z-.565,x+.35,z+.558),.113,.120,CHANNEL,'dark gasket around panel')
    f.prism(box(x-.344,z-.557,x+.344,z+.55),.119,.13,BOX,'inset front panel')
    for column in range(3):
        u=x+(column-1)*.213
        for row in range(3):
            h=z-.292+row*.257
            f.prism(box(u-.058,h-.069,u+.058,h+.069),.128,.141,METER,'nine inspection windows')
            if not low:
                f.prism(box(u-.039,h-.039,u+.041,h-.021),.140,.144,COPING,'meter scale sill')
        for line in range(3):
            h=z+.365+line*.035
            f.prism(box(u-.049,h,u+.049,h+.008),.130,.134,METER,'upper ventilation slots')
    path=[(-.07,-.002,2.061),(-.07,-.098,2.155),(.01,-.098,2.199),
          (1.87,-.098,2.199),(1.91,-.098,2.248),(1.91,-.098,2.86)]
    f.builder.tube(path,.022,PIPE,8 if low else 14,'No 24/surface conduit and rising bend')


def canopy(builder, low):
    # One continuous folded sheet. The sheltered open strip beneath remains visible along the lane.
    length=3.98
    points=[]
    faces=[]
    stations=22*(4 if low else 8)
    for j in range(stations+1):
        x=-length/2+j*length/stations
        ripple=.022*cos(2*pi*22*j/stations)
        for y,z in [(-.10,2.818),(DEPTH,2.926),(DEPTH,2.909),(-.10,2.801)]:
            points.append((x,y,z+ripple))
        if j:
            for k in range(4):
                a=(j-1)*4+k;b=(j-1)*4+(k+1)%4
                faces.append((a,a+4,b+4,b))
    faces.extend([(0,1,2,3),(stations*4+3,stations*4+2,stations*4+1,stations*4)])
    builder.add(points,faces,ROOF,'No 24/folded corrugated shelter')
    for u in (-1.83,.01,1.85):
        builder.box((u,.018,2.600),(.035,.041,.405),CHANNEL,label='No 24/open ventilation supports')
        builder.tube([(u,.025,2.534),(u,.823,2.850)],.013,CHANNEL,6 if low else 12,'No 24/short canopy braces')
    for y,h in [(.014,2.775),(.963,2.871)]:
        builder.box((0,y,h),(3.90,.036,.044),CHANNEL,label='No 24/canopy rail')


def make_entrance(builder, low=False):
    f=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'No 24 lane entrance')
    opening=box(*DOOR)
    f.prism(box(-WIDTH/2,0,WIDTH/2,WALL).difference(opening),-.201,0,STUCCO,'roughcast wall with open door')
    f.prism(box(-WIDTH/2-.018,WALL,WIDTH/2+.018,WALL+.054),-.218,.027,COPING,'low wall coping')
    for a,b in [(-WIDTH/2,DOOR[0]),(DOOR[2],WIDTH/2)]:
        f.prism(box(a,.004,b,.102),-.011,.011,COPING,'low plinth between threshold and wall end')
    fit_plaques(f,low)
    cabinet(f,low)
    canopy(builder,low)
