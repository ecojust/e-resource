"""Surviving north street front of the French Municipal Council at Central Plaza."""
from math import cos, sin, pi
from pathlib import Path
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

BRICK='pressed red face brick'; WARM='warm red brick'; DARK='dark red brick'; MORTAR='brick bed joints'
STONE='pale stone door surround'; COPING='weathered stone cornices'; FRAME='dark bronze casements'; GLASS='shop and office glass'
CANOPY='wine red canvas'; TILES='weathered clay roof'; FLASH='roof flashing'; STEP='street entrance granite'; LETTER='door lettering'
PALETTE={
 BRICK:dict(color=[.443,.187,.130],roughness=.86),WARM:dict(color=[.500,.224,.164],roughness=.87),
 DARK:dict(color=[.345,.147,.115],roughness=.9),MORTAR:dict(color=[.299,.178,.145],roughness=.88),
 STONE:dict(color=[.701,.645,.506],roughness=.77),COPING:dict(color=[.53,.49,.419],roughness=.80),
 FRAME:dict(color=[.134,.119,.098],metallic=.41,roughness=.54),GLASS:dict(color=[.143,.193,.191],metallic=.20,roughness=.27),
 CANOPY:dict(color=[.318,.075,.109],roughness=.89),TILES:dict(color=[.44,.245,.179],roughness=.87),
 FLASH:dict(color=[.316,.308,.271],metallic=.18,roughness=.74),STEP:dict(color=[.446,.429,.385],roughness=.88),
 LETTER:dict(color=[.103,.104,.093],roughness=.64)}
FONT=Path(__file__).with_name('fonts')/'HuaihaiFrontPlaque.otf'
EXTENT=29.65
REAR=8.35
SECTIONS=[(-EXTENT,-19.40,.15,13.55,'east end pavilion'),(-19.40,-5.60,1.32,11.68,'east connecting bays'),
          (-5.60,5.60,0,14.20,'central entrance pavilion'),(5.60,19.40,1.32,11.68,'west connecting bays'),
          (19.40,EXTENT,.15,13.55,'west end pavilion')]


def wedge(b,left,right,profile,material,label):
    # Extrude a signed y/z (depth/height) roof or awning cross-section along the street.
    b.prism(Polygon(profile),left,right,lambda y,z,x:(x,y,z),material,label)


def sash(f,op,depth,columns=3,transoms=(.65,)):
    x0,z0,x1,z1=op.bounds
    pieces=[op.difference(op.buffer(-.094,join_style='mitre'))]
    for i in range(1,columns):
        x=x0+(x1-x0)*i/columns;pieces.append(box(x-.049,z0,x+.049,z1))
    for frac in transoms:
        z=z0+(z1-z0)*frac;pieces.append(box(x0,z-.048,x1,z+.048))
    f.prism(op.buffer(.012,join_style='mitre'),-depth-.025,-depth,GLASS,'recessed glazing')
    f.prism(unary_union(pieces).intersection(op),-depth+.013,-depth+.074,FRAME,'bronze window joinery')


def brick_skin(f,wall,width,top,low):
    # Beds are continuous; alternating perpends are most legible on the broad projecting piers.
    groups={BRICK:[],WARM:[],DARK:[]}; rowheight=.70 if low else .335
    for row in range(int(top/rowheight)+1):
        z=row*rowheight+.019;high=min(z+rowheight-.034,top)
        if high<=z:continue
        pitch=2.23 if low else .95;x=-width/2-pitch*(row%2)*.5;i=0
        while x<width/2:
            left=max(-width/2,x)+.013;right=min(width/2,x+pitch)-.013
            if right-left>.065:
                poly=wall.intersection(box(left,z,right,high))
                if poly.area>.008:
                    tone=(row*7+i*13)%23;groups[WARM if tone in (4,10,17) else DARK if tone in (3,21) else BRICK].append(poly)
            x+=pitch;i+=1
    for mat,pieces in groups.items():
        if pieces:f.prism(unary_union(pieces),.002,.034,mat,'bonded red masonry')
    lines=[box(-width/2,.59+i*.86,width/2,.64+i*.86)for i in range(int((top-.62)/.86)+1)]
    f.prism(unary_union(lines).intersection(wall),.036,.075,DARK,'chamfered horizontal brick bands')


def canopy(b,x,y,width,z):
    wedge(b,x-width/2,x+width/2,[(y+.06,z),(y-.93,z-.40),(y-.93,z-.68),(y-.87,z-.68),(y-.87,z-.45),(y+.06,z-.064)],CANOPY,'paired shop awnings / sloping fabric and valance')
    for u in [x-width*.39,x+width*.39]:
        b.tube([(u,y-.04,z-.74),(u,y-.83,z-.48)],.032,FRAME,sides=6,label='awning stays')


def dormer(b,x,y,low):
    # Small glazed roof openings have pitched caps, open window reveals and copper side cheeks.
    front=Facade(b,(x-1.0,y),(x+1.0,y),'roof dormer');shape=Polygon([(-.89,12.15),(.89,12.15),(.89,13.45),(0,14.07),(-.89,13.45)])
    op=box(-.56,12.24,.56,13.39);front.prism(shape.difference(op),-.88,.0,BRICK,'front and cheeks');sash(front,op,.24,2,())
    for sign in (-1,1):
        v=[(x,y-.16,14.13),(x+sign*.99,y-.16,13.46),(x+sign*.99,y+1.30,13.46),(x,y+1.30,14.13)]; b.add(v+[(a,b0,c-.08)for a,b0,c in v],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],FLASH,'dormer pitched metal cap')


def entrance(f,op,low):
    outer=opening(0,.48,4.55,6.16,arch=2.23,segments=24 if low else 48)
    f.prism(outer.difference(op),.032,.265,STONE,'rounded stone archivolt and jambs');sash(f,op,.81,2,(.53,.63))
    inner=op.buffer(-.12,join_style='mitre');zspring=4.57;bars=[]
    for deg in (31,61,90,119,149):
        a=deg*pi/180;bars.append(LineString([(0,zspring),(2.0*cos(a),zspring+1.85*sin(a))]).buffer(.045,cap_style='flat'))
    fan=unary_union(bars).intersection(inner);f.prism(fan,-.70,-.647,FRAME,'semicircular fanlight spokes')
    f.box(0,7.03,7.13,1.25,.31,.09,STONE,'Central Plaza entrance name tablet')
    add_facade_lettering(f,'中环广场',0,7.075,4.89,.62,.247,.289,LETTER,label='current entrance lettering',font=FONT)


def section(b,left,right,y,top,name,low):
    f=Facade(b,(left,y),(right,y),name);width=right-left;mid=(left+right)/2;cut=[];glazing=[]
    central=name.startswith('central');connector='connecting' in name
    xs=[-3.80,3.80]if connector else [0]
    if central:
        door=opening(0,.46,3.12,5.61,arch=1.53,segments=24 if low else 48);cut.append(door);entrance(f,door,low)
        for u in (-2.75,2.75):
            op=box(u-.38,.65,u+.38,5.02);cut.append(op);glazing.append((op,1))
        op=box(-2.71,8.22,2.71,11.63);cut.append(op);glazing.append((op,3))
    else:
        for u in xs:
            w=4.02 if connector else 5.20;ground=box(u-w/2,.83,u+w/2,5.00);upper=box(u-w/2,7.49,u+w/2,10.75 if connector else 11.46)
            cut.extend([ground,upper]);glazing.extend([(ground,3),(upper,3)])
            for z in (5.78,11.06 if connector else 11.87):canopy(b,mid+u,y,w+.24,z)
            f.box(u,.70,w+.38,.23,.24,.065,COPING,'projecting sill');f.box(u,7.38,w+.28,.18,.16,.053,COPING,'upper window sill')
    for op,cols in glazing:sash(f,op,.34,cols,() if op.bounds[1]>7 else (.81,))
    outline=box(-width/2,.05,width/2,top);wall=outline.difference(unary_union(cut));f.prism(wall,-.41,0,MORTAR,'street wall and deep reveals');brick_skin(f,wall,width,top,low)
    for z,w,h in [(top-.65,.22,.21),(top-.42,.42,.18),(top-.17,.54,.22)]:f.box(0,z,width+.13,h,w,.07,COPING,'stone entablature')
    f.prism(wall.intersection(box(-width/2,.06,width/2,.49)),.038,.102,STEP,'granite plinth')
    # Close only the narrow new strip. The city retains the rear podium and tower.
    b.plan_prism(box(left,y+.84,right,REAR),.03,.47,STEP,name+'/floor behind doors')
    if not central:b.plan_prism(box(left,y+.42,right,y+.85),.03,.45,STEP,name+'/window ledge backing')
    if connector:
        wedge(b,left,right,[(y-.14,11.72),(y+3.96,14.02),(REAR,13.63),(REAR,13.39),(y+3.96,13.77),(y-.14,11.51)],TILES,'sloping tile roof / '+name)
        for offset in (-4.44,0,4.44):dormer(b,mid+offset,y+1.46,low)
        if not low:
            for i in range(1,14):
                start=y+.27*i;z=11.72+.56*(start-y+.14);wedge(b,left+.02,right-.02,[(start,z+.035),(start+.06,z+.057),(start+.06,z-.015),(start,z-.026)],DARK,'overlapping tile courses')
    else:
        b.plan_prism(box(left-.04,y-.02,right+.04,REAR),top-.21,top-.04,FLASH,name+'/flat roof inside coping')
        for side in [-1,1]:f.box(side*(width/2-.54),top*.51,.43,top-.75,.28,.09,BRICK,'raised corner quoin')
    end_height=13.63 if connector else top-.04
    back=Facade(b,(right,REAR),(left,REAR),name+' rear section');back.wall(.06,end_height,thickness=.24,material=BRICK)
    if not connector:
        # The raised end and middle bays have brick cheeks above the sloping connecting roofs.
        for x,sgn in [(left,-1),(right,1)]:
            if abs(x)==EXTENT:continue
            a,c=((x,REAR),(x,y)) if sgn==-1 else ((x,y),(x,REAR));cheek=Facade(b,a,c,name+' attic cheek');cheek.wall(11.38,top-.045,thickness=.17,material=BRICK)
    return top


def make_council(b,low=False):
    for left,right,y,top,name in SECTIONS:section(b,left,right,y,top,name,low)
    for i,(left,right,y,top,name) in enumerate(SECTIONS):
        if i and y!=SECTIONS[i-1][2]:
            yy=SECTIONS[i-1][2];f=Facade(b,(left,y),(left,yy),'brick at inset wall junction');f.wall(.10,min(top,SECTIONS[i-1][3])-.1,thickness=.24,material=BRICK)
    for x,sgn in [(-EXTENT,-1),(EXTENT,1)]:
        a,c=((x,REAR),(x,.15))if sgn==-1 else ((x,.15),(x,REAR));Facade(b,a,c,'short pavilion return').wall(.07,13.45,thickness=.30,material=BRICK)
    for n in range(4):
        b.plan_prism(box(-5.54,-1.42+n*.355,5.54,.86),n*.113,(n+1)*.113,STEP,'four granite entrance treads')
