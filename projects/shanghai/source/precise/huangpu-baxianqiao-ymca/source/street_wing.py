"""West-facing wing with its two eaves and chamfered portal, in Blender metres."""
from math import cos, sin, pi
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering
from eaves import add_eaves

def material(rgb, roughness=.8, metallic=0):
    return {'color':rgb,'roughness':roughness,'metallic':metallic}

PALETTE={
    'brown brick':material([.37,.165,.118]),'brick joint':material([.26,.145,.117]),
    'buff artificial granite':material([.62,.46,.275]),'pale carved stone':material([.68,.56,.39]),
    'window glazing':material([.13,.19,.21],.30,.22),'dark sash':material([.105,.105,.08],.53,.2),
    'blue glazed tile':material([.055,.105,.17],.37,.13),'glazed tile rib':material([.11,.18,.24],.37,.15),
    'vermilion':material([.51,.14,.105]),'painted blue green':material([.20,.43,.42]),
    'ivory paint':material([.65,.69,.60]),'door timber':material([.29,.095,.048]),
    'plaque gold':material([.69,.49,.18],.52,.22),'flat upper roof':material([.23,.255,.22]),
    'plain party wall':material([.38,.205,.163]),'portal shadow':material([.13,.11,.08])}
GLASS='window glazing'
SASH='dark sash'
BRICK='brown brick'
STONE='buff artificial granite'
TRIM='pale carved stone'
FRONT_Y=.14
HALF=18.43
CORNICE=11.35
BRICK_TOP=27.66
GALLERY_TOP=31.84
FONT=Path(__file__).with_name('fonts')/'BaxianqiaoPlaque.otf'


def windows(f, hole, lod, cols=2, rows=3, label='sash', frame=SASH, setback=.29):
    x0,z0,x1,z1=hole.bounds
    backing=hole.buffer(.009,join_style='mitre').intersection(box(x0-.05,max(0,z0-.02),x1+.05,z1+.02))
    f.prism(backing,-setback-.04,-setback,GLASS,label+'/glass')
    bars=[]
    if lod:
        cols,rows=min(2,cols),min(2,rows)
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols
        bars.append(box(x-.023,z0,x+.023,z1))
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows
        bars.append(box(x0,z-.025,x1,z+.025))
    panes=hole.buffer(-.066,join_style='mitre').difference(unary_union(bars))
    f.prism(hole.buffer(-.016,join_style='mitre').difference(panes),-setback+.025,-setback+.083,frame,label+'/grid')


def strip(f,z,h,d,mat,label):
    f.box(0,z,f.length,h,.19+d,(d-.19)/2,mat,label)


def portals(f,lod):
    # A tall chamfered outline encloses the modern doors and the clerestory.
    def chamfered(hw,bottom,top,cut):
        return Polygon([(-hw,bottom),(hw,bottom),(hw,top-cut),(hw-cut,top),
                        (-hw+cut,top),(-hw,top-cut)])
    portal=chamfered(1.70,0,7.65,.68)
    surround=chamfered(2.18,0,8.14,.97).difference(portal)
    f.prism(surround,-.12,.24,TRIM,'carved doorway surround')
    f.prism(portal,-1.0,-.96,'portal shadow','recessed doorway back')
    windows(f,opening(0,.14,2.88,2.82),lod,4,4,'recessed timber doors','door timber',.74)
    windows(f,opening(0,4.95,2.72,1.95),lod,4,3,'upper vestibule lights',SASH,.67)
    f.box(0,3.48,2.95,.73,.14,-.64,'portal shadow','name board')
    add_facade_lettering(f,'青年会',0,3.48,1.72,.42,-.559,-.53,'plaque gold',font=FONT)
    # Cast floral relief on the outer jambs is modelled as repeated scrolls;
    # the worn historical relief is not individually traced.
    for sign in (-1,1):
        for z in (.93,2.30,3.67,5.04,6.41):
            x=sign*1.95
            f.prism(Polygon([(x-.12,z-.29),(x+.02,z-.19),(x+.15,z+.19),(x+.01,z+.28)]),
                    .245,.29,STONE,'carved jamb scrolls')
            if not lod:
                pts=[f.point(x+.128*cos(a),z+.22*sin(a),.294) for a in
                     [i*pi/10 for i in range(18)]]
                f.builder.tube(pts,.028,TRIM,6,'Entrance/jamb scroll outline')
    # Modern canopy documented in the entrance photograph. The historical
    # jambs remain readable from both the street and the short side returns.
    f.box(0,4.88,4.18,.075,1.86,.77,GLASS,'glazed canopy')
    for x in (-2.07,0,2.07):
        f.box(x,4.91,.078,.12,1.95,.77,SASH,'canopy steel channels')
    f.box(0,4.94,4.23,.24,.095,1.72,SASH,'canopy leading edge')
    return portal


def stone_base(f,is_front,lod):
    holes=[]
    centers=[i*4.08 for i in range(-4,5)] if is_front else [-3.22,0,3.22]
    for u in centers:
        for row,z,w,h in [(0,.38,2.23,2.69),(1,4.31,1.53,2.75),(2,8.32,1.43,2.05)]:
            if is_front and row<=1 and abs(u)<.01:continue
            if is_front and row==0 and abs(abs(u)-4.08)<.01:
                hole=opening(u,0,1.35,2.78);holes.append(hole)
                windows(f,hole,lod,2,3,'side lobby doors','door timber',.48)
                continue
            hole=opening(u,z,w,h);holes.append(hole)
            windows(f,hole,lod,3,4,'stone storeys')
    if is_front:
        # The two smaller doors immediately flank the taller stone frame.
        holes.append(portals(f,lod))
    f.wall(0,CORNICE,holes,.40,STONE)
    for z,h,projection in [(3.33,.14,.12),(10.96,.16,.21),(11.30,.32,.30)]:
        if is_front and z<4:
            length=f.length/2-2.20
            for sign in (-1,1):
                f.box(sign*(2.20+length/2),z,length,h,projection+.19,(projection-.19)/2,
                      TRIM,'lower belt outside entrance')
        else:
            strip(f,z,h,projection,TRIM,'carved granite belt')
    n=round(f.length/.95)
    for i in range(n):
        u=(i+.5)*f.length/n-f.length/2
        diamond=Polygon([(u-.14,11.31),(u,11.41),(u+.14,11.31),(u,11.21)])
        f.prism(diamond,.302,.327,STONE,'belt lozenge')


def brick_storeys(f,is_front,lod):
    holes=[]
    windows_by_axis=[]
    if is_front:
        for i in range(-4,5):
            x=i*4.08
            windows_by_axis.extend([x-.72,x+.72] if i in (-3,-2,0,2,3) else [x])
    else:
        windows_by_axis=[-3.23,0,3.23]
    for level in range(5):
        z=CORNICE+.37+level*3.15
        for u in windows_by_axis:
            hole=opening(u,z,1.02,1.89);holes.append(hole)
            windows(f,hole,lod,2,3,'residential windows')
            f.box(u,z-.047,1.16,.09,.24,.035,BRICK,'brick sills')
    masonry=f.wall(CORNICE,BRICK_TOP,holes,.38,BRICK)
    # Observable narrow horizontal bed joints, drawn only on full masonry.
    if not lod:
        for k in range(1,85):
            z=CORNICE+k*.19
            band=masonry.intersection(box(-f.length/2,z-.009,f.length/2,z+.009))
            if not band.is_empty:f.prism(band,.002,.013,'brick joint','brick bed joints')


def painted_eaves(f,z,lod,is_front):
    strip(f,z,.45,.21,'painted blue green','painted frieze')
    strip(f,z-.245,.06,.23,'vermilion','painted frieze border')
    n=round(f.length/(1.24 if is_front else 1.38))
    for j in range(n):
        u=(j+.5)*f.length/n-f.length/2
        if j%2==0:
            f.box(u,z,.71,.28,.043,.23,'ivory paint','frieze panel')
            if not lod:
                outer=Polygon([(u-.15,z),(u,z+.12),(u+.15,z),(u,z-.12)])
                f.prism(outer.difference(outer.buffer(-.039)),.253,.273,'painted blue green','painted diamond')
        # Corbel arms get successively wider toward the tile skirt.
        f.box(u,z+.32,.21,.17,.55,.13,'painted blue green','dougong bracket foot')
        f.box(u,z+.47,.47,.14,.75,.22,'ivory paint','dougong bracket arms')
        if not lod:
            for side in (-1,1):
                f.box(u+side*.16,z+.54,.17,.16,.84,.27,'painted blue green','dougong bearing blocks')


def gallery(f,is_front,lod):
    holes=[]
    if is_front:
        for i in range(-4,5):
            if abs(i)==4:
                hole=opening(i*4.08,29.33,1.12,1.65)
            else:
                hole=opening(i*4.08,29.28,3.49,1.74)
            holes.append(hole);windows(f,hole,lod,7 if abs(i)<4 else 2,3,'gallery timber lights')
        for i in range(-4,4):
            f.box((i+.5)*4.08,30.30,.31,2.38,.26,.028,'vermilion','red gallery piers')
    else:
        for u in (-3.22,0,3.22):
            hole=opening(u,29.28,1.20,1.71)
            holes.append(hole);windows(f,hole,lod,2,3,'gallery end sash')
    f.wall(BRICK_TOP,GALLERY_TOP,holes,.38,BRICK)
    painted_eaves(f,27.54,lod,is_front)
    painted_eaves(f,31.48,lod,is_front)


def add_street_wing(b,lod):
    ring=[(-HALF,FRONT_Y),(HALF,FRONT_Y),(18.31,11.36),(-18.95,10.64)]
    for i,label in enumerate(['West street face','South end','East cut wall','North end']):
        f=Facade(b,ring[i],ring[(i+1)%4],label)
        if i==2:
            f.wall(0,GALLERY_TOP,(),.28,'plain party wall')
            continue
        stone_base(f,i==0,lod);brick_storeys(f,i==0,lod);gallery(f,i==0,lod)
    # Roof inner parapet ties the flat deck to the sloped upper rim. The
    # unobstructed southern courtyard lies beyond the rear wall.
    b.plan_prism(Polygon(ring),GALLERY_TOP-.12,GALLERY_TOP,'flat upper roof','Upper ceiling')
    add_eaves(b,lod)
