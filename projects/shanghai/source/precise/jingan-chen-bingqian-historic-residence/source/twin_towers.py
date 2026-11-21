"""The garden elevation of the lost residence at 80 North Shaanxi Road, from the attributed frontal photograph."""
import math
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade,opening

BRICK='ochre red brick interpreted from the written account'
STONE='pale masonry bands and arch slips'
ROOF='grey pitched roof'
DARK='recessed timber frames'
GLASS='shaded glazing behind loggia'
IRON='dark metal'
PALETTE={BRICK:{'color':[.48,.25,.19],'roughness':.92},STONE:{'color':[.69,.60,.49],'roughness':.92},ROOF:{'color':[.235,.25,.265],'roughness':.88},DARK:{'color':[.22,.20,.175],'roughness':.75},GLASS:{'color':[.26,.29,.295],'metallic':.09,'roughness':.50},IRON:{'color':[.17,.18,.17],'roughness':.64},'carved pale stone':{'color':[.69,.60,.49],'roughness':.92}}
BAY=3.22
CENTRAL_HALF=4*BAY
TOWER_RADIUS=3.34
CENTERS=(-15.94,15.94)
TOWER_Y=1.48
PORCH_BACK=1.62
SHELF=6.95
TOP=12.65
LEVELS=((.91,5.32,1.41),(7.16,4.33,.78))


def railing(face,u,span,z,lod,kind='gallery'):
    face.box(u,z+.58,span,.085,.10,-.08,IRON,kind+' top rail')
    face.box(u,z+.14,span,.055,.08,-.08,IRON,kind+' lower rail')
    n=max(4,round(span/(.32 if lod else .17)))
    for j in range(n+1):
        x=u+span*(j/n-.5)
        face.box(x,z+.36,.025,.44,.036,-.08,IRON,kind+' uprights')


def arch_bands(face,holes,lod,rise):
    for h in holes:
        x0,z0,x1,z1=h.bounds
        radius=(x1-x0)/2
        # The photographed bands follow the full arch, with vertical reveals inside the opening.
        border=h.buffer(.075,join_style=2).difference(h).intersection(box(x0-.13,z0+.08,x1+.13,z1+.13))
        face.prism(border,0,.085,STONE,'raised archivolt and reveals')
        if not lod:
            face.box((x0+x1)/2,z1+.012,.155,.20,.14,.11,STONE,'crown slip')
            for x in (x0,x1):face.box(x,z1-rise,.145,.105,.17,.08,STONE,'impost blocks')
            for index in range(1,12):
                theta=math.pi*index/12
                dx,dz=math.cos(theta),math.sin(theta);u=(x0+x1)/2
                edge=(u+radius*dx,z1-rise+rise*dz,.091)
                outer=(edge[0]+.068*dx,edge[1]+.068*dz,.091)
                face.line(edge,outer,.012,BRICK,5,'arch joint')
            for u in (x0-.038,x1+.038):
                for i in range(1,math.ceil((z1-rise-z0)/.28)):
                    z=z0+i*.28
                    face.line((u-.036,z,.089),(u+.036,z,.089),.009,BRICK,4,'jamb course')


def gallery(builder,lod):
    front=Facade(builder,(-CENTRAL_HALF,0),(CENTRAL_HALF,0),'eight-bay garden gallery')
    bays=[(n-3.5)*BAY for n in range(8)]
    for ix,(sill,h,rise) in enumerate(LEVELS):
        width=2.77 if ix==0 else 2.88
        holes=[opening(u,sill,width,h,rise,12 if lod else 28)for u in bays]
        front.wall(.40 if ix==0 else SHELF,6.87 if ix==0 else TOP,holes,.37,BRICK)
        arch_bands(front,holes,lod,rise)
        for u in bays:
            if ix==1:railing(front,u,width-.04,sill,lod)
    back=Facade(builder,(-CENTRAL_HALF,PORCH_BACK),(CENTRAL_HALF,PORCH_BACK),'recessed gallery backing')
    glazing=[]
    for level,z in enumerate((.90,7.13)):
        h=4.08 if level==0 else 3.54
        for u in bays:glazing.append(opening(u,z,1.90,h,.0))
    back.wall(.35,TOP,glazing,.30,BRICK)
    for h in glazing:back.window(h,2,3,DARK,False,GLASS,'paired glazed shutters')
    for u in [i*BAY for i in range(-3,4)]:
        front.box(u,3.44,.33,5.05,.21,.12,BRICK,'square ground pier')
        front.box(u,.96,.49,.36,.32,.14,STONE,'ground pier plinth')
        front.box(u,8.95,.26,3.56,.18,.10,BRICK,'upper pilaster')
    for z,h,p in [(.43,.26,.32),(6.71,.13,.32),(6.89,.18,.44),(12.04,.13,.27),(12.38,.24,.42),(12.63,.15,.58)]:front.beam(z,h,p,STONE,label='continuous string course')
    for z in (.58,6.91,12.50):builder.box((0,1.06,z),(2*CENTRAL_HALF,2.68,.19),STONE,label='gallery floor and soffit')
    # A narrow continuous cap sits over the square openings of the photographed parapet.
    front.box(0,12.88,2*CENTRAL_HALF,.24,.24,.02,BRICK,'parapet lower rail')
    for i in range(34):
        x=(i-16.5)*(2*CENTRAL_HALF/34)
        front.box(x,13.15,.47,.49,.26,.025,STONE,'parapet merlons')
    front.box(0,13.42,2*CENTRAL_HALF,.105,.31,.025,STONE,'pierced parapet cap')
    # Only the front roof band and three groups of masonry rising behind it are recorded.
    for side in (-1,1):
        face=Facade(builder,(side*9.55,2.30),(side*5.05,2.30),'roof silhouettes')
        face.prism(Polygon([(-2.25,12.50),(2.25,12.50),(1.35,13.60),(.22,13.88),(-.51,14.72),(-1.22,13.67)]),-.66,.03,ROOF,'stepped roof crest')
        builder.box((side*6.57,2.85,14.17),(.64,.72,2.31),BRICK,label='chimney shaft')
        builder.box((side*6.57,2.85,15.35),(.87,.88,.17),STONE,label='chimney cap')
    ped=Facade(builder,(-3.4,2.05),(3.4,2.05),'central roof gable')
    ped.prism(Polygon([(-3.4,12.55),(3.4,12.55),(2.02,13.50),(.34,14.83),(-.10,14.96),(-1.80,13.95)]),-.38,0,BRICK,'central pediment')
    for a,b in [((-3.4,12.59,.04),(-.10,14.96,.04)),((-.10,14.96,.04),(3.4,12.59,.04))]:ped.line(a,b,.083,STONE,5 if lod else 9,'gable edge')


def ring_vertices(cx,r,z):
    return [(cx+r*math.cos(math.radians(i*45-112.5)),TOWER_Y+r*math.sin(math.radians(i*45-112.5)),z)for i in range(8)]


def tower(builder,cx,lod):
    ring=ring_vertices(cx,TOWER_RADIUS,0)
    outline=Polygon([(x,y)for x,y,z in ring])
    faces=[Facade(builder,ring[i][:2],ring[(i+1)%8][:2],('west'if cx<0 else'east')+' faceted tower')for i in range(8)]
    for face in faces:
        visible_edge=face.n[1]<-.24
        for i,(sill,h,rise)in enumerate(LEVELS):
            w=face.length*.76
            holes=[opening(0,sill,w,h,min(rise,w*.44),10 if lod else 24)]if visible_edge else []
            face.wall(.40 if i==0 else SHELF,6.87 if i==0 else TOP,holes,.27,BRICK)
            arch_bands(face,holes,lod,min(rise,w*.44))
            if visible_edge and i==1:railing(face,0,w-.05,sill,lod,'tower balcony')
        if visible_edge:
            for u in (-face.length*.44,face.length*.44):
                face.box(u,3.45,.16,4.98,.13,.04,STONE,'tower pier facing')
    for z,h,e,mat in [(0,.50,.04,BRICK),(.51,.17,.19,STONE),(6.79,.22,.18,STONE),(12.10,.16,.13,STONE),(12.44,.30,.25,STONE),(12.61,.76,.02,BRICK),(13.37,.18,.17,STONE),(13.55,1.29,-.10,BRICK),(14.84,.16,.13,STONE)]:
        builder.plan_prism(outline.buffer(e,join_style=2),z,z+h,mat,'octagonal tower base, string courses and attic')
    for f in faces:
        if f.n[1]<-.24:
            f.box(0,14.11,f.length*.64,.73,.04,-.04,DARK,'attic panel')
    for z in (.61,6.87):builder.plan_prism(outline,z-.07,z+.07,STONE,'visible tower gallery floor')
    rings=[ring_vertices(cx,r,z)for r,z in [(3.56,15.04),(3.48,15.25),(2.89,16.11),(1.66,19.23),(1.48,19.70)]]
    for j in range(len(rings)-1):
        lo,hi=rings[j:j+2]
        for i in range(8):
            k=(i+1)%8
            builder.add([lo[i],lo[k],hi[k],hi[i]],[(0,1,2),(0,2,3)],ROOF,'eight sloping tower facets')
            if not lod:builder.tube([lo[i],hi[i]],.026,IRON,6,'roof hip joints')
    cap=Polygon([(x,y)for x,y,z in rings[-1]]);builder.plan_prism(cap,19.69,19.79,ROOF,'tower roof cap')
    for i in range(8):
        a,b=rings[-1][i],rings[-1][(i+1)%8]
        builder.tube([(a[0],a[1],19.76),(a[0],a[1],20.15)],.027,IRON,4 if lod else 7,'roof crest uprights')
        builder.tube([(a[0],a[1],20.04),(b[0],b[1],20.04)],.019,IRON,4 if lod else 6,'roof crest rail')


def facade(builder,lod):
    gallery(builder,lod)
    for cx in CENTERS:tower(builder,cx,lod)
    # The photograph only resolves the central projecting low crest above garden planting.
    # The concealed entrance, step count, interior and plan have no attributed source.
    low=Facade(builder,(-4.12,-1.03),(4.12,-1.03),'central garden parapet')
    profile=Polygon([(-4.12,0),(-4.12,.62),(-3.36,.77),(-2.40,1.60),(-1.15,1.70),(-.98,1.90),(.98,1.90),(1.15,1.70),(2.40,1.60),(3.36,.77),(4.12,.62),(4.12,0)])
    low.prism(profile,-.34,0,BRICK,'front parapet visible over greenery')
    top=list(profile.exterior.coords)[1:12]
    for a,b in zip(top,top[1:]):low.line((a[0],a[1],.05),(b[0],b[1],.05),.075,STONE,5 if lod else 9,'parapet coping')
