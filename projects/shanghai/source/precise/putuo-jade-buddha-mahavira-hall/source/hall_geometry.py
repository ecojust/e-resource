"""Measured roof envelope and original exterior modeling for the 2017-relocated hall."""
from math import ceil, cos, pi, sin
from pathlib import Path
from shapely.geometry import Point, Polygon, box
from shapely import affinity
from photo_architecture import Facade
from sign_lettering import lettering_shapes

TILE='weathered graphite clay tiles'
CAP='silver grey ridge tiles'
EAVE='deep umber timber soffit'
WOOD='dark lacquered timber'
RED='cinnabar plaque and posts'
GOLD='warm gilt lettering'
WALL='ochre lime plaster'
BASE='grey carved stone'
STEP='pale granite treads'
DARK='recessed door and screen shadow'
IRON='bronze lattice'
PALETTE={
    TILE:{'color':[.225,.233,.231],'roughness':.80},
    CAP:{'color':[.342,.349,.340],'roughness':.78},
    EAVE:{'color':[.144,.096,.069],'roughness':.82},
    WOOD:{'color':[.215,.135,.099],'roughness':.60},
    RED:{'color':[.513,.114,.070],'roughness':.64},
    GOLD:{'color':[.90,.697,.302],'roughness':.49,'metallic':.23},
    WALL:{'color':[.797,.628,.370],'roughness':.84},
    BASE:{'color':[.470,.463,.425],'roughness':.86},
    STEP:{'color':[.668,.649,.593],'roughness':.81},
    DARK:{'color':[.106,.083,.071],'roughness':.73},
    IRON:{'color':[.33,.239,.159],'roughness':.64,'metallic':.16},
}
# Each level is a separately editable curved roof. +X follows the northeast
# ridge. The front elevation is the south-facing (-Y) elevation in temple terms.
LEVELS={
    'lower':(14.55,10.50,5.88,9.78,6.22,8.06,1.56),
    'upper':(10.75,6.83,9.62,4.82,2.95,11.26,1.49),
}


def surface(level, side, u, t):
    """Point at fraction t from the upturned eave to the head of the hip."""
    ex,ey,low,ix,iy,high,turn=LEVELS[level]
    w=ex+(ix-ex)*t
    d=ey+(iy-ey)*t
    # The lifted hip is concentrated at each corner, tapering on both faces.
    z=low+(high-low)*(.39*t+.61*t*t)+turn*abs(u)**5*(1-t)**2
    if side==0:return (u*w,-d,z)
    if side==1:return (w,u*d,z)
    if side==2:return (-u*w,d,z)
    return (-w,-u*d,z)


def sheet(builder, rows, material, label):
    verts=[p for row in rows for p in row];nc=len(rows[0])
    faces=[(j*nc+i,j*nc+i+1,(j+1)*nc+i+1,(j+1)*nc+i)
           for j in range(len(rows)-1) for i in range(nc-1)]
    builder.add(verts,faces,material,label)


def rib(builder, path, axis, material, label, width=.034, rise=.040):
    ux,uy=axis
    rings=[[(x-ux*width,y-uy*width,z+.012),(x,y,z+rise),
            (x+ux*width,y+uy*width,z+.012)] for x,y,z in path]
    sheet(builder,rings,material,label)


def eaves(builder,level,lod):
    ex,ey,_,ix,iy,high,_=LEVELS[level]
    name=level+' eaves'
    for side in range(4):
        nc=8 if lod else 16; nr=4 if lod else 7
        u=[-1+2*i/nc for i in range(nc+1)];t=[j/nr for j in range(nr+1)]
        rows=[[surface(level,side,a,b) for a in u] for b in t]
        sheet(builder,rows,TILE,name+'/tile slopes')
        bottom=[(x,y,z-.23) for x,y,z in rows[0]]
        # Trace the actual turned hip underside. A flat inward continuation
        # can cut through the tiled surface where the lifted corner descends.
        soffit=[bottom]
        for b in t[1:]:
            path=[surface(level,side,a,b) for a in u]
            soffit.append([(x,y,z-.23) for x,y,z in path])
            if b>=.29:break
        sheet(builder,[bottom,rows[0]],EAVE,name+'/timber eave fascia')
        sheet(builder,list(reversed(soffit)),EAVE,name+'/curved timber soffit')
        builder.tube(rows[0],.075,CAP,6,name+'/continuous eave course')
        spacing=.65 if lod else .31
        count=ceil(2*(ex if side%2==0 else ey)/spacing)
        across=(1,0) if side%2==0 else (0,1)
        for i in range(1,count):
            a=-1+2*i/count
            path=[surface(level,side,a,b) for b in t]
            rib(builder,path,across,CAP,name+'/convex tile runs',.035 if not lod else .048)
        hip=[surface(level,side,-1,b) for b in t]
        builder.tube([(x,y,z+.10)for x,y,z in hip],.105,CAP,7,name+'/curved diagonal ridge')
        # A small terminal folds upwards at each of the four photographed tips.
        x,y,z=hip[0];rad=(x*x+y*y)**.5;dx,dy=x/rad,y/rad
        tail=[(x+dx*r,y+dy*r,z+h) for r,h in [(0,.02),(.15,.19),(.30,.43),(.32,.56)]]
        builder.tube(tail,.066,CAP,7,name+'/turned eave tips')
    if level=='lower':
        builder.plan_prism(box(-ix,-iy,ix,iy),high-.14,high,TILE,'lower roof central decking')


def gable_and_ridge(builder,lod):
    x=4.82;y=2.95;z=11.26;ridge=12.59
    for sign in [-1,1]:
        # Upper two roof planes keep a straight gable end above the four hips.
        rows=[]
        for j in range(6):
            t=j/5
            rows.append([(-x,sign*y*(1-t),z+(ridge-z)*(.87*t+.13*t*t)),
                         (x,sign*y*(1-t),z+(ridge-z)*(.87*t+.13*t*t))])
        sheet(builder,rows if sign<0 else [r[::-1]for r in rows],TILE,'upper gable/upper pitches')
        count=16 if lod else 37
        for i in range(1,count):
            xx=-x+2*x*i/count
            rib(builder,[(xx,r[0][1],r[0][2])for r in rows],(1,0),CAP,'upper gable/vertical tile ribs')
        # Fill the upright triangular gable ends, visible above the side hips.
        sx=x*sign
        builder.add([(sx,-y,z),(sx,y,z),(sx,0,ridge)],[(0,1,2) if sign>0 else (0,2,1)],WOOD,'upper gable/timber end')
        builder.tube([(sx,-y,z),(sx,0,ridge),(sx,y,z)],.10,CAP,7,'upper gable/sloping verge')
    builder.box((0,0,ridge+.14),(9.94,.38,.30),TILE,label='main ridge/ceramic spine')
    builder.box((0,-.005,ridge+.42),(9.93,.29,.35),CAP,label='main ridge/raised carved frieze')
    for s in [-1,1]:
        tail=[(s*(4.73+dx),0,ridge+zz) for dx,zz in
              [(0,.24),(.17,.49),(.25,.72),(.22,.93),(.09,1.06),(-.03,1.00),(-.03,.88)]]
        builder.tube(tail,.090,CAP,8,'main ridge/turned ceramic terminal')
    if not lod:
        for x0 in [-3.96,-3.32,-2.69,-2.06,-1.43,-.80,.80,1.43,2.06,2.69,3.32,3.96]:
            for s in [-1,1]:
                pts=[(x0+.21*cos(t*pi/8),s*.17,ridge+.43+.095*sin(t*pi/8))for t in range(17)]
                builder.tube(pts,.027,TILE,5,'main ridge/openwork panel relief')


def platform(builder,lod):
    builder.plan_prism(box(-12.35,-8.60,12.35,8.75),.01,.82,BASE,'hall platform/stone plinth')
    builder.plan_prism(box(-12.48,-8.71,12.48,8.85),.82,1.02,STEP,'hall platform/coping')
    steps=6
    for i in range(steps):
        edge=-10.82+.36*i
        builder.box((0,(edge-8.60)/2,(i+1)*.16/2),(6.1,-8.60-edge,(i+1)*.16),STEP,label='hall platform/central stone stair')
    # The central flight interrupts both balustrades.
    for s in [-1,1]:
        first,last=3.26,9.20
        for z,h,w in [(1.25,.20,.25),(1.71,.13,.20)]:
            builder.box((s*(first+last)/2,-8.43,z),(last-first,w,h),STEP,label='hall platform/stone railing')
        for i in range(6):
            xx=s*(first+(last-first)*i/5)
            builder.box((xx,-8.43,1.44),(.19,.23,.80),BASE,label='hall platform/rail uprights')
            builder.box((xx,-8.43,1.88),(.24,.27,.15),STEP,label='hall platform/post caps')


def doors(builder,lod):
    y=-6.87
    front=Facade(builder,(-11.29,y),(11.29,y),'front painted hall')
    holes=[]
    for center in [-5.31,0,5.31]:
        width=4.20
        rect=box(center-width/2,1.08,center+width/2,4.90);holes.append(rect)
        front.prism(rect,-.33,-.28,DARK,'deep door screen')
        leaves=4
        for j in range(leaves):
            u=center-width/2+(j+.5)*width/leaves
            front.box(u,2.95,width/leaves-.08,3.60,.085,-.19,WOOD,'panelled folding doors')
            front.box(u,3.62,width/leaves-.24,2.08,.035,-.131,DARK,'recessed upper panel')
            front.box(u,1.69,width/leaves-.25,.66,.048,-.128,IRON,'lower panel relief')
            if lod:
                for z in [3.14,3.66,4.16]:
                    front.box(u,z,width/leaves-.24,.035,.035,-.116,IRON,'lattice crossbars')
            else:
                for k in range(4):
                    front.box(u+(k-1.5)*.188,3.64,.030,2.01,.038,-.105,IRON,'lattice verticals')
                for k in range(8):
                    front.box(u,2.72+.25*k,.78,.029,.04,-.099,IRON,'lattice rails')
                for k in [0,1,2,3]:
                    h=2.89+.46*k
                    for s in [-1,1]:
                        front.line((u-.30,h, -.078),(u,h+s*.14,-.078),.018,IRON,5,'lattice fretwork')
                        front.line((u,h+s*.14,-.078),(u+.30,h,-.078),.018,IRON,5,'lattice fretwork')
    # Flanking circular openings are visible in the yellow walls; the back
    # plates remain behind the cut stone surrounds.
    for u in [-9.38,9.38]:
        o=Point(u,3.65).buffer(.72,quad_segs=10 if lod else 16);holes.append(o)
        front.prism(o,-.35,-.31,DARK,'recessed circular opening')
        front.prism(o.buffer(.125).difference(o),.001,.092,STEP,'carved circular surround')
        if not lod:
            for k in range(3):
                r=.19+.16*k
                line=Point(u,3.65).buffer(r,quad_segs=9).boundary.buffer(.025)
                front.prism(line,.021,.055,IRON,'round lattice rings')
            for a in range(8):
                angle=a*pi/4
                front.line((u+.17*cos(angle),3.65+.17*sin(angle),.08),
                           (u+.65*cos(angle),3.65+.65*sin(angle),.08),.024,IRON,5,'round lattice spokes')
    front.wall(1.02,6.32,holes,thickness=.35,material=WALL)
    for a,b in [((11.29,y),(11.29,7.61)),((11.29,7.61),(-11.29,7.61)),((-11.29,7.61),(-11.29,y))]:
        f=Facade(builder,a,b,'side and rear returns');f.wall(1.02,6.25,material=WALL)
        f.beam(1.25,.29,.12,BASE)
    for xx in [-7.77,-2.65,2.65,7.77]:
        builder.tube([(xx,-7.93,1.19),(xx,-7.93,5.78)],.134,WOOD,10 if lod else 16,'front porch/round timber post')
        builder.box((xx,-7.93,1.13),(.37,.37,.25),BASE,label='front porch/stone post foot')
        for z,width,depth in [(5.14,.36,.41),(5.35,.60,.56),(5.56,.85,.71)]:
            builder.box((xx,-7.93,z),(width,depth,.18),RED,label='front porch/interlocking brackets')
    builder.box((0,-7.93,5.68),(17.3,.42,.35),EAVE,label='front porch/main lintel')


def drum_top(x,y):
    # The straight timber drum sits under the hip, whose central eaves
    # are lower than the turned corners. Follow the local roof plane.
    ex,ey,_,ix,iy,_,_=LEVELS['upper']
    tx=(ex-abs(x))/(ex-ix)
    ty=(ey-abs(y))/(ey-iy)
    t=max(0.,min(1.,tx,ty))
    if tx<ty:
        u=abs(y)/(ey+(iy-ey)*t)
    else:
        u=abs(x)/(ex+(ix-ex)*t)
    return surface('upper',0,min(1.,u),t)[2]-.23

def plaques(builder,lod):
    face=Facade(builder,(-9.78,-6.22),(9.78,-6.22),'clerestory facing the forecourt')
    for a,b in [((-9.78,-6.22),(9.78,-6.22)),((9.78,-6.22),(9.78,6.22)),
                ((9.78,6.22),(-9.78,6.22)),((-9.78,6.22),(-9.78,-6.22))]:
        panel=Facade(builder,a,b,'upper timber drum')
        n=8 if lod else 16
        us=[panel.length*(i/n-.5) for i in range(n+1)]
        upper=[]
        for u in us:
            x,y,_=panel.point(u,0)
            upper.append((u,drum_top(x,y)))
        outline=Polygon([(us[0],7.94),(us[-1],7.94),*reversed(upper)])
        panel.wall(7.94,11.6,material=WOOD,thickness=.28,outline=outline)
    font=Path(__file__).with_name('fonts')/'HallPlaques.otf'
    for u,char in [(-4.26,'殿'),(-1.42,'寶'),(1.42,'雄'),(4.26,'大')]:
        face.box(u,8.88,1.48,1.30,.135,.12,RED,'four crimson square tablets')
        face.prism(box(u-.74,8.23,u+.74,9.53).difference(box(u-.68,8.29,u+.68,9.47)),.187,.195,GOLD,'narrow plaque border')
        for _,glyph in lettering_shapes(char,1.02,1.05,font=font):
            face.prism(affinity.translate(glyph.simplify(.009 if lod else .003),xoff=u,yoff=8.88),.193,.222,GOLD,'four front inscriptions/'+char)
    # The second plaque's wording and location are documented by the temple.
    sign=Facade(builder,(-4,-7.93),(4,-7.93),'inner door lintel')
    sign.box(0,5.28,3.18,.67,.09,.24,GOLD,'door inscription tablet')
    if not lod:
        for i,ch in enumerate('虛崇道佛'):
            for _,g in lettering_shapes(ch,.57,.50,font=font):
                sign.prism(affinity.translate(g.simplify(.006),xoff=(i-1.5)*.7,yoff=5.28),.289,.305,WOOD,'inner door inscription/'+ch)


def add_building(builder,lod=False):
    platform(builder,lod)
    doors(builder,lod)
    plaques(builder,lod)
    eaves(builder,'lower',lod)
    eaves(builder,'upper',lod)
    gable_and_ridge(builder,lod)
