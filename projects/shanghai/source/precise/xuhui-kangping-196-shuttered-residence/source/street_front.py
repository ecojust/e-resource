"""The five openings in the signed 2019 street view, the adjoining horizontal sash and classical cornice."""
from math import pi,sin,cos
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from materials import BASE,DEEP,EAVE,PALE,PAVE,RIDGE,ROOF,SHADE,TRIM,WALL
from photo_plane import hit
from shuttered_windows import add_shutters,add_small,apertures
from scroll_panels import add_scroll_panel,add_scroll_panels,measured_layout

# The two sectional cuts retain the identifiable front and its nearest flanking window bays.
LEFT=-11.20
RIGHT=8.12
DEPTH=1.34
def slab(f,plan,z0,z1,mat,label):
    f.b.prism(plan,z0,z1,lambda u,d,z:f.point(u,d,z),mat,f.label+' | '+label)

def piers(f,lo,hi,base,head,name):
    f.rect(lo,hi,base,head,-.015,.084,WALL,name+' | shaft')
    plinth=hit(207,484)[1]
    f.rect(lo-.009,hi+.009,base,plinth,.085,.109,BASE,name+' | coursed pier base')
    f.rect(lo-.015,hi+.015,plinth-.015,plinth+.035,.081,.12,SHADE,name+' | plinth cap')
    for low,high,edge,mat in [(head-.09,head+.01,.034,TRIM),(head+.01,head+.065,.057,SHADE),
                              (head+.065,head+.136,.077,PALE),(head+.136,head+.197,.098,TRIM)]:
        f.rect(lo-edge,hi+edge,low,high,-.008,.099+edge,mat,name+' | stepped capital')

def dentilled_course(f,start,end,z,lod,label):
    for low,high,relief,mat in [(z,z+.057,.068,TRIM),(z+.145,z+.194,.105,PALE),
                                 (z+.194,z+.248,.16,TRIM),(z+.248,z+.313,.188,PALE)]:
        f.rect(start,end,low,high,.002,relief,mat,label+' | cornice course')
    pitch=.286
    u=start+pitch*.50
    while u+.077 < end:
        shape=Polygon([(u-.074,z+.148),(u+.074,z+.148),(u+.062,z+.099),(u+.032,z+.077),
                       (u-.028,z+.077),(u-.063,z+.101)])
        f.solid(shape,.009,.098,PALE,label+' | pendant dentil')
        u+=pitch

def add_portal_cornice(f,left,right,shoulder):
    # Across the actual 2019 lintel, the top white lip spans v303.6–307.9.
    # The lower bed lies at v321.3, above the long plaque's incised upper fillet.
    def level(v,projection):
        return hit(525,v,-projection)[1]

    levels=[(321.3,.10),(319.7,.12),(317.9,.136),(316.4,.15),
            (314.7,.175),(311.0,.175),(307.9,.215),(303.6,.215)]
    courses=[(.105,TRIM),(.125,PALE),(.142,SHADE),(.159,PALE),
             (.178,TRIM),(.152,SHADE),(.215,PALE)]
    elevations=[level(v,p) for v,p in levels]
    f.rect(left-.57,right+.57,shoulder-.08,elevations[0],-.20,-.002,
           WALL,'portal | high plaster backing')
    for (projection,mat),z0,z1 in zip(courses,elevations,elevations[1:]):
        # Two terminal blocks stand slightly proud of the central cap over the windowed leaves.
        a,b=left-.59,right+.59
        j,k=left+.15,right-.17
        end=projection+.039
        plan=Polygon([(a,-end),(j,-end),(j,-projection),(k,-projection),
                      (k,-end),(b,-end),(b,.19),(a,.19)])
        slab(f,plan,z0,z1,mat,'portal | stepped square-return cornice')
    # Bright fronts and the sloping lower faces of the hanging teeth are visible separately.
    # The last narrow tip retreats to the wall, leaving the plaque's upper rim in front of it.
    for i in range(-5,6):
        u=hit(528.4+14.35*i,323.,-.10)[0]
        if not left-.45 < u < right+.45:
            continue
        rings=[(level(325.9,.025),.033,.025),
               (level(324.55,.042),.052,.042),
               (level(323.35,.109),.075,.109),
               (elevations[0]+.004,.080,.109)]
        vertices=[]
        for z,half,projection in rings:
            vertices.extend(f.point(u+dx,depth,z) for dx,depth in
                            [(-half,-projection),(half,-projection),(half,-.002),(-half,-.002)])
        faces=[(3,2,1,0),(12,13,14,15)]
        for ring in range(len(rings)-1):
            for edge in range(4):
                a=4*ring+edge
                b=4*ring+(edge+1)%4
                faces.append((a,b,b+4,a+4))
        f.b.add(vertices,faces,PALE,f.label+' | portal | tapered pendant dentil '+str(i+6))


def tile_cap(f,start,end,z,lod):
    # The visible low red tiles rise gently behind the front cornice.
    slope=.20;dash=.20
    s=0
    while start+s*dash < end:
        a=start+s*dash;b=min(a+dash,end);w=b-a
        n=4 if lod else 8
        section=[(a+w*i/n,z+.038*sin(pi*i/n))for i in range(n+1)]
        shell=Polygon([*section,*[(u,h-.035)for u,h in section[::-1]]])
        f.b.prism(shell,-DEPTH,0,lambda u,h,p:f.point(u,-p,h+(-p)*slope),RIDGE if s%7==0 else ROOF,f.label+' | front pitch | clay pan tiles')
        s+=1

def add_street_front(f,lod=False):
    orig=apertures()
    # The right-hand short sash is visible beyond the crop in the additional 2020 street view.
    small=orig['small-right'];low=small.bounds[1];high=small.bounds[3]
    right_small=box(5.54-.77,low,5.54+.77,high)
    holes=unary_union([*orig.values(),right_small])
    shoulder=hit(204,348)[1];top=shoulder+.34
    front=box(LEFT,0,RIGHT,top)
    f.solid(front.difference(holes),-.26,0,WALL,'street wall | apertures through continuous rendered wall')
    f.solid(box(LEFT,.001,RIGHT,hit(207,484)[1]).difference(holes),.001,.032,BASE,'street wall | slate grey plinth')
    add_shutters(f,lod)
    add_small(f,right_small,'right return sash')
    add_scroll_panels(f,lod)
    nearby=next(v for v in measured_layout() if v['id']=='horizontal-2')
    right_panel=dict(nearby,id='horizontal-right-2020',x=right_small.centroid.x,
                     z=right_small.bounds[1]+nearby['z']-orig['small-right'].bounds[1])
    add_scroll_panel(f,right_panel,lod)
    left_edge=orig['door'].bounds[0];right_edge=orig['door'].bounds[2]
    pier_w=.43
    for x,name in [(left_edge-.23,'left portal pier'),(right_edge+.23,'right portal pier')]:
        piers(f,x-pier_w/2,x+pier_w/2,.02,top+.09,name)
    for x in [hit(130,485)[0],hit(307,482)[0]]:
        piers(f,x-.19,x+.19,.04,top-.10,'short facade pier')
    dentilled_course(f,LEFT,left_edge-.52,shoulder,lod,'left shuttered wing')
    dentilled_course(f,right_edge+.52,RIGHT,shoulder,lod,'right shuttered wing')
    add_portal_cornice(f,left_edge,right_edge,shoulder)
    tile_cap(f,LEFT,left_edge-.57,top+.022,lod)
    tile_cap(f,right_edge+.57,RIGHT,top+.022,lod)
    for x,along in [(LEFT,-1),(RIGHT,1)]:
        side=f.face(x,DEPTH if along<0 else 0,0,along)
        side.rect(0,DEPTH,0,top,-.235,0,WALL,'street section | return')
        side.rect(0,DEPTH,0,.60,.001,.028,BASE,'street section | plinth return')
    rear=f.face(RIGHT,DEPTH,-1,0);rear.rect(0,RIGHT-LEFT,0,top,-.17,0,WALL,'street wing | inner sectional limit')
    slab(f,box(LEFT,0,RIGHT,DEPTH),.007,.031,BASE,'street section | base')
    for i,(depth,z) in enumerate([(.58,.14),(.39,.27),(.19,orig['door'].bounds[1])]):
        f.rect(left_edge-.075,right_edge+.075,.008,z,.005,depth,PAVE,'entrance | visible stone tread '+str(i+1))
