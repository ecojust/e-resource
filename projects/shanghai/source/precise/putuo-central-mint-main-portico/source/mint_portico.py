"""Six Ionic columns and the central pediment of the former Shanghai Central Mint.

The 2016 public exterior provides the adopted features. A historical frontal
photograph verifies their position within the long main building. Dimensions
are estimates from photograph proportions and the nominal footprint frontage.
"""
import math
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

STONE='warm grey dressed stone'
CARVED='pale capital and cornice stone'
BASE='granite steps'
JOINT='stone joint shadows'
BROWN='brown window frames'
GLASS='dark reflected window glass'
GOLD='gold parapet inscription'
ROOF='grey roof covering'
PALETTE={
    STONE:{'color':[.572,.548,.502],'roughness':.91},
    CARVED:{'color':[.683,.647,.565],'roughness':.87},
    BASE:{'color':[.462,.445,.415],'roughness':.93},
    JOINT:{'color':[.398,.375,.346],'roughness':.92},
    BROWN:{'color':[.282,.214,.163],'roughness':.76},
    GLASS:{'color':[.163,.177,.175],'roughness':.45,'metallic':.12},
    GOLD:{'color':[.767,.565,.220],'roughness':.45,'metallic':.6},
    ROOF:{'color':[.398,.386,.357],'roughness':.9}}
COLUMNS=(-7.40,-3.43,-2.05,2.05,3.43,7.40)
HALF=12.70
PORTICO=8.45
FONT=Path(__file__).parent/'fonts/MintNameSubset.otf'
def beam(f,u,z,w,h,depth,dist,mat,name):
    f.box(u,z,w,h,depth,dist,mat,name)

def windows(f,x,bottom,width,height,lod,depth=-.18):
    """Real openings with fitted glass, wood transoms, sills and layered casing."""
    opening=box(x-width/2,bottom,x+width/2,bottom+height)
    f.prism(opening.buffer(.012,join_style=2),depth-.025,depth,GLASS,'recessed glazing')
    inner=opening.buffer(-.067,join_style=2)
    f.prism(opening.difference(inner),depth+.008,.025,BROWN,'window jambs and lintel')
    cells=3 if width>=2 else 2
    for j in range(1,cells):
        beam(f,x-width/2+width*j/cells,bottom+height*.5,.063,height,.10,depth+.058,BROWN,'upright wood mullion')
    for z in [bottom+height*.68]+([] if lod or height<1.6 else [bottom+height*.33]):
        beam(f,x,z,width,.052,.095,depth+.052,BROWN,'window transom')
    if not lod and height>2:
        for j in range(cells):
            beam(f,x-width/2+width*(j+.5)/cells,bottom+height*.84,.027,height*.32,.046,depth+.043,BROWN,'upper light divider')
    return opening
def wall_panel(f,xx,lod,raised):
    """Portals under the portico or projecting bays on each side."""
    if raised:
        sizes=[(.92,2.38,3.38),(6.55,2.13,2.96),(12.12,2.40,1.84)]
    else:
        sizes=[(.78,2.84,3.7),(6.75,2.62,2.90),(12.23,2.04,1.65)]
    holes=[]
    for x in xx:
        for z,width,height in sizes:holes.append(windows(f,x,z,width,height,lod))
    base=f.wall(0,15.13,holes,.36,STONE)
    for x in xx:
        for z,width,height in sizes:
            for level,h,extra,d in ((z-.10,.15,.20,.14),(z+height+.12,.18,.28,.12)):
                beam(f,x,level,width+extra,h,d,d*.25,CARVED,'dressed stone sill and hood')
            if raised:
                for side in [-1,1]:
                    beam(f,x+side*(width*.5+.095),z+height*.5,.11,height+.16,.13,.035,CARVED,'raised window surround')
    if not lod:
        for row in range(1,20):
            z=.42+row*.74
            cut=base.intersection(box(-f.length*.5,z,f.length*.5,z+.014))
            if not cut.is_empty:f.prism(cut,.001,.009,JOINT,'ashlar bed joints')
    for z,h,depth in [(.32,.22,.20),(5.24,.23,.20),(5.58,.10,.23),(10.84,.20,.19),(11.02,.14,.27),(14.96,.27,.25)]:
        f.beam(z,h,depth,CARVED,label='storey string course')
def column(b,x,lod):
    """Tapered fluted shaft, moulded foot and paired Ionic volutes."""
    y=-2.21;seg=15 if lod else 30
    b.box((x,y,.89),(1.14,1.10,.22),BASE,label='Portico / square base')
    p=[(.93,.56),(1.00,.56),(1.06,.52),(1.12,.55),(1.19,.50),(1.24,.46),(1.30,.49),(1.36,.438)]
    b.lathe((x,y),p,CARVED,seg,'Portico / torus and scotia')
    rings=18 if lod else 22; samples=rings*(4 if lod else 6);flutes=[]
    for z,radius in [(1.34,.441),(1.59,.440),(3.95,.433),(6.51,.414),(9.05,.390),(9.20,.390)]:
        for j in range(samples):
            t=math.tau*j/samples
            r=radius-(.019 if lod else .028)*(.5+.5*math.cos(rings*t))
            flutes.append((x+r*math.cos(t),y+r*math.sin(t),z))
    sides=[]
    for level in range(5):
        for j in range(samples):
            a=level*samples+j;c=level*samples+(j+1)%samples;sides.append((a,c,c+samples,a+samples))
    b.add(flutes,sides,STONE,'Portico / fluted shafts')
    b.lathe((x,y),[(9.17,.391),(9.23,.421),(9.27,.443),(9.31,.432),(9.37,.462),(9.48,.452)],CARVED,seg,'Ionic / neck moulding')
    b.box((x,y,9.63),(1.16,.87,.17),CARVED,label='Ionic / horizontal echinus')
    for face in (-1,1):
        fy=y+face*.39
        for side in (-1,1):
            vs=[];st=15 if lod else 30
            for j in range(st):
                u=j/(st-1);angle=math.pi*.50+math.tau*1.24*u;rad=.225*(1-u)+.042*u
                vs.append((x+side*(.425+rad*math.cos(angle)),fy,9.40+rad*math.sin(angle)))
            b.tube(vs,.045,CARVED,5 if lod else 7,'Ionic / carved volutes')
    b.box((x,y,9.78),(1.31,.98,.15),CARVED,label='Ionic / square abaci')
def portico(b,lod):
    front=Facade(b,(-PORTICO,-2.58),(PORTICO,-2.58),'Portico')
    for i in range(6):
        step=.136*(i+1);low=-4.48+.305*i; b.box((0,(low+.6)/2,step*.5),(17.56-i*.05,.6-low,step),BASE,label='Portico / graduated granite treads')
    for x in COLUMNS:column(b,x,lod)
    for z,h,width,d in [(9.95,.29,16.64,3.08),(10.19,.13,16.85,3.14),(10.53,.62,16.61,3.13),(10.91,.17,16.84,3.20),(11.12,.22,17.12,3.29)]:
        b.box((0,-1.28,z),(width,d,h),CARVED if h<.4 else STONE,label='Portico / entablature and cornice')
    if not lod:
        for k in range(-42,43):
            front.box(k*.198,10.94,.11,.10,.18,.23,CARVED,'dentils under projecting cornice')
    tri=Polygon([(-8.52,11.20),(8.52,11.20),(0,14.05)])
    front.prism(tri,-2.85,.31,STONE,'triangular pediment')
    inner=tri.buffer(-.20,join_style=2)
    front.prism(tri.difference(inner),.295,.435,CARVED,'raking stone moulding')
    front.prism(inner.buffer(-.10,join_style=2),.307,.321,STONE,'recessed tympanum')
    for a,c in [((-8.63,11.32),(0,14.22)),((0,14.22),(8.63,11.32))]:
        front.line((a[0],a[1],.44),(c[0],c[1],.44),.105,CARVED,6 if lod else 10,'raking cornice')
def facade(b,lod=False):
    # Y increases into the wall; the front of the column drums is near −2.65m.
    f=Facade(b,(-8.22,0),(8.22,0),'Center wall')
    wall_panel(f,[-5.71,0,5.71],lod,False)
    for x in (-10.42,10.42):
        wing=Facade(b,(x-2.22,-.33),(x+2.22,-.33),'Flanking bay')
        # Remove the solid underlying panel throughout the inner glass opening.
        # The central wall ends before each flanking window.
        wall_panel(wing,[0],lod,True)
        for sign in (-1,1):
            wing.box(sign*1.93,5.75,.31,10.9,.30,.03,CARVED,'marginal pier')
            wing.box(sign*1.93,11.12,.55,.27,.49,.055,CARVED,'pier cap')
        profile=Polygon([(-2.22,15.02),(2.22,15.02),(2.22,15.63),(1.60,15.63),(1.33,16.01),(1.32,16.51),(1.19,16.72),(1.19,17.15),(-1.19,17.15),(-1.19,16.72),(-1.32,16.51),(-1.33,16.01),(-1.60,15.63),(-2.22,15.63)])
        wing.prism(profile,-1.09,.09,STONE,'stepped parapet above window group')
        for z,w in [(15.43,4.56),(16.50,2.79),(17.13,2.48)]:
            wing.box(0,z,w,.16,1.29,-.43,CARVED,'stepped parapet cap')
        wing.box(0,16.20,1.66,.73,.095,.112,JOINT,'recessed square plaque shadow')
        wing.box(0,16.21,1.56,.64,.115,.13,STONE,'plain plaque field')
    f.box(0,15.25,16.48,.64,1.11,-.47,STONE,'upper parapet')
    f.box(0,15.61,16.51,.12,1.19,-.47,CARVED,'upper parapet cap')
    add_facade_lettering(f,'上海造幣',0,15.23,7.20,.72,.095,.145,GOLD,label='four recorded gold characters',font=FONT)
    portico(b,lod)
    b.box((0,1.02,14.91),(25.18,2.10,.21),ROOF,label='Upper roof / visible leading edge')
