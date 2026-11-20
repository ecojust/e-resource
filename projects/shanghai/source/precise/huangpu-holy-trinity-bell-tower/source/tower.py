"""Independent north belfry in metres, with the garden front facing local -Y."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from photo_architecture import Facade
from cathedral import PALETTE as CHURCH_PALETTE
from gothic import arch, light, colonnade, RED, DARK, BASE, PALE
from roofs import slope

CLAY = 'terracotta spire'
LOUVRE = 'louvred shutter'
METAL = 'finial metal'
PALETTE = {**CHURCH_PALETTE,
    CLAY:{'color':[.49,.23,.135],'roughness':.78},
    LOUVRE:{'color':[.225,.228,.204],'roughness':.73},
    METAL:{'color':[.36,.345,.24],'roughness':.59,'metallic':.48}}
HALF = 3.20
DECK = 23.00


def belfry(f, lod, side):
    holes=[]
    # Lower garden face in the archive: two ground-stage windows with a single opening above.
    if side in ('Garden', 'North'):
        for u in (-1.08, 1.08):
            holes.append(light(f,u,1.02,.66,2.08,lod,columns=1))
        holes.append(light(f,0,5.54,.96,2.65,lod))
    if side=='Gallery':
        door,_,_=arch(.95,0,1.88,3.14,1.29,False,lod)
        holes.append(door)
        f.prism(door,-.46,-.43,'oak door','door behind covered gallery')
    for j in range(-2,3):
        hole,curve,_=arch(j*.825,10.15,.68,1.06,.455,False,lod)
        holes.append(hole)
        f.prism(hole,-.23,-.22,DARK,'small blind arcade recess')
        rim=hole.buffer(.07,join_style='mitre').difference(hole)
        f.prism(rim,-.03,.054,PALE,'blind arcade archivolt')
    for u in (-1.13,1.13):
        h,curve,spring=arch(u,12.01,1.64,7.13,1.27,False,lod)
        holes.append(h)
        crown=Polygon([*curve,*[(x,z+.16) for x,z in reversed(curve)]])
        f.prism(crown,-.02,.15,PALE,'pointed belfry archivolt')
        for offset in (-.85,.85):
            f.builder.lathe(f.point(u+offset,0,.047)[:2],
                [(11.83,.17),(12.06,.17),(12.14,.115),(spring-.29,.11),(spring-.24,.15),(spring-.04,.18),(spring,.17)],
                PALE,9 if lod else 16,f.label+'/paired slender jambs')
        # The broad horizontal louvres project from the back of each open belfry light.
        for k in range(6):
            z=12.55+k*.85
            cross=Polygon([(-.33,z+.07),(-.51,z+.17),(-.52,z+.10),(-.33,z)])
            f.builder.prism(cross,-u-.77,-u+.77,lambda d,h,t:f.point(-t,h,d),LOUVRE,f.label+'/angled louvres')
    f.wall(0,22.05,holes,.43,RED)
    for u in (-HALF+.28, HALF-.28):
        f.box(u,5.7,.55,11.4,.30,.07,RED,'tower angle buttress')
        f.box(u,15.46,.44,7.77,.24,.07,RED,'belfry angle pier')
        p=Polygon([(u-.38,18.26),(u+.38,18.26),(u,19.80)])
        f.prism(p,-.01,.20,PALE,'corner buttress pointed cap')
        f.prism(p.buffer(-.067,join_style='mitre'),.19,.225,RED,'brick face inside gable')
        for z in (1.05,7.65,11.70,17.95):
            f.box(u,z,.67,.17,.42,.07,PALE,'buttress weathering')
    for z,depth,material in [(.24,.15,BASE),(9.85,.11,PALE),(11.72,.19,PALE),(21.85,.24,PALE)]:
        f.beam(z,.16,depth,material,width=f.length+.12,label='belt course')
    for k in range(11):
        u=(k-5)*.535
        f.box(u,21.42,.19,.48,.20,.06,DARK,'corbel table')
    cuts=[]
    for k in range(13):
        window,_,_=arch((k-6)*.46,22.22,.26,.45,.13,True,lod)
        cuts.append(window)
    f.wall(22.05,22.91,cuts,.24,PALE)
    f.beam(22.97,.15,.20,PALE,width=f.length+.35,label='deck coping')


def pinnacle(b,x,y,lod):
    profile=[(22.96,.39),(23.18,.43),(23.29,.32),(24.63,.32),(24.72,.39),(24.85,.34),
             (26.49,.065),(26.58,.06)]
    b.lathe((x,y),profile,CLAY,8,'Four corner turrets/brick octagonal pinnacles')
    for z,r in [(23.28,.36),(24.70,.41),(25.39,.23)]:
        b.lathe((x,y),[(z-.036,r),(z+.036,r)],PALE,8,'Four corner turrets/stone collars')
    b.tube([(x,y,26.51),(x,y,26.99)],.034,METAL,6 if lod else 9,'Four corner turrets/finials')


def upper(b,lod):
    # The square parapet surrounds a separate octagonal lower spire stage.
    b.plan_prism(box(-3.28,-3.28,3.28,3.28),21.90,22.03,'slate roof','Square tower/platform')
    b.lathe((0,0),[(21.96,2.67),(23.12,2.67),(26.57,2.19),(30.25,1.88)],CLAY,8,'Spire/lower octagon')
    for k in range(4):
        a=k*pi/2
        tangent=(cos(a),sin(a));out=(sin(a),-cos(a));cx,cy=2.85*out[0],2.85*out[1]
        def end(t): return (cx+t*tangent[0],cy+t*tangent[1])
        f=Facade(b,end(-.91),end(.91),'Spire dormers')
        hole,curve,_=arch(0,24.24,.84,1.98,.63,False,lod)
        shape=Polygon([(-.91,23.79),(.91,23.79),(.91,25.63),(0,27.72),(-.91,25.63)])
        f.wall(23.79,27.72,[hole],.48,CLAY,shape)
        f.prism(hole,-.26,-.25,DARK,'dormer recess')
        for side in (-1,1):
            f.line((side*.91,25.63,.08),(0,27.75,.08),.075,PALE,7,'hood coping')
            f.box(side*.58,25.03,.12,1.75,.17,.04,PALE,'dormer stone jamb')
        f.beam(24.07,.12,.15,PALE,width=1.53,label='dormer sill')
    b.lathe((0,0),[(30.14,1.93),(30.27,1.98),(30.78,1.90),(30.86,1.88)],PALE,8,'Spire/stone band')
    for k in range(8):
        a=(k+.5)*pi/4;r=1.80
        b.box((r*cos(a),r*sin(a),30.49),(.22,.22,.22),DARK,label='Spire/dark band insets')
    b.lathe((0,0),[(30.78,1.90),(45.96,.145),(46.19,.082)],CLAY,8,'Spire/tall octagonal cone')
    for k in range(8):
        a=k*pi/4
        b.tube([(1.9*cos(a),1.9*sin(a),30.8),(.15*cos(a),.15*sin(a),45.96)],
               .029,CLAY,6,'Spire/arrises')
    for z in (33.8,37.35,40.9,44.1):
        r=1.90-(z-30.78)*(1.90-.145)/(45.96-30.78)
        b.lathe((0,0),[(z-.025,r+.025),(z+.025,r+.025)],DARK,8,'Spire/course joints')
    b.lathe((0,0),[(46.05,.09),(46.32,.19),(46.52,.11),(46.60,.06)],PALE,8,'Spire/finial socket')
    b.tube([(0,0,46.41),(0,0,48)],.041,METAL,10,'Spire/finial staff')
    b.tube([(-.31,0,47.54),(.31,0,47.54)],.035,METAL,8,'Spire/finial cross')
    for x in (-2.87,2.87):
        for y in (-2.87,2.87):pinnacle(b,x,y,lod)


def gallery(b,lod):
    # Positions follow the measured gap to the independent nave. The ends
    # remain open at the pavement, with the tower-entry door at the north end.
    x0,x1=-11.8,-3.2
    y0,y1=-3.10,1.20
    for a,c in [((x0,y0),(x1,y0)),((x1,y1),(x0,y1))]:
        f=Facade(b,a,c,'Covered link')
        colonnade(f,[1]*4,lod,top=4.08,spring=2.54,end_piers=.21,shaft_radius=.17)
        f.beam(4.08,.15,.13,PALE,width=f.length,label='eave band')
    b.plan_prism(box(x0,y0,x1,y1),0,.082,'porch pavement','Covered link/pavement')
    mid=(y0+y1)/2
    for y in (y0-.13,y1+.13):
        slope(b,[(x0,y,4.16),(x1,y,4.16),(x1,mid,4.78),(x0,mid,4.78)],'Covered link/low roof')


def add_tower(b,lod):
    corners=[(-HALF,-HALF),(HALF,-HALF),(HALF,HALF),(-HALF,HALF)]
    for i,title in enumerate(['Garden','North','Courtyard','Gallery']):
        belfry(Facade(b,corners[i],corners[(i+1)%4],title),lod,title)
    b.plan_prism(box(-HALF,-HALF,HALF,HALF),0,.09,BASE,'Tower/closed ground floor')
    upper(b,lod)
    gallery(b,lod)
