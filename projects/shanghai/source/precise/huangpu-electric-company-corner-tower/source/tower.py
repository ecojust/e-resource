"""The northeast corner tower and the first window group of each street frontage."""
import json
from math import cos, pi, sin
from pathlib import Path

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from brickwork import texture_uv
from photo_architecture import Facade

SOURCE = Path(__file__).resolve().parent
EDGES = json.loads((SOURCE / 'frontage-registration.json').read_bytes())['visible_edges_local_m']
BRICK = 'ochre face brick'
GRANITE = 'pale base granite'
STONE = 'pale geometric stone'
MARBLE = 'polished brown portal'
BRONZE = 'patinated bronze'
HIGHLIGHT = 'raised bronze highlights'
IRON = 'black cast iron'
GLASS = 'steel blue glazing'
LAMP = 'lamp glass'
ROOF = 'lead roof flashing'
PALETTE = {
    name: {'color': colour, 'roughness': roughness}
    for name, colour, roughness in [
        (BRICK, [1, 1, 1], .90), (GRANITE, [.78, .77, .73], .82),
        (STONE, [.68, .66, .61], .80), (MARBLE, [.39, .25, .20], .49),
        (BRONZE, [.43, .34, .22], .48), (HIGHLIGHT, [.75, .65, .45], .43),
        (IRON, [.15, .16, .16], .68), (GLASS, [.32, .40, .44], .32),
        (LAMP, [.81, .82, .75], .46), (ROOF, [.32, .33, .32], .76),
        ('flag red', [.69, .08, .07], .88), ('flag gold', [.98, .78, .10], .81),
    ]
}
PALETTE[BRICK]['texture'] = str(SOURCE / 'ochre-brick.png')
BASE = 5.60
SPACING = 3.18
CORNICE = 23.55


def panel(face, x, z, width, height, material, depth=.12, projection=.035, label='panel'):
    face.box(x, z, width, height, depth, projection, material, label)


def glazing(face, opening, columns, transom, label):
    left, bottom, right, top = opening.bounds
    inner = opening.buffer(-.055, join_style='mitre')
    bars = [box(left, bottom+(top-bottom)*transom-.025, right, bottom+(top-bottom)*transom+.025)]
    for n in range(1, columns):
        x = left + (right-left)*n/columns
        bars.append(box(x-.022, bottom, x+.022, top))
    grid = opening.difference(inner.difference(unary_union(bars)))
    face.prism(opening.buffer(.009, join_style='mitre'), -.255, -.225, GLASS, label+' glass')
    face.prism(grid, -.170, -.092, IRON, label+' frame')


def numeral_plate(face, z):
    panel(face, 0, z, .32, .19, STONE, .022, .139, '181 enamel address')
    segments = {'1': ('tr','br'), '8': ('t','tr','br','b','bl','tl','m')}
    for digit, x in zip('181', (-.085, 0, .085)):
        for part in segments[digit]:
            dx, dz, width, height = {
                't':(0,.060,.046,.009), 'b':(0,-.060,.046,.009), 'm':(0,0,.046,.009),
                'tr':(.025,.032,.009,.048), 'br':(.025,-.032,.009,.048),
                'tl':(-.025,.032,.009,.048), 'bl':(-.025,-.032,.009,.048),
            }[part]
            panel(face, x+dx, z+dz, width, height, IRON, .010, .155, 'address number')


def entrance(face, distant):
    from door_reliefs import add_relief
    opening = box(-1.44, 0, 1.44, 4.18)
    face.wall(0, BASE, [opening], .46, GRANITE)
    face.prism(opening.buffer(.23, join_style='mitre').difference(opening), -.33, .098, MARBLE, 'polished deep stone surround')
    face.prism(opening.buffer(.35, join_style='mitre').difference(opening.buffer(.23, join_style='mitre')), -.05, .105, STONE, 'outer portal edge')
    for i in range(3):
        panel(face, 0, .055+i*.109, 2.81, .11, GRANITE, .52-.10*i, .08-.08*i, 'entrance tread')
    a = face.point(-face.length/2, 0, -.28)[:2]
    b = face.point(face.length/2, 0, -.28)[:2]
    door = Facade(face.builder, a, b, '181 double street gate')
    door.prism(box(-1.39,.31,1.39,4.14), -.11, -.075, GLASS, 'glass behind bronze')
    for x in (-1.34,-.028,.028,1.34):
        panel(door,x,1.65,.059,2.65,BRONZE,.057,.023,'leaf perimeter stile')
    for x in (-.685,.685):
        for z in (.39,2.82,3.01):
            panel(door,x,z,1.27,.062,BRONZE,.059,.024,'horizontal leaf rail')
        for i in range(1,5):
            u=x-.64+i*1.28/5
            panel(door,u,1.53,.028,2.18,BRONZE,.042,.019,'gate upright')
        add_relief(door,x,2.32,'left' if x<0 else 'right',distant)
    for n in range(-7,8):
        panel(door,n*.176,3.56,.025,1.07,BRONZE,.04,.012,'fanlight grille')
    panel(door,0,3.03,2.73,.13,BRONZE,.063,.022,'transom crossbar')
    crest = Polygon([(-.19,3.96),(.19,3.96),(.19,3.56),(0,3.43),(-.19,3.56)])
    door.prism(crest,.04,.095,HIGHLIGHT,'shield above the transom')
    if not distant:numeral_plate(door,3.07)
    for x in (-2.30,2.30):
        panel(face,x,2.68,.18,1.12,IRON,.25,.15,'wall lantern backplate')
        panel(face,x,2.73,.12,.87,LAMP,.10,.30,'lantern glass')
        for z in (2.22,3.22):
            panel(face,x,z,.24,.10,BRONZE,.32,.19,'lantern lid')


def base_windows(face, distant):
    width=face.length*.63
    hole=box(-width/2,.26,width/2,4.20)
    face.wall(0,BASE,[hole],.46,GRANITE)
    glazing(face,hole,3,.69,'street display')
    panel(face,0,4.05,width,.30,IRON,.075,-.06,'street window grille')
    if not distant:
        for n in range(13):
            panel(face,(n-6)*width/13,4.05,.024,.29,BRONZE,.043,-.01,'shop grille bars')


def crown(face, central, distant):
    width=face.length
    for x in (-width*.31,width*.31):
        for i in range(3):
            panel(face,x,22.14+i*.40,.36+.03*i,.36,STONE,.10,.052,'stepped vertical plaque')
    top=CORNICE+(.67 if central else .09)
    panel(face,0,(top+21.41)/2,.86,top-21.41,STONE,.21,.095,'long dropped keystone')
    wing=1.49 if central else 1.76
    for n in range(4):
        for sign in (-1,1):
            length=wing-n*.22
            panel(face,sign*(.37+length/2),23.37-n*.127,length,.077,STONE,.20,.107,'horizontal stepped crown')
    if central:
        sections=[(2.12,23.55,24.22),(1.56,24.22,25.97),(.90,25.97,26.31),(.42,26.31,26.55)]
        for width,lo,hi in sections:
            panel(face,0,(lo+hi)/2,width,hi-lo,BRICK,1.29,-.50,'receding masonry tower')
        panel(face,0,25.02,.52,1.53,STONE,.12,.177,'crown centre plaque')
        if not distant:
            for n in range(6):
                panel(face,0,24.44+n*.205,.45,.023,GRANITE,.05,.239,'plaque relief joints')


def upper(face, central, distant):
    xs=[0] if central else [-1.19,0,1.19]
    width=1.27 if central else .99
    holes=[]
    for i in range(5):
        base=BASE+.14+i*SPACING
        for x in xs:
            window=box(x-width/2,base,x+width/2,base+1.91)
            holes.append(window)
            glazing(face,window,2 if central or x==0 else 1,.73,'tower window' if central else 'street window')
            if i<4:
                panel(face,x,base+2.54,width,1.14,IRON,.115,-.009,'cast-iron spandrel')
                if not distant:
                    for j in (-2,-1,0,1,2):
                        panel(face,x+width*j/6,base+2.53,.025,.93,IRON,.05,.059,'vertical spandrel rib')
    face.wall(BASE,CORNICE,holes,.35,BRICK)
    for x in xs:
        for off in (-.5,.5):
            panel(face,x+width*off,13.61,.081,15.78,BRICK,.17,.080,'raised brick window edge')
    crown(face,central,distant)


def flag(face, distant):
    stem=face.point(0,26.54,-.47)
    top=face.point(0,32.06,-.47)
    face.builder.tube([stem,top],.040,BRONZE,6 if distant else 10,'mast over northeast tower')
    # Wind-folded cloth. The obverse and reverse share the same folds and star positions.
    def mapping(u,v,d=0):
        return face.point(-u*.88,31.91-v*.90-u*.27,-.47+sin(u*4.5)*.12+d)
    count=6 if distant else 18
    vertices=[]
    for n in range(count+1):
        u=1.5*n/count
        vertices.extend([mapping(u,0,.006),mapping(u,1,.006),mapping(u,1,-.006),mapping(u,0,-.006)])
    faces=[(0,3,2,1),tuple(4*count+i for i in range(4))]
    for n in range(count):
        for j in range(4):
            off=4*n
            faces.append((off+j,off+(j+1)%4,off+4+(j+1)%4,off+4+j))
    face.builder.add(vertices,faces,'flag red','folded flag')
    for x,y,r,rot in [(.25,.25,.15,-pi/2),(.50,.10,.05,2.60),(.60,.20,.05,3.00),(.60,.35,.05,-2.86),(.50,.45,.05,-2.46)]:
        pts=[(x+cos(rot+i*pi/5)*(r if i%2==0 else .382*r),y+sin(rot+i*pi/5)*(r if i%2==0 else .382*r))for i in range(10)]
        for side in (-.010,.010):
            face.builder.prism(Polygon(pts),side-.001,side+.001,mapping,'flag gold','embroidered stars')


def add_building(builder,distant):
    for i,(a,b)in enumerate(zip(EDGES,EDGES[1:])):
        face=Facade(builder,a,b,['Jiangxi return','northeast tower','Nanjing return'][i])
        central=i==1
        if central:entrance(face,distant)
        else:base_windows(face,distant)
        face.beam(BASE,.15,.24,GRANITE,label='base coping')
        upper(face,central,distant)
        for x in (-face.length/2+.085,face.length/2-.085):
            panel(face,x,14.55,.17,17.66,BRICK,.19,.074,'corner brick nosing')
        if central:flag(face,distant)
    roof=LineString(EDGES).buffer(1.76,single_sided=True,join_style='mitre',cap_style='flat')
    builder.plan_prism(roof,CORNICE-.16,CORNICE-.055,ROOF,'street side of the roof')
    for part in builder.parts:
        if part['material']==BRICK:
            part['texcoords']=[(u,1-v)for u,v in [texture_uv(*xyz)for xyz in part['vertices']]]
