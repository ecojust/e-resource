"""The restored three-bay garden portico and red-brick residence in Lane 185."""
from math import ceil,floor
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from photo_architecture import Facade
from roof import make_roof,plane,TILES,UNDER,EDGE,BRICK,CAP

JOINT='warm weathered brick joints';LIGHT='light red face brick';DEEP='burnt sienna face brick'
STONE='pale washed stone';PORCH='buff exposed aggregate';GLASS='smoked window glass'
FRAME='black steel casement';WOOD='dark porch joinery';SLAB='grey stone paving';PAVE='terrace quarry tile'
PALETTE={k:{'color':v,'roughness':r}for k,v,r in (
    (BRICK,[.463,.228,.156],.87),(LIGHT,[.493,.255,.18],.87),(DEEP,[.413,.201,.139],.9),
    (JOINT,[.54,.398,.315],.86),(STONE,[.686,.633,.535],.84),(PORCH,[.64,.492,.37],.88),
    (GLASS,[.170,.208,.208],.26),(FRAME,[.094,.098,.091],.63),(WOOD,[.141,.11,.088],.72),
    (SLAB,[.568,.561,.509],.88),(PAVE,[.476,.258,.171],.84),
    (TILES[0],[.482,.257,.174],.89),(TILES[1],[.456,.238,.164],.88),(TILES[2],[.51,.281,.189],.87),
    (UNDER,[.221,.203,.178],.92),(EDGE,[.219,.219,.207],.79),(CAP,[.285,.228,.180],.84))}

def facade(b,x0,x1,y,name):
    return Facade(b,(x0,y),(x1,y),name)

def stretcher_face(f,surface,lod):
    # Only the observed garden faces receive individual stretcher outlines.
    # The clipped mesh follows every doorway, glazed opening, and gable rake.
    unit=.26 if not lod else .51;course=.106 if not lod else .207
    xmin,zmin,xmax,zmax=surface.bounds;vs=[[],[],[]];fs=[[],[],[]]
    for j in range(floor(zmin/course),ceil(zmax/course)):
        dz=j*course;stagger=unit*(j%2)*.5
        for i in range(floor((xmin-stagger)/unit),ceil((xmax-stagger)/unit)):
            u=i*unit+stagger
            tile=box(u+.005,dz+.005,u+unit-.005,dz+course-.005)
            if not surface.intersects(tile):continue
            tone=(i*17+j*23+(i*j)%13)%17;k=0 if tone<11 else (1 if tone<15 else 2)
            if surface.covers(tile):polygons=[list(tile.exterior.coords)[:-1]]
            else:
                piece=surface.intersection(tile)
                if piece.area<.00004:continue
                polygons=[list(q.exterior.coords)[:-1]for q in constrained_delaunay_triangles(piece).geoms if q.area>.00001]
            for poly in polygons:
                offset=len(vs[k]);vs[k].extend(f.point(x,z,.008)for x,z in poly)
                fs[k].append(tuple(offset+i for i in range(len(poly))))
    for k,m in enumerate([BRICK,LIGHT,DEEP]):
        if vs[k]:f.builder.add(vs[k],fs[k],m,f.label+'/running bond')

def window(f,u,z,w,h,cols=3,rows=3,hood=True,door=False):
    hole=box(u-w/2,z,u+w/2,z+h);f.box(u,z+h/2,w,h,.06,-.174,GLASS,'recessed glazing')
    for j in range(cols+1):
        f.box(u-w/2+j*w/cols,z+h/2,.049 if j in (0,cols)else .034,h,.075,-.123,FRAME,'steel verticals')
    for j in range(rows+1):
        f.box(u,z+j*h/rows,w,.045 if j in (0,rows)else .032,.077,-.122,FRAME,'steel horizontals')
    if hood:
        f.box(u,z-.012,w+.18,.095,.163,.007,STONE,'stone sill')
        for sign in (-1,1):f.box(u+sign*(w/2+.045),z+h/2,.095,h+.09,.114,.004,STONE,'cut stone window jamb')
        profile=[(u-w/2-.13,z+h-.08),(u-w/2-.13,z+h+.10),(u-.20*w,z+h+.12),(u,z+h+.16),
                 (u+.20*w,z+h+.12),(u+w/2+.13,z+h+.10),(u+w/2+.13,z+h-.08),(u+w/2+.035,z+h-.08),
                 (u+w/2+.035,z+h+.01),(u-w/2-.035,z+h+.01),(u-w/2-.035,z+h-.08)]
        f.prism(Polygon(profile),.006,.119,STONE,'shallow Tudor drip mould')
    if door:f.box(u,z+.73,w-.10,1.38,.072,-.108,WOOD,'lower entrance joinery')
    return hole

def wall(f,lower,upper,windows,lod,outline=None):
    holes=[window(f,*args)for args in windows]
    surface=f.wall(lower,upper,holes,material=JOINT,thickness=.21,outline=outline)
    stretcher_face(f,surface,lod)

def closed_sides(b,x0,x1,y0,y1,z,name):
    for a,c in [((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
        Facade(b,a,c,name).wall(0,z,material=BRICK,thickness=.18)
    b.plan_prism(box(x0,y0,x1,y1),0,.09,SLAB,name+'/ground floor')

def opening(u,width,spring,peak):
    half=width/2
    return Polygon([(u-half,0),(u+half,0),(u+half,spring),
       (u+half-.10,spring+.17),(u+half-.27,spring+.27),(u+.27*width,peak-.07),
       (u,peak),(u-.27*width,peak-.07),(u-half+.27,spring+.27),(u-half+.10,spring+.17),(u-half,spring)])

def panel(f,u,z,w,h,lod):
    # Two curved branches cross in the middle. The negative shapes in the
    # original ornamental panels are true holes through front and back skins.
    def curve(points,width):return LineString([(u+x*w,z+y*h)for x,y in points]).buffer(width*h,cap_style='round',join_style='round',quad_segs=3 if lod else 6)
    field=box(u-w/2,z,u+w/2,z+h);border=field.difference(box(u-w/2+.058,z+.05,u+w/2-.058,z+h-.04))
    paths=[ [(-.47,.11),(-.40,.20),(-.32,.33),(-.19,.42),(-.03,.50),(.10,.56),(.25,.64),(.39,.79),(.45,.92)],
            [(-.45,.92),(-.39,.79),(-.25,.64),(-.10,.56),(.03,.50),(.19,.42),(.32,.33),(.40,.20),(.47,.11)] ]
    pieces=[border]+[curve(points,.063)for points in paths]
    for s in (-1,1):
        pieces+=[curve([(s*.43,.90),(s*.30,.85),(s*.20,.91),(s*.17,.98)],.049),
                 curve([(s*.411,.12),(s*.29,.15),(s*.19,.09),(s*.17,.02)],.048)]
    fret=unary_union(pieces).intersection(field)
    f.prism(fret,-.126,.06,PORCH,'pierced crossed foliate panel')

def portico(b,lod):
    x0=-5.10;x1=5.10;back=4.48;width=x1-x0;z=3.47;front=facade(b,x0,x1,0,'garden portico')
    holes=[opening(i*3.30,3.00,2.59,3.11)for i in (-1,0,1)]
    front.wall(0,z,holes,material=PORCH,thickness=.32)
    for a,c in [((x1,0),(x1,back)),((x0,back),(x0,0))]:
        f=Facade(b,a,c,'portico open ends');f.wall(0,z,[opening(0,back-.65,2.61,3.13)],material=PORCH,thickness=.27)
    b.plan_prism(box(x0+.05,.15,x1-.05,back+.06),.015,.09,SLAB,'open portico stone pavement')
    b.plan_prism(box(x0-.065,-.096,x1+.065,back+.12),z-.107,z+.104,STONE,'portico lintel and terrace plate')
    b.plan_prism(box(x0+.01,.04,x1-.01,back+.1),z+.104,z+.13,PAVE,'terracotta terrace finish')
    # The garden photograph shows three groups of three pierced panels.
    for k in (-1,0,1):
        center=3.3*k
        for j in (-1,0,1):panel(front,center+j*.93,z+.17,.915,.66,lod)
    for x in [-4.98,-1.65,1.65,4.98]:front.box(x,z+.49,.34,.76,.25,-.035,PORCH,'solid parapet piers')
    front.box(0,z+.163,10.23,.12,.34,.004,STONE,'balustrade base rail')
    front.box(0,z+.89,10.28,.123,.34,.012,STONE,'continuous terrace coping')
    for side in (-1,1):
        a=(x1,0)if side>0 else(x0,back);c=(x1,back)if side>0 else(x0,0)
        f=Facade(b,a,c,'terrace return')
        for i in range(4):panel(f,-1.62+i*1.08,z+.17,1.03,.66,lod)
        for y in (-2.11,2.11):f.box(y,z+.49,.26,.76,.25,-.02,PORCH,'terminal posts')
        f.box(0,z+.89,back,.123,.32,.002,STONE,'return coping')
    # Repaired door leaves are recessed behind the three clear outdoor bays.
    backwall=facade(b,x0,x1,back,'recessed porch entrances')
    wall(backwall,0,3.48,[(x,.12,1.10,2.48,2,4,False,True)for x in (-3.21,-.20,3.09)],lod)

def build_residence(b,lod):
    portico(b,lod)
    # East garden wing in the fourth-survey photograph: 1, 2 narrow, 1 broad,
    # 1 separate bay on each of the two levels.
    e=facade(b,5.10,16.25,4.78,'garden east wing')
    starts=[(6.24,1.1),(7.61,.58),(8.71,.58),(11.18,1.68),(14.64,1.33)]
    wins=[(cx-10.675,z,w,h,2 if w<.8 else 3,4,(cx==6.24),False)for z,h in [(.68,1.63),(4.23,1.56)]for cx,w in starts]
    wall(e,0,6.77,wins,lod)
    g=facade(b,-5.43,1.58,4.12,'projecting garden gable');half=g.length/2
    outline=Polygon([(-half,3.46),(half,3.46),(half,6.74),(0,10.47),(-half,6.74)])
    win=[(-2.23,3.85,1.0,1.67,2,4,True,False),(-.02,3.85,1.12,1.67,2,4,True,False),(2.18,3.85,1.00,1.67,2,4,True,False),
         (-.43,7.51,.74,1.22,2,3,True,False),(.43,7.51,.74,1.22,2,3,True,False)]
    wall(g,3.46,10.47,win,lod,outline)
    central=facade(b,1.58,5.10,4.62,'terrace glazed bays')
    wall(central,3.47,6.76,[(0,3.74,3.05,2.03,5,3,False,False)],lod)
    annex=facade(b,-10.01,-5.41,-.37,'one-storey west wing')
    wall(annex,0,3.14,[(.03,.67,1.71,1.77,3,4,True,False)],lod)
    closed_sides(b,-10.01,-5.41,-.37,5.74,3.14,'west wing returns')
    for x in (-10.01,-5.41):
        side=Facade(b,(x,-.37),(x,5.74),'west wing side gables')
        side.prism(Polygon([(-3.055,3.12),(3.055,3.12),(-.155,5.23)]),-.13,0,BRICK,'wall below roof returns')
    closed_sides(b,-5.75,16.25,4.78,13.5,6.77,'main rear and ends')
    for x0,x1,y0,y1,top in [(-5.43,1.58,4.12,5.03,6.65)]:
        for x in (x0,x1):Facade(b,(x,y0),(x,y1),'gable return').wall(3.46,top,material=BRICK,thickness=.13)
    for x in [-5.73,16.25]:
        side=Facade(b,(x,4.78),(x,13.5),'plain gable end')
        side.prism(Polygon([(-4.36,6.75),(4.36,6.75),(.32,10.52)]),-.13,0,BRICK,'brick beneath eaves')
    make_roof(b,lod)
    # A single broad shed dormer projects through the main south slope.
    df=facade(b,1.64,4.20,5.76,'south shed dormer')
    wall(df,7.27,9.15,[(0,7.95,2.13,1.02,5,3,False,False)],lod)
    for x in (1.64,4.20):
        Facade(b,(x,5.76),(x,8.82),'dormer cheeks').wall(7.32,9.12,material=BRICK,thickness=.11)
    plane(b,[(1.40,5.51,9.20),(4.45,5.51,9.20),(4.45,8.88,9.72),(1.40,8.88,9.72)],lod,'shed dormer tiled roof')
