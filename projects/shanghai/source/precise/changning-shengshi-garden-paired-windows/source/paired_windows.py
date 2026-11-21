"""Street window bay of the inter-war villa registered at 540 Wanhangdu Road."""
from math import cos, sin, pi
from pathlib import Path
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

RENDER='warm ochre roughcast'
REVEAL='ochre window returns'
STONE='grey moulded window stone'
DARK='dark edge beneath mouldings'
METAL='painted steel casements'
GLASS='muted blue-green window glass'
PALE='second-light glass'
WOOD='dark shutter rails'
SLAT='louvred shutter blades'
IRON='weathered ironwork'
LEAD='old zinc rain gutter'
TILE='umber clay roof tile'
TILE_LIGHT='lighter clay ridge'
JOINT='roofing shadow'
PALETTE={name:dict(color=color,roughness=roughness) for name,color,roughness in [
    (RENDER,[.555,.395,.221],.97),(REVEAL,[.402,.277,.147],.95),
    (STONE,[.29,.264,.217],.88),(DARK,[.152,.143,.118],.94),
    (METAL,[.040,.043,.033],.72),(GLASS,[.105,.135,.132],.27),
    (PALE,[.144,.172,.168],.32),(WOOD,[.080,.070,.048],.90),
    (SLAT,[.105,.090,.064],.84),(IRON,[.076,.067,.048],.74),
    (LEAD,[.31,.313,.291],.71),(TILE,[.267,.127,.070],.93),
    (TILE_LIGHT,[.314,.152,.086],.92),(JOINT,[.136,.068,.043],.99)]}
PALETTE[RENDER].update(color=[1.,1.,1.],texture=str(Path(__file__).with_name('ochre-roughcast.png')))
AXES=(-.79,.81)
BASES=(.25,2.72)
WIDTH=1.02
HEIGHT=1.27

def block(b,x0,x1,y0,y1,z0,z1,material,name):
    b.box(((x0+x1)*.5,(y0+y1)*.5,(z0+z1)*.5),(x1-x0,y1-y0,z1-z0),material,label=name)

def cast_face(b,polygon,front,back,material,name):
    for piece in getattr(polygon,'geoms',[polygon]):
        if piece.geom_type=='Polygon' and piece.area>1.e-8:
            b.prism(piece,-back,-front,lambda x,z,t:(x,-t,z),material,label=name)

def profile(b,x0,x1,section,material,name):
    b.prism(Polygon(section),x0,x1,lambda y,z,x:(x,y,z),material,label=name)

def shutter(b,x,z,side,lod):
    near=x+side*(WIDTH/2+.063);far=near+side*.297
    left,right=sorted((near,far));top=z+HEIGHT
    block(b,left,right,-.077,-.034,z+.025,top-.025,WOOD,'Shutter frame and backing')
    for p in (left+.014,right-.014):
        block(b,p-.014,p+.014,-.099,-.075,z+.022,top-.022,WOOD,'Shutter side rail')
    for p in (z+.043,z+.64,top-.043):
        block(b,left,right,-.101,-.075,p-.020,p+.020,WOOD,'Shutter cross rail')
    for bottom in (z+.069,z+.671):
        count=6 if lod else 10
        pitch=.525/count
        for i in range(count):
            base=bottom+i*pitch
            profile(b,left+.028,right-.028,[(-.096,base),(-.082,base),(-.074,base+pitch*.74),(-.087,base+pitch*.87)],SLAT,'Sloping louvre blades')

def window(b,x,z,index,lod):
    low=z;top=z+HEIGHT;left=x-WIDTH/2;right=x+WIDTH/2
    outer=box(left-.071,low-.077,right+.071,top+.085)
    cast_face(b,outer.difference(box(left,low,right,top)),-.044,.145,STONE,'Stone jambs and head')
    for side in (-1,1):
        edge=x+side*WIDTH/2
        block(b,edge-.014,edge+.014,.016,.146,low,top,REVEAL,'Recessed side returns')
    for dx in (-WIDTH/2+.023,0,WIDTH/2-.023):
        block(b,x+dx-.018,x+dx+.018,.091,.141,low+.017,top-.017,METAL,'Outer frame and opening stiles')
    for dx in (-.251,.251):
        block(b,x+dx-.010,x+dx+.010,.105,.142,low+.026,top-.026,METAL,'Vertical glazing bars')
    for dz in (.025,.441,.844,HEIGHT-.025):
        thick=.021 if dz in (.025,HEIGHT-.025) else .012
        block(b,left,right,.101,.143,low+dz-thick,low+dz+thick,METAL,'Casement rails')
    for col in range(4):
        for row,(a,c) in enumerate(((.015,.441),(.441,.844),(.844,HEIGHT-.015))):
            block(b,left+col*WIDTH/4,left+(col+1)*WIDTH/4,.151,.17,low+a,low+c,PALE if (col+row+index)%7==2 else GLASS,'Inset individual window lights')
    profile(b,left-.114,right+.114,[(.05,top+.013),(-.086,top+.013),(-.106,top+.068),(-.173,top+.108),(-.183,top+.158),(.05,top+.158)],STONE,'Stepped hood over each casement')
    profile(b,left-.092,right+.092,[(.06,low+.008),(-.201,low+.008),(-.207,low-.031),(-.167,low-.052),(-.145,low-.091),(.06,low-.091)],STONE,'Splayed sill with a drip')
    block(b,left-.065,right+.065,-.129,-.028,low-.11,low-.09,DARK,'Shadow course under sill')
    shutter(b,x,z,-1,lod)
    if index%2==0:shutter(b,x,z,1,lod)

def flower_stand(b,lod):
    sides=5 if lod else 9
    wire=lambda points,r,name:b.tube(points,r,IRON,sides=sides,label=name)
    front=-.390
    for z in (1.705,1.934):
        wire([(-1.43,front,z),(1.43,front,z)],.016,'Front horizontal iron rails')
    for x in (-1.43,-.79,-.135,.135,.81,1.43):
        wire([(x,-.023,1.657),(x,front,1.705),(x,front,1.934),(x,-.035,1.934)],.014,'Bent shelf ends and wall ties')
    for x in (-1.36,-1.09,-.79,-.48,-.20,.20,.48,.81,1.1,1.36):
        wire([(x,-.055,1.478),(x,front,1.701),(x,-.048,1.683)],.012,'Triangular flower shelf brackets')
    for x0,x1 in ((-1.43,-.13),(.13,1.43)):
        for y in (-.33,-.22,-.11):
            wire([(x0,y,1.698),(x1,y,1.698)],.011,'Open iron shelf rods')
    # Individual loop tops are visible above the straight upper bar in the dated photograph.
    n=9 if lod else 17
    for i in range(25):
        x=-1.373+i*(2.746/24)
        points=[(x-.048,-.341,1.706),(x-.048,-.398,1.795),(x-.048,-.41,1.847)]
        points += [(x+.048*cos(pi-j*pi/n),front,1.927+.067*sin(pi-j*pi/n)) for j in range(n+1)]
        points += [(x+.048,-.41,1.847),(x+.048,-.398,1.795),(x+.048,-.341,1.706)]
        wire(points,.009,'Loop-headed iron guard')

def eaves(b,lod):
    profile(b,-1.95,1.95,[(.23,4.18),(-.28,4.18),(-.34,4.23),(.24,4.62)],JOINT,'Section of original roof at cut line')
    for row in range(5):
        y=-.317+row*.11;z=4.244+row*.073
        for i in range(21):
            a=max(-1.95,-2.15+i*.20+(.1 if row%2 else 0));c=min(1.95,-1.95+i*.20+(.1 if row%2 else 0))
            if c-a <.065:continue
            profile(b,a+.004,c-.003,[(y,z-.006),(y+.126,z+.071),(y+.124,z+.09),(y,z+.019)],TILE_LIGHT if (i+row)%6==1 else TILE,'Overlapping clay pantiles')
    # The roof gutter is a hollow half-round sheet open at its top.
    n=8 if lod else 18
    trough=[(-.342+.082*cos(pi+j*pi/n),4.223+.066*sin(pi+j*pi/n))for j in range(n+1)]
    trough += [(-.342+.074*cos(pi+j*pi/n),4.223+.058*sin(pi+j*pi/n))for j in reversed(range(n+1))]
    profile(b,-1.955,1.955,trough,LEAD,'Half-round metal gutter')

def model(b,lod=False):
    wall=box(-1.94,0,1.94,4.245)
    holes=unary_union([box(x-WIDTH/2,z,x+WIDTH/2,z+HEIGHT)for z in BASES for x in AXES])
    cast_face(b,wall.difference(holes),0,.255,RENDER,'Ochre rendered masonry around four openings')
    for part in b.parts:
        if part['material']==RENDER:
            part['texcoords']=[[(x+1.95)/3.9,1-z/4.27] for x,y,z in part['vertices']]
    # Shallow vertical plaster return is visible immediately right of the casements.
    block(b,1.83,1.94,-.066,.03,0,4.19,REVEAL,'Right-hand wall return')
    for level,z in enumerate(BASES):
        for side,x in enumerate(AXES):window(b,x,z,level*2+side,lod)
    flower_stand(b,lod)
    eaves(b,lod)
