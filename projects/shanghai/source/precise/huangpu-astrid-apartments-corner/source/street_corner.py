"""Street corner of the Astrid Apartments. Author coordinates are metres, with +Y into the building."""
from math import pi, sin, cos, sqrt
from shapely.geometry import box, Polygon, LineString
from shapely import union_all
from photo_architecture import Facade

BUFF = 'honey glazed tile'
MINT = 'sage glazed tile'
SAND = 'yellow ochre brick'
JOINT = 'fine recessed tile joints'
FRAME = 'dark painted steel'
GLASS = 'smoky window glass'
STONE = 'pale artificial stone'
RELIEF = 'sandstone geometry'
BRONZE = 'patinated entrance metal'
ROOF = 'grey roof felt'
SECTION = 'section plane'
PALETTE = {name: dict(color=colour,roughness=rough,metallic=metal) for name, colour, rough, metal in [
    (BUFF,[.71,.568,.369],.66,0),(MINT,[.506,.562,.419],.64,0),
    (SAND,[.486,.316,.197],.79,0),(JOINT,[.56,.48,.36],.83,0),
    (FRAME,[.188,.207,.182],.53,.32),(GLASS,[.226,.289,.282],.28,.27),
    (STONE,[.71,.666,.561],.78,0),(RELIEF,[.565,.390,.247],.81,0),
    (BRONZE,[.218,.202,.17],.55,.46),(ROOF,[.503,.505,.476],.86,0),
    (SECTION,[.541,.509,.435],.88,0)]}

CORNERS = [(-9.71,9.21),(-6.05,1.63),(-4.13,-.35),(4.13,-.35),(5.25,2.41),(8.49,9.21)]
FLOORS = [4.36,7.60,10.84,14.08,17.32,20.56,23.80]
EAVE = 27.47

def ribbon(f, path, width, depth, material, name):
    f.prism(LineString(path).buffer(width/2,cap_style=2,join_style=2),depth,depth+.028,material,name)

def opening(center,width,bottom,height):
    return box(center-width/2,bottom,center+width/2,bottom+height)

def tile_courses(f,base,top,holes,lod):
    # Photos show green at window height and buff spandrels, interrupted by the vertically tiled central panel.
    width=f.length
    boundary=box(-width/2+.008,base,width/2-.008,top)
    aperture=union_all(holes) if holes else Polygon()
    face=boundary.difference(aperture)
    f.wall(base,top,holes,.22,BUFF)
    for z in FLOORS:
        band=box(-width/2,z+.16,width/2,z+2.47).intersection(face)
        if band.area>.001:f.prism(band,.004,.032,MINT,'green sash-height bands')
    # Two thin perpendicular sets of grout channels read the tile grid across tinted and yellow surfaces.
    pitch=.36 if lod else .19
    # Emit straight grout strips split at actual apertures. Preserve the shallow relief
    # while keeping the source editable and avoiding a polygon with thousands of holes.
    def spans(start,end,forbidden):
        cursor=start
        for a,b in sorted(forbidden):
            if a>cursor:yield cursor,min(a,end)
            cursor=max(cursor,b)
        if cursor<end:yield cursor,end

    edges=[h.bounds for h in holes]
    for i in range(1,int(width/pitch)+1):
        x=-width/2+i*pitch
        gaps=[(b-.012,t+.012)for l,b,r,t in edges if l-.008<x<r+.008]
        for low,high in spans(base,top,gaps):
            if high-low>.02:
                f.box(x,(low+high)/2,.013,high-low,.006,.037,JOINT,'vertical glazed tile joints')
    for i in range(1,int((top-base)/(pitch*.79))+1):
        z=base+i*pitch*.79
        gaps=[(l-.012,r+.012)for l,b,r,t in edges if b-.01<z<t+.01]
        for left,right in spans(-width/2+.008,width/2-.008,gaps):
            if right-left>.02:
                f.box((left+right)/2,z,right-left,.010,.005,.042,JOINT,'horizontal glazed tile joints')

def steel_window(f,shape,label,columns=3,rows=3):
    f.window(shape,columns,rows,frame=FRAME,glass=GLASS,trim=False,label=label)
    l,b,r,t=shape.bounds
    f.box((l+r)/2,b-.032,r-l+.11,.085,.21,.061,STONE,'window drip sill')

def central_crown(f,lod):
    panel=Polygon([(-1.04,3.487),(1.04,3.487),(1.04,27.6),(.92,28.05),(.46,30.84),
                   (.31,31.06),(-.31,31.06),(-.46,30.84),(-.92,28.05),(-1.04,27.60)])
    f.prism(panel,.055,.19,SAND,'long vertical street pier')
    for sign in (-1,1):
        path=[(sign*.962,4.48),(sign*.962,27.54),(sign*.794,28.16),(sign*.347,30.64)]
        ribbon(f,path,.094,.185,BUFF,'raked crown outer moulding')
        ribbon(f,[(sign*.74,21.76),(sign*.74,27.4),(sign*.31,30.15)],.087,.235,RELIEF,'inner crown ribs')
        f.prism(box(sign*.79-.042,4.36,sign*.79+.042,20.85),.19,.235,BUFF,'narrow bands beside pier')
    face=Polygon([(-.653,21.47),(.653,21.47),(.653,27.54),(.29,30.13),(-.29,30.13),(-.653,27.54)])
    f.prism(face,.208,.27,RELIEF,'raised ornament panel')
    # The upper panel has a diagonal fold, a band of vertical reeds and a
    # broad arch above the lowest shelf in both independent street views.
    for points in [[(-.52,25.43),(-.37,26.50),(.51,27.60)],
                   [(-.43,26.34),(-.18,27.16),(.49,27.93)],
                   [(-.41,27.07),(-.19,27.71),(.41,28.46)],
                   [(-.34,28.53),(.30,29.25)]]:
        ribbon(f,points,.092,.293,SAND,'diagonally folded crown relief')
    for u in (-.50,-.34,-.17,0,.17,.34,.50):
        ribbon(f,[(u,23.55),(u,25.51)],.052,.286,BUFF,'vertical reeds in cartouche')
    for step in (0,.18):
        arch=[(.57*cos(i*pi/18),21.99+step+.62*sin(i*pi/18)) for i in range(19)]
        ribbon(f,arch,.072,.298,BUFF,'arched relief above crown bracket')
    for i in range(3):
        f.box(0,20.75+i*.23,1.09+i*.28,.20,.28+i*.10,.23+i*.02,RELIEF,'three projecting supporting ledges')
    for i in range(5):
        x=(i-2)*.302
        f.prism(Polygon([(x-.137,21.29),(x+.137,21.29),(x+.087,21.10),
                         (x,20.976),(x-.087,21.10)]),.425,.585,BUFF,'faceted crown corbels')
    f.box(0,31.12,.35,.13,.21,.14,STONE,'crest cap')
    f.builder.tube([tuple(f.point(0,31.13,.14)),tuple(f.point(0,33.47,.14))],.031,BRONZE,6 if lod else 10,'roof/thin mast')

def entrance(f):
    left,right=-2.30,2.30
    # Sheltered opening with straight, splayed masonry flanks. The lintel carries a fan of oblique ridges.
    for side in (-1,1):
        u=side*2.22
        f.box(u,1.69,.16,3.37,.45,.135,STONE,'light doorway jambs')
        f.box(side*2.048,1.43,.17,2.81,.32,.05,SAND,'inner tiled jamb')
    f.box(0,3.40,4.59,.162,.48,.17,STONE,'outer lintel')
    half=2.13
    spring=2.05
    rise=.54
    def intrados(x):
        return spring+rise*sqrt(max(0,1-(x/half)**2))
    curve=[(-half+2*half*i/40,intrados(-half+2*half*i/40)) for i in range(41)]
    f.prism(Polygon([*curve,(half,3.31),(-half,3.31)]),-.30,.075,SAND,'shallow arch in tiled doorway head')
    ribbon(f,curve,.055,.082,RELIEF,'slender arch moulding')
    for side in (-1,1):
        for i in range(6):
            x=.14+i*.289
            ribbon(f,[(side*x,2.67+i*.018),(side*(x+.36),2.95+i*.032)],.044,.080,RELIEF,'fan carving over entrance')
    rear=Facade(f.builder,(-2.06,.46),(2.06,.46),'entrance/dark metal doors')
    # Opaque pressed-metal waist panels separate groups of slender vertical
    # bars. The segmental fanlight and three horizontals are visible above them.
    rear.prism(box(-2.045,.07,2.045,2.65),-.37,-.34,GLASS,'dark backing behind iron gate')
    for u in (-1.52,-.51,.51,1.52):
        rear.prism(box(u-.49,.75,u+.49,1.22),-.096,-.040,BRONZE,'solid panels across gate leaves')
    for i in range(-17,18):
        u=i*.115
        for low,high in ((.12,.75),(1.22,1.77)):
            rear.box(u,(low+high)/2,.027,high-low,.057,-.041,BRONZE,'vertical gate grille')
    for z in (.103,.75,1.24,1.79,1.99,2.09):
        rear.box(0,z,4.04,.047,.076,-.018,BRONZE,'horizontal gate rails')
    for u in (-2.005,-1.006,0,1.006,2.005):
        rear.box(u,.94,.055,1.70,.08,-.015,BRONZE,'gate leaf posts')
    half_fan=1.985
    base_fan=2.11
    for i in range(1,16):
        angle=pi*i/16
        ribbon(rear,[(.27*cos(angle),base_fan+.15*sin(angle)),
                     (half_fan*cos(angle),base_fan+.42*sin(angle))],.032,-.038,BRONZE,'radial fanlight spokes')
    for width,height in ((.28,.15),(half_fan,.42)):
        curve=[(width*cos(i*pi/32),base_fan+height*sin(i*pi/32))for i in range(33)]
        ribbon(rear,curve,.038,-.026,BRONZE,'arched fanlight frame')
    f.builder.plan_prism(box(-2.19,-.72,2.19,.69),.015,.083,STONE,'entrance/low threshold')

def build_corner(b,lod):
    front=Facade(b,CORNERS[2],CORNERS[3],'corner/south street')
    openings=[opening(u,1.22,z+.27,2.12)for z in FLOORS for u in (-2.89,2.89)]
    low=[opening(u,1.06,.71,2.50)for u in (-3.08,3.08)]
    door=box(-2.15,.06,2.15,3.31)
    tile_courses(front,.06,EAVE,[*openings,*low,door],lod)
    for o in openings:steel_window(front,o,'paired street casements',2,3)
    for o in low:steel_window(front,o,'beside entrance',2,3)
    central_crown(front,lod)
    entrance(front)
    for i in (0,1,3,4):
        f=Facade(b,CORNERS[i],CORNERS[i+1],'street wing/'+('west' if i<2 else 'southeast'))
        wide=i in (0,4);width=f.length*(.77 if wide else .61)
        holes=[opening(0,width,z+.28,2.13)for z in FLOORS]
        shop=opening(0,width,.43,2.62)
        tile_courses(f,.06,EAVE,[shop,*holes],lod)
        steel_window(f,shop,'street shop',4 if wide else 2,3)
        for j,(z,o)in enumerate(zip(FLOORS,holes)):
            if not wide:
                steel_window(f,o,'canted return window',2,3)
                continue
            # Shallow box windows continue on both photographed street arms.
            for side in (-1,1):
                f.box(side*(width/2+.02),z+1.35,.12,2.27,.62,.20,BUFF,'projecting bay cheeks')
            f.box(0,z+.22,width+.27,.20,.79,.24,STONE,'projecting bay base')
            f.box(0,z+2.50,width+.27,.15,.78,.24,BUFF,'projecting bay head')
            edge=(f.point(-width/2,0,.56)[:2],f.point(width/2,0,.56)[:2])
            sash=Facade(b,*edge,'wing/projected steel window')
            steel_window(sash,o,'wing strip glazing',6 if wide else 2,3)
    outline=Polygon(CORNERS)
    b.plan_prism(outline,EAVE-.17,EAVE+.04,ROOF,'roof/limited street corner')
    for i in range(len(CORNERS)-1):
        wall=LineString([CORNERS[i],CORNERS[i+1]]).buffer(.105,cap_style=2,join_style=2)
        b.plan_prism(wall,EAVE,EAVE+.31,BUFF,'roof/street parapet')
    b.plan_prism(outline,.015,.07,STONE,'base/street corner')
    cut=Facade(b,CORNERS[-1],CORNERS[0],'retained wing junction')
    cut.wall(.05,EAVE,[],.16,SECTION)
