"""Garden-facing curved window wall and its deep pebble-rendered parapet at 325 Changle Road."""
import math
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

HERE=Path(__file__).resolve().parent
CONTROL=json.loads((HERE.parent/'measurements/wing-cameras.json').read_text())
POINTS=CONTROL['points']
RENDER='325 garden | pale ochre pebble finish'
UNDER='325 garden | shaded beige soffit'
DARK='325 garden | dark bronze window sections'
GLASS='325 garden | green garden reflection'
GLASS_R='325 garden | dark interior glass'
HANDLE='325 garden | dark casement latch'
TILE='325 garden | muted orange pan tile'
RIDGE='325 garden | pale terracotta round edges'
PALETTE={
    RENDER:{'color':[.65,.55,.34],'roughness':.94},
    UNDER:{'color':[.535,.445,.294],'roughness':.92},
    DARK:{'color':[.053,.050,.039],'metallic':.43,'roughness':.60},
    GLASS:{'color':[.135,.173,.113],'roughness':.32,'metallic':.23},
    GLASS_R:{'color':[.076,.078,.057],'roughness':.33,'metallic':.17},
    HANDLE:{'color':[.039,.046,.038],'metallic':.58,'roughness':.48},
    TILE:{'color':[.41,.167,.080],'roughness':.90},
    RIDGE:{'color':[.48,.231,.128],'roughness':.84},
}
CENTRE=POINTS['Ltl'][0]
RADIUS=.93
RIGHT=1.90
ARC_END=103.
OUTSET=.43

def face_path(degrees,offset=0):
    a=math.radians(degrees)
    return np.array([CENTRE-(RADIUS+offset)*math.sin(a),RADIUS-(RADIUS+offset)*math.cos(a)])

def path(samples,offset=0,straight=True):
    p=[face_path(a,offset)for a in samples]
    return [np.array([RIGHT,-offset]),*p] if straight else p

def sweep(b,outer,inner,low,high,material,label):
    # A continuous closed quadrilateral tube; distinct normals at the two end cuts
    # leave the exposed bend smooth in plan, the fascia sharp along its bottom edge.
    verts=[];faces=[]
    for j,(a,c) in enumerate(zip(outer,inner)):
        verts.extend([(*a,low(*a)),(*a,high(*a)),(*c,high(*c)),(*c,low(*c))])
        if j:
            for k in range(4):
                i=(j-1)*4+k;next_i=(j-1)*4+(k+1)%4
                faces.append((i,i+4,next_i+4,next_i))
    faces.extend([(0,1,2,3),tuple(range(len(verts)-1,len(verts)-5,-1))])
    v=np.asarray(verts);vol=sum(np.dot(v[f[0]],np.cross(v[f[i]],v[f[i+1]]))for f in faces for i in range(1,len(f)-1))
    if vol<0:faces=[f[::-1]for f in faces]
    b.add(verts,faces,material,'325 garden / '+label)

def flat(z):
    return lambda x,y:z

def front_opening(key):
    a=POINTS[key+'bl'];c=POINTS[key+'tr']
    return box(a[0],a[2],c[0],c[2])

def joinery(b,face,x0,x1,z0,z1,kind,lod):
    """A continuous upper light above two lower leaves; the turning pane has one leaf."""
    edge=.043; gap=.012
    if kind=='right':
        edge=.045
    top_light=z1-(z1-z0)*(.301 if kind!='right' else .319)
    post=(x0+x1)/2
    bars=[box(x0+edge,top_light-.020,x1-edge,top_light+.024)]
    if kind!='turn':
        bars.append(box(post-.022,z0+edge,post+.024,top_light-.019))
    glazing=box(x0+edge,z0+edge,x1-edge,z1-edge).difference(unary_union(bars))
    casing=box(x0,z0,x1,z1).difference(glazing)
    face.prism(casing,-.105,-.040,DARK,kind+' / frame transom and lower meeting stiles')
    for i,pane in enumerate(getattr(glazing,'geoms',[glazing])):
        # Opening leaves have a second thinner lip, leaving an actual recessed pane.
        skin=pane.buffer(-gap,join_style=2)
        if skin.is_empty:continue
        face.prism(pane.difference(skin),-.125,-.066,DARK,kind+' / glazing lip '+str(i))
        face.prism(skin,-.151,-.128,GLASS_R if kind=='right'else GLASS,kind+' / glass '+str(i))
    # In Fayhoo's inner garden photograph the curved bay shows the latch below the meeting rail.
    if kind=='flat' and not lod:
        z=z0+.45*(top_light-z0)
        face.box(post-.036,z,.026,.100,.023,-.026,HANDLE,'leaf / handle seat')
        face.box(post-.049,z+.014,.045,.017,.045,-.001,HANDLE,'leaf / return handle')

def add_curved_wing(b,lod=False):
    for k,v in PALETTE.items():b.palette.setdefault(k,v)
    front=Facade(b,(-1.,0.),(1.,0.),'325 garden / front')
    head=lambda x,y:3.78-.032*x
    upper=lambda x,y:4.83-.039*x
    roof=lambda x,y:5.65-.043*x+.36*(y-.30)
    wall=Polygon([(CENTRE,0),(RIGHT,0),(RIGHT,head(RIGHT,0)),(CENTRE,head(CENTRE,0))])
    holes=unary_union([front_opening('L'),front_opening('R')])
    front.prism(wall.difference(holes),-.18,0,RENDER,'rendered wall with open window reveals')
    for key,kind in [('R','right'),('L','flat')]:
        x0,z0,x1,z1=front_opening(key).bounds
        joinery(b,front,x0,x1,z0,z1,kind,lod)
    # The native image shows a single glazed return and a continuous transverse rail.
    # The return is a chord between two frames; only the backing render sweeps the arc.
    end=63.;segments=9 if lod else 22
    angles=np.linspace(0,ARC_END,segments+1)
    x0,z0,x1,z1=front_opening('L').bounds
    sweep(b,path(angles,0,False),path(angles,-.18,False),flat(0),flat(z0),RENDER,'curved apron')
    sweep(b,path(angles,0,False),path(angles,-.18,False),flat(z1),head,RENDER,'curved head')
    tail=np.linspace(end,ARC_END,5 if lod else 12)
    sweep(b,path(tail,0,False),path(tail,-.18,False),flat(z0),flat(z1),RENDER,'return pier')
    a=face_path(end);c=face_path(0)
    arcface=Facade(b,a,c,'325 garden / single glazed return')
    length=float(np.linalg.norm(c-a));joinery(b,arcface,-length/2,length/2,z0,z1,'turn',lod)
    # Solid curved sill and lintel bridge the chord glazing to the rendered radius.
    segment=np.linspace(end,0.,12 if lod else 24)
    arc=[tuple(face_path(t))for t in segment]
    wedge=Polygon(arc)
    for low,high,label in [(z0-.025,z0+.026,'winding sill'),(z1-.021,z1+.023,'winding lintel')]:
        b.plan_prism(wedge,low,high,DARK,'325 garden / '+label)
    sweep(b,path(angles,OUTSET),path(angles,-.23),lambda x,y:head(x,y)-.095,head,UNDER,'curved overhang soffit')
    sweep(b,path(angles,OUTSET),path(angles,OUTSET-.165),head,upper,RENDER,'deep rendered curved parapet')
    # Only the small upper opening and the tiled margin visible above the parapet are resolved.
    upperface=Facade(b,(-1,.38),(1,.38),'325 garden / wall behind parapet')
    opening=box(-1.84,4.69,-.38,5.40)
    skin=Polygon([(-3.60,3.77),(RIGHT,3.70),(RIGHT,roof(RIGHT,.38)),(-3.60,roof(-3.6,.38))])
    upperface.prism(skin.difference(opening),-.17,0.,RENDER,'recessed upper wall')
    upperface.prism(opening.difference(opening.buffer(-.058,join_style=2)),-.091,-.044,DARK,'small top light frame')
    upperface.prism(opening.buffer(-.058,join_style=2),-.12,-.095,GLASS_R,'small upper light')
    # A close crop resolves parallel rolled pan ends across the low red edge.
    sweep(b,[np.array([-3.69,.27]),np.array([RIGHT+.04,.27])],[np.array([-3.69,.85]),np.array([RIGHT+.04,.85])],
          lambda x,y:roof(x,y)-.065,roof,TILE,'cropped red upper tile margin')
    pitch=.142
    for j in range(round((RIGHT+3.70)/pitch)+1):
        x=-3.67+j*pitch
        if x>RIGHT+.04:break
        b.tube([(x,.27,roof(x,.27)+.008),(x,.85,roof(x,.85)+.008)],.038,RIDGE,5 if lod else 10,
               '325 garden / upper pan roll '+str(j+1))
