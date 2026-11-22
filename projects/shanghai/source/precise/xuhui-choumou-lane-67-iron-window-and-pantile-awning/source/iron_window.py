"""Recessed pointed iron sash and tiled awning at 67 Lane 1857, Middle Huaihai Road."""
from pathlib import Path
from math import sin,cos,pi
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box

ID='xuhui-choumou-lane-67-iron-window-and-pantile-awning'
WALL='Ochre roughcast';CLAY='Mottled burnt clay';SILL='Pressed red window sill bricks';MORTAR='Bedding mortar';IRON='Painted ironwork';SPANDREL='Recessed warm spandrel';GLASS='Blue green reflective glass';GLOW='Muted lower window glass';FASCIA='Deep red painted fascia';FLASH='Grey flashing';SHADE='Shaded entry'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[1.,1.,1.],.99),(CLAY,[1.,1.,1.],.88),(SILL,[1.,1.,1.],.94),(MORTAR,[.66,.60,.50],.97),(IRON,[.18,.195,.18],.69),(SPANDREL,[.49,.45,.38],.95),(GLASS,[.27,.325,.33],.33),(GLOW,[.37,.39,.346],.35),(FASCIA,[.33,.255,.212],.86),(FLASH,[.38,.41,.40],.86),(SHADE,[.23,.235,.209],.87)]}
R=.751;SPRING=2.93;APEX=4.20;BASE=1.50
def texture():
    p=Path(__file__).with_name('roughcast-and-weathered-terracotta.png')
    if not p.is_file() or Image.open(p).width!=768:
        rng=np.random.default_rng(763);n=256
        def cloud(sw,sh):return np.asarray(Image.fromarray(rng.integers(0,255,(sh,sw),dtype='uint8')).resize((n,n),Image.Resampling.BICUBIC),float)-128
        gravel=cloud(25,30)*.030+cloud(170,190)*.054+rng.normal(0,2.65,(n,n));patina=cloud(9,11)*.11+cloud(40,36)*.061+rng.normal(0,3.4,(n,n))
        panels=[np.array(c)+noise[:,:,None] for c,noise in [([190,182,155],gravel),([153,105,77],patina),([171,127,95],patina*.78+cloud(35,70)*.035)]]
        Image.fromarray(np.clip(np.concatenate(panels,axis=1),0,255).astype('uint8')).quantize(208).save(p)
    for m in (WALL,CLAY,SILL):PALETTE[m]['texture']=str(p)
def top(x):
    return SPRING+(APEX-SPRING)*max(0,1-(abs(x)/R)**1.57)**.69
def inner(t,side):return side*(.148+.397*t**1.47),2.923+.70*t
def tile_height(y):return .488+(y+1.095)*.365
TILES=np.linspace(-1.55,1.55,12)
def add_building(b,far=False):
    texture()
    def block(x0,x1,y0,y1,z0,z1,m,label):
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=label)
    def skin(poly,f,r,m,label):b.prism(poly,-r,-f,lambda x,z,d:(x,-d,z),m,label)
    def tube(points,r,m,label):b.tube(points,r,m,7 if far else 12,label)
    def wire(points,r,n):tube([(x,-.011,z)for x,z in points],r,IRON,n)
    outside=box(-1.72,.042,1.72,4.64)
    openings=box(-R-.055,BASE-.027,R+.055,APEX+.085).union(box(-.77,.036,.77,.96))
    skin(outside.difference(openings),0,.42,WALL,'Roughcast wall with separate window and entry openings')
    block(-.765,.765,.19,.31,.04,.96,SHADE,'Shaded top of entrance below the reconstructed roof')
    xs=np.linspace(-R,R,31 if far else 75);curve=[(x,top(x))for x in xs]
    silhouette=Polygon([(-R,BASE),(R,BASE),*curve[::-1],(-R,BASE)])
    skin(box(-R-.055,BASE-.027,R+.055,APEX+.085).difference(silhouette),.035,.087,SPANDREL,'Backing to the two spandrels')
    skin(silhouette,.028,.041,GLASS,'Continuous inset glazing beneath pointed head')
    for x in (-1,1):
        block((-.72 if x<0 else .025),(-.025 if x<0 else .72),.019,.027,BASE+.04,2.49,GLOW,'Two muted lower lights')
    for x in (-R,0,R):block(x-.018,x+.018,-.009,.025,BASE,APEX-.012 if x==0 else SPRING,IRON,'Outer jambs and centre mullion')
    for z in (BASE,2.52,2.93):block(-R,R,-.017,.025,z-.022,z+.022,IRON,'Horizontal metal sash rails')
    wire(curve,.020,'Pointed arched perimeter')
    for side in (-1,1):
        wire([inner(t,side)for t in np.linspace(0,1,17 if far else 32)],.016,'Pair of curved upper glazing bars')
        for i,(x,z,size) in enumerate([(.645,3.65,.050),(.650,3.79,.066),(.687,3.96,.074),(.552,4.074,.054),(.407,4.13,.044)]):
            coords=[]
            for t in np.linspace(0,2.78*pi,13 if far else 27):
                radius=size*(1-.89*t/(2.78*pi));coords.append((side*(x+radius*cos(t)),z+radius*sin(t)))
            wire(coords,.009 if far else .008,'Scrolls in ironwork of upper spandrel')
        wire([(side*x,z)for x,z in [(.754,3.56),(.704,3.73),(.685,3.91),(.606,4.028),(.495,4.102),(.360,4.145)]],.010,'Scroll supporting tendril')
    block(-.923,.923,-.179,.154,1.317,1.46,MORTAR,'Mortar bed under projecting sill')
    for i in range(17):
        x=-.925+i*(1.85/17);block(x+.004,x+1.85/17-.004,-.205,.139,1.344,1.490,SILL,'Edge-set brick sill units')
    block(-1.69,1.69,-1.08,-.992,.257,.452,FASCIA,'Front edge below tile mouths')
    block(-1.665,1.665,-1.043,.01,.324,.43,FASCIA,'Underside of entrance canopy')
    block(-1.675,1.675,-.05,.035,.863,1.00,FLASH,'Upstand flashing at wall junction')
    # Every tile has an underside and cut edges; adjacent courses overlap along the roof slope.
    ends=[(-1.098,-.689),(-.782,-.381),(-.473,-.084),(-.173,.003)]
    def curved_tile(cx,a,y1,y2,convex,course,lab):
        theta=np.linspace(.02,pi-.02,9 if far else 17)
        z=lambda ang,y:tile_height(y)+(course*.012)+(.105*sin(ang) if convex else -.052*sin(ang))
        verts=[]
        for surf in (0,-.016):
            for y in (y1,y2):
                verts.extend((cx+a*cos(t),y,z(t,y)+surf)for t in theta)
        n=len(theta);faces=[]
        for j in range(n-1):
            faces.extend([(j,j+1,j+1+n,j+n),(2*n+j,3*n+j,3*n+j+1,2*n+j+1),(j,2*n+j,2*n+j+1,j+1),(j+n,j+1+n,3*n+j+1,3*n+j)])
        faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
        # The parameter traverses +X to -X. Reverse both skins and edges to keep the upper visible normal positive.
        b.add(verts,[tuple(reversed(f))for f in faces],CLAY,lab)
    for c,(y1,y2)in enumerate(ends):
        for x in TILES:curved_tile(x,.085,y1,y2,True,c,'Overlapping clay barrel caps')
        for x in (TILES[:-1]+TILES[1:])/2:curved_tile(x,.119,y1+.012,y2,False,c,'Concave channel tiles between caps')
    for part in b.parts:
        mat=part['material']
        if mat in (WALL,CLAY,SILL):
            slot=(WALL,CLAY,SILL).index(mat)
            part['texcoords']=[((slot+.02+.96*((x+.26*y+1.80)/3.78%1))/3,.98-.96*((z+.53*y+.61)/5.72%1))for x,y,z in part['vertices']]
