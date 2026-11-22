"""Upper corner of the Shanghai Navy YMCA. The paired curved eave brackets are separate meshes."""
from math import cos, sin, pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ID='huangpu-navy-ymca-paired-eave-brackets'
WHITE='Pale lime render';ACCENT='Light moulding';DARK='Cool underside';BASE='Red masonry at the lower edge'
FRAME='Window framing';PANE='Deep window shade';SKY='Glazing reflected light'
FABRIC='Muted rose coloured hood';STITCH='Fold of fabric';SHADOW='Shadow beneath canopy'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [
    (WHITE,[1,1,1],.94),(ACCENT,[.88,.87,.82],.89),(DARK,[.60,.61,.59],.93),(BASE,[.63,.33,.24],.94),
    (FRAME,[.177,.16,.15],.83),(PANE,[.123,.14,.156],.38),(SKY,[.25,.29,.335],.4),
    (FABRIC,[.58,.47,.42],.94),(STITCH,[.67,.54,.48],.95),(SHADOW,[.33,.24,.23],.94)]}
HALF=1.76
ANGLE=pi/4
FACE=lambda u,z,d:(u,-d,z)
LEFT=lambda u,z,d:(-HALF+u*cos(ANGLE)-d*sin(ANGLE),-u*sin(ANGLE)-d*cos(ANGLE),z)
RIGHT=lambda u,z,d:(HALF+u*cos(ANGLE)+d*sin(ANGLE),u*sin(ANGLE)-d*cos(ANGLE),z)
PLANES=[(LEFT,-1.16,0.),(FACE,-HALF,HALF),(RIGHT,0.,1.16)]
CENTERS=(-.59,.59)
SOFFIT=3.30

def texture():
    path=Path(__file__).with_name('upper-plaster.png')
    if not path.exists():
        rng=np.random.default_rng(503)
        broad=rng.integers(0,255,(30,30),dtype=np.uint8)
        broad=np.asarray(Image.fromarray(broad).resize((280,224),Image.Resampling.BICUBIC),float)
        var=(broad-128)*.033+rng.normal(0,2.4,(224,280))
        rgb=np.array([218,218,211])[None,None,:]+var[:,:,None]
        Image.fromarray(np.clip(rgb,0,255).astype('u1')).quantize(128).save(path)
    PALETTE[WHITE]['texture']=str(path)

def slab(b,fn,poly,front,back,m,label):
    b.prism(poly,back,front,fn,m,label)
def rect(b,fn,l,r,bottom,top,front,back,m,label):
    slab(b,fn,box(l,bottom,r,top),front,back,m,label)

def arch(c,far):
    half=.402
    points=[(c-half,.58),(c+half,.58)]
    points.extend((c+half*cos(t),1.77+.26*sin(t)) for t in np.linspace(0.,pi,13 if far else 27))
    return Polygon(points)

def bracket(b,fn,u,far):
    # Fore-and-aft vertical section. The lower end is fixed against the wall.
    # The offset accelerates toward the flat eave, corresponding to the photographed curved profile.
    values=np.linspace(0.,1.,8 if far else 18)
    outer=[(.155+.43*(t**1.91),2.57+.71*t) for t in values]
    inner=[(.033+.425*(t**1.84),2.58+.71*t) for t in reversed(values)]
    section=Polygon(outer+inner)
    for dx in (-.077,.077):
        center=u+dx
        # min/max in the local section are reversed because the section's transverse axis is -u.
        slab(b,lambda d,z,minus_u:fn(-minus_u,z,d),section,-center+.041,-center-.041,WHITE,'One of two curved cornice brackets')
        rect(b,fn,center-.054,center+.054,2.535,2.605,.166,-.021,ACCENT,'Lower heel of plaster bracket')
        rect(b,fn,center-.050,center+.050,3.255,3.300,.604,.411,DARK,'Shoe at the cantilevered eave')
def fabric_hood(b,c,far):
    n=24 if far else 48
    rings=7
    material={m:([],[]) for m in (FABRIC,STITCH)}
    for i in range(n):
        for j in range(rings-1):
            vert,fs=material[FABRIC];start=len(vert)
            for k,t in [(i,j),(i,j+1),(i+1,j+1),(i+1,j)]:
                lon=k*pi/n;lat=t*(pi/2-.014)/(rings-1)
                vert.append((c+.466*cos(lon)*cos(lat),-.032-.392*sin(lon)*cos(lat),1.865+.314*sin(lat)))
            fs.append(tuple(start+q for q in range(4)))
    for m,(verts,faces) in material.items():
        if verts:b.add(verts,faces,m,'Dome of upper window hood')
    for index in range(1,6):
        lon=index*pi/6
        path=[(c+.467*cos(lon)*cos(lat),-.032-.393*sin(lon)*cos(lat),1.865+.315*sin(lat))
              for lat in np.linspace(0,pi/2-.04,rings)]
        b.tube(path,.004,STITCH,4 if far else 6,'Narrow fabric join in the window hood')
    verts=[];faces=[]
    for i in range(n+1):
        a=i*pi/n;lower=1.865-.055-.039*(1-cos(16*a))*.5
        verts.extend([(c+.466*cos(a),-.032-.392*sin(a),lower),(c+.466*cos(a),-.032-.392*sin(a),1.873)])
    for i in range(n):faces.append((i*2,i*2+1,i*2+3,i*2+2))
    b.add(verts,faces,SHADOW,'Scalloped lip across rose coloured hood')
def window(b,c,far):
    hole=arch(c,far)
    slab(b,FACE,hole,-.143,-.168,PANE,'Dark head behind the hood')
    for i in range(2):
        l=c-.348+i*.348;r=l+.348
        for j in range(3):
            lo=.615+j*.379;hi=lo+.379
            rect(b,FACE,l+.015,r-.015,lo+.012,hi-.012,-.133,-.146,SKY if (i+j)%3==0 else PANE,'Two-leaf glazing in deep reveal')
    for x in (c-.363,c,c+.363):rect(b,FACE,x-.016,x+.016,.58,1.8,-.102,-.142,FRAME,'Slender dark sash stile')
    for z in (.597,.993,1.37,1.758):rect(b,FACE,c-.363,c+.363,z-.014,z+.014,-.100,-.137,FRAME,'Sash rail')
    rect(b,FACE,c-.45,c+.45,.53,.585,.084,-.168,ACCENT,'Light projecting window sill')
    fabric_hood(b,c,far)
def add_building(b,far=False):
    texture()
    voids=unary_union([arch(c,far) for c in CENTERS])
    for fn,l,r in PLANES:
        wall=box(l,.20,r,SOFFIT)
        slab(b,fn,wall.difference(voids) if fn is FACE else wall,0.,-.20,WHITE,'Pale-rendered top storey with recessed windows')
        rect(b,fn,l,r,0.,.205,.005,-.20,BASE,'Short band of red wall below the upper floor')
        for lo,hi,proj,mat in [(.185,.236,.05,DARK),(.236,.305,.085,ACCENT),(.305,.353,.04,WHITE),(2.423,2.451,.018,ACCENT)]:
            pad=.4143*proj
            rect(b,fn,l-pad,r+pad,lo,hi,proj,-.145,mat,'Horizontal moulding follows the chamfer')
        for lo,hi,proj,mat in [(3.275,3.344,.665,DARK),(3.344,3.407,.715,ACCENT),(3.407,3.44,.705,DARK),(3.44,3.468,.72,ACCENT)]:
            pad=proj*.4143
            rect(b,fn,l-pad,r+pad,lo,hi,proj,-.20,mat,'Overhanging roof edge and continuous soffit')
    for c in CENTERS:window(b,c,far)
    for x in (-1.22,0.,1.22):
        # Narrow raised wall panels flank the pair of dark upper openings.
        rect(b,FACE,x-.044,x+.044,.61,1.81,.027,-.08,ACCENT,'Narrow pale upright on the window bay')
    rect(b,FACE,-1.27,1.27,2.027,2.059,.021,-.06,ACCENT,'Fine horizontal head of the outlined window panel')
    for fn,centers in [(FACE,(-.87,.87)),(LEFT,(-.71,)),(RIGHT,(.71,))]:
        for u in centers:bracket(b,fn,u,far)
    for part in b.parts:
        if part['material']==WHITE:
            part['texcoords']=[[(x+.19*y+3.2)/6.6,.025+z/3.74]for x,y,z in part['vertices']]
