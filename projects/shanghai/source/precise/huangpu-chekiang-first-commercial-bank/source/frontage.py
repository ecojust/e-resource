"""Modernist strip windows, the chamfered corner and the Hankou Road staircase."""
from pathlib import Path
import numpy as np
from shapely.geometry import box, LineString, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

BRICK = 'brown glazed facing brick'
LIGHT_BRICK = 'warm ochre fired tiles'
DARK_BRICK = 'dark fired tiles'
STONE = 'polished Jinshan stone'
SHADE = 'buff exposed aggregate sunshade'
GLASS = 'blue grey window glass'
STEEL = 'dark rolled steel sash'
BRONZE = 'aged bronze portal'
NAVY = 'blue street fascia'
SILVER = 'pale metal letters'
SECTION = 'plain section'
PALETTE = {name: {'color': color, 'roughness': roughness} for name, color, roughness in [
    (BRICK,[.42,.282,.240],.79),(LIGHT_BRICK,[.48,.321,.251],.77),(DARK_BRICK,[.34,.235,.211],.78),
    (STONE,[.62,.565,.466],.72),(SHADE,[.753,.691,.563],.79),(GLASS,[.195,.275,.311],.29),
    (STEEL,[.118,.129,.126],.55),(BRONZE,[.296,.234,.174],.49),(NAVY,[.040,.156,.273],.6),
    (SILVER,[.815,.803,.735],.49),(SECTION,[.37,.332,.297],.93)]}
FONT = Path(__file__).with_name('fonts')/'ChekiangStreet.otf'
SOUTH = np.array([22.02031,0.0])
WEST = np.array([-22.02035,0.0])
CORNER = np.array([-33.15233,11.16454])
NORTH = np.array([-34.78759,32.15649])
NORTH_DIR = (NORTH-CORNER)/np.linalg.norm(NORTH-CORNER)
STEP = CORNER + NORTH_DIR*9.52
GROUND_TOP = 6.54
MAIN_TOP = 35.10
LOW_TOP = 22.80
DEPTH = 2.28
BANDS = [(7.20,2.13),(10.06,1.71),(13.27,2.05),(17.04,2.02),(20.97,2.08),(25.15,2.02),(30.28,2.13)]



# Construction coordinates follow the surveyed Jiangxi frontage. The published axes
# bisect the approach so the front camera sees the west windows and the north door.
ANGLE = np.radians(32.0)
ROTATION = np.array([[np.cos(ANGLE), -np.sin(ANGLE)], [np.sin(ANGLE), np.cos(ANGLE)]])
DRAWING_ORIGIN = np.array([-11.81246, 7.38124])


def to_model(xy):
    return (np.asarray(xy)-DRAWING_ORIGIN) @ ROTATION.T


def light(f, form, columns=2, rows=2, deep=.31, frame=STEEL):
    x,z,xx,zz = form.bounds
    f.prism(form.buffer(.012,join_style=2),-deep-.06,-deep,GLASS,'recessed glazing')
    inside = form.buffer(-.07,join_style=2)
    pieces = []
    for i in range(1,columns):
        at = x+(xx-x)*i/columns
        pieces.append(box(at-.027,z,at+.027,zz))
    for i in range(1,rows):
        at = z+(zz-z)*i/rows
        pieces.append(box(x,at-.026,xx,at+.026))
    panes = inside.difference(unary_union(pieces))
    f.prism(form.difference(panes),-deep+.025,-deep+.112,frame,'metal sash')
    return form


def strip(f, holes, start, end, z, height, bays, lod):
    """Create real window reveals and opaque brick piers at regular structural bays."""
    width = (end-start)/bays
    for index in range(bays):
        left = start+width*index+( .20 if index else .07)
        right = start+width*(index+1)-(.20 if index+1<bays else .07)
        holes.append(light(f,box(left,z,right,z+height),2 if lod else 4,2))
    # Slabs project outside the continuous wall, including the pencil-thin lower rail.
    f.prism(box(start-.10,z+height+.07,end+.10,z+height+.27),-.02,.62,SHADE,'projecting sunshade')
    f.prism(box(start-.07,z-.08,end+.07,z+.018),-.025,.22,SHADE,'strip window sill')
    f.prism(box(start-.08,z+.73,end+.08,z+.83),-.03,.33,SHADE,'horizontal mid-window rail')


def tile_variation(f, wall, start, end, top, lod):
    # Opaque tile colours are authored here. All windows use true wall voids.
    if lod:
        return
    for tone, offset in [(DARK_BRICK,0),(LIGHT_BRICK,5)]:
        accents = []
        for row in range(int((top-GROUND_TOP)/.34)):
            z = GROUND_TOP+.19+row*.34
            for col in range(int((end-start)/.56)):
                if (col*13+row*9+row*col)%23 != offset:
                    continue
                x = start+.1+col*.56+(.11 if row%2 else 0)
                accents.append(box(x,z,x+.21,z+.147))
        if accents:
            clipped = unary_union(accents).intersection(wall)
            if not clipped.is_empty:
                f.prism(clipped,.003,.008,tone,'kiln variation in brown wall tiles')


def entrance(f, u, width, height, lod, north=False):
    opening = box(u-width/2,0,u+width/2,height)
    depth = .71 if north else 1.39
    for side in [-1,1]:
        xx=u+side*(width/2-.08)
        f.prism(box(xx-.08,.07,xx+.08,height),-depth,-.11,STONE,'polished stone portal return')
    f.prism(box(u-width/2,height-.12,u+width/2,height),-depth,-.065,STONE,'portal soffit')
    if north:
        f.prism(box(u-width/2+.10,.055,u+width/2-.10,height-.14),-depth-.1,-depth,BRONZE,'bronze north door leaves')
        f.prism(box(u-.038,.06,u+.038,height-.15),-depth+.005,-depth+.046,STEEL,'north door meeting stile')
        for j in [-1,1]:
            f.prism(box(u+j*width*.25-.18,1.58,u+j*width*.25+.18,2.78),-depth+.008,-depth+.052,STEEL,'bronze leaf inset')
    else:
        f.prism(box(u-width/2+.15,.42,u+width/2-.15,height-.14),-depth-.13,-depth,STONE,'west portal rear stone surround')
        door=box(u-width*.34,.45,u+width*.34,3.42)
        # Opening through the surround exposes glazing standing forward of the deep wall.
        f.prism(door,-depth+.019,-depth+.033,GLASS,'entrance glazing')
        for x in [door.bounds[0],u-.51,u+.51,door.bounds[2]]:
            f.prism(box(x-.042,.47,x+.042,3.42),-depth+.035,-depth+.075,BRONZE,'west entry door stiles')
        f.prism(box(door.bounds[0],2.70,door.bounds[2],2.78),-depth+.035,-depth+.075,BRONZE,'west entry transom')
        # The outer sill rises in three visible steps to the public door.
        for i in range(3):
            d=.11+i*.25;h=.14*(i+1)
            f.prism(box(u-width/2+.13,0,u+width/2-.13,h),-depth+.01,-d,STONE,'west entrance steps')
    return opening


def west_wall(b,lod):
    f=Facade(b,WEST,SOUTH,'Jiangxi west front');half=f.length/2
    upper=[];ground=[]
    for i,(z,h) in enumerate(BANDS):
        start=-half+(.86 if i==6 else .10)
        strip(f,upper,start,half-.35,z,h,7,lod)
    for i in [-3,-2,-1,1,2,3]:
        u=i*5.56
        ground.append(light(f,box(u-2.12,1.28,u+2.12,5.91),3 if lod else 4,3))
        f.prism(box(u-2.13,.60,u+2.13,.98),-.01,.02,STEEL,'paired low stone ventilation opening')
    ground.append(entrance(f,0,4.66,6.33,lod))
    f.wall(0,GROUND_TOP,ground,.39,STONE)
    wall=f.wall(GROUND_TOP,MAIN_TOP,upper,.39,BRICK)
    tile_variation(f,wall,-half,half,MAIN_TOP,lod)
    f.prism(box(-half,GROUND_TOP-.16,half,GROUND_TOP+.04),-.03,.23,STONE,'stone and brick transition')
    f.prism(box(-10.50,5.78,10.50,6.85),.23,.42,NAVY,'bank fascia')
    add_facade_lettering(f,'交通银行',0,6.56,3.30,.38,.425,.462,SILVER,label='Chinese bank name',font=FONT)
    if not lod:
        add_facade_lettering(f,'BANK OF COMMUNICATIONS',0,6.07,4.66,.165,.424,.447,SILVER,label='bank name on fascia',font=FONT)


def corner_wall(b,lod):
    f=Facade(b,CORNER,WEST,'splayed corner');half=f.length/2
    upper=[];ground=[]
    for z,h in BANDS[:6]:
        strip(f,upper,-half+4.72,half+.04,z,h,2,lod)
        upper.append(light(f,box(-half+2.13,z+.23,-half+2.73,z+1.15),1,1))
    upper.append(light(f,box(half-3.72,30.57,half-1.17,32.32),3,2))
    upper.append(light(f,box(-half+2.10,30.73,-half+2.76,31.69),1,1))
    for u in [half-8.24,half-2.9]:
        ground.append(light(f,box(u-1.11,2.0,u+1.11,3.74),2,2))
        ground.append(light(f,box(u-1.07,4.9,u+1.07,5.8),2,1))
    f.wall(0,GROUND_TOP,ground,.38,STONE);wall=f.wall(GROUND_TOP,MAIN_TOP,upper,.39,BRICK)
    tile_variation(f,wall,-half,half,MAIN_TOP,lod)
    f.prism(box(-half,GROUND_TOP-.14,half,GROUND_TOP+.03),-.02,.20,STONE,'turn of the stone base')
    add_facade_lettering(f,'ECADI',-.50,31.62,3.17,.69,.012,.11,SILVER,label='institute corner lettering',font=FONT)


def north_wall(b,lod):
    t=Facade(b,STEP,CORNER,'Hankou stair tower');half=t.length/2
    u=half-3.20;si=box(u-1.55,7.30,u+1.55,31.40);upper=[si];ground=[entrance(t,u,2.78,4.98,lod,True)]
    t.prism(si.buffer(.01,join_style=2),-.39,-.34,GLASS,'continuous stair band glazing')
    for x in np.linspace(u-1.53,u+1.53,5):
        t.prism(box(x-.077,7.21,x+.077,31.52),.014,.196,SHADE,'four tall narrow stair lights')
    for h in [7.25,11.49,15.7,19.88,24.05,28.12,31.39]:
        t.prism(box(u-1.61,h,u+1.61,h+.13),.015,.13,SHADE,'stair transoms')
    for z,h in BANDS:
        upper.append(light(t,box(-half+1.16,z+.21,-half+2.51,z+1.44),2,2))
    t.wall(0,GROUND_TOP,ground,.38,STONE);wall=t.wall(GROUND_TOP,MAIN_TOP,upper,.39,BRICK)
    tile_variation(t,wall,-half,half,MAIN_TOP,lod)
    t.prism(box(-half,GROUND_TOP-.20,half,GROUND_TOP+.02),-.025,.3,STONE,'north entrance canopy')
    wing=Facade(b,NORTH,STEP,'lower Hankou street wall');r=wing.length/2;upper=[];ground=[]
    for z,h in BANDS[:4]:
        strip(wing,upper,-r+.39,r-.38,z,h,3,lod)
    for u in [-r*.63,0,r*.62]:
        ground.append(light(wing,box(u-.67,2.52,u+.67,3.77),2,1))
    wing.wall(0,GROUND_TOP,ground,.38,STONE);wall=wing.wall(GROUND_TOP,LOW_TOP,upper,.39,BRICK)
    tile_variation(wing,wall,-r,r,LOW_TOP,lod)


def backing(b):
    # Miter the return at the two changes in street direction. The low north wing has a separate roof level.
    for chain,top in [([NORTH,STEP],LOW_TOP),([STEP,CORNER,WEST,SOUTH],MAIN_TOP)]:
        path=LineString(chain);outline=path.buffer(DEPTH,single_sided=True,join_style='mitre')
        b.plan_prism(outline,0,.069,SECTION,'street wall ground section')
        b.plan_prism(outline,top-.081,top,SECTION,'plain top section')
        back=path.offset_curve(DEPTH,join_style='mitre')
        for a,c in zip(back.coords,list(back.coords)[1:]):
            b.add([(*a,0),(*a,top),(*c,top),(*c,0)],[(0,1,2,3)],SECTION,'closed rear cut face')
        for idx,end in [(0,chain[0]),(-1,chain[-1])]:
            floor=LOW_TOP if np.allclose(end,STEP) and top==MAIN_TOP else 0
            if np.allclose(end,STEP) and top==LOW_TOP:
                continue
            a=tuple(end);c=back.coords[idx]
            b.add([(*a,floor),(*a,top),(*c,top),(*c,floor)],[(0,1,2,3)],SECTION,'closed end of wall section')


def add_frontage(b,lod):
    west_wall(b,lod)
    corner_wall(b,lod)
    north_wall(b,lod)
    backing(b)
    for part in b.parts:
        vertices = np.asarray(part['vertices'])
        vertices[:, :2] = to_model(vertices[:, :2])
        part['vertices'] = vertices.tolist()
