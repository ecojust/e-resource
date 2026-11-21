"""Garden elevation of Willow Court, 34 West Fuxing Road. Dimensions are in metres."""
from math import cos, sin, pi
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

PLASTER='pale yellow mineral render'
RED='muted red oxide balcony'
STONE='grey artificial stone steps'
GLASS='grey blue glass'
FRAME='brown steel window'
NOSING='weathered step riser'
ROOF='weathered flat roof'
DOOR='glazed dark garden door'
PALETTE={name:{'color':colour,'roughness':roughness} for name,colour,roughness in (
    (PLASTER,[.79,.71,.52],.92),(RED,[.42,.18,.13],.86),
    (STONE,[.55,.52,.46],.87),(GLASS,[.23,.31,.31],.36),
    (FRAME,[.24,.20,.17],.67),(NOSING,[.42,.39,.35],.89),
    (ROOF,[.32,.32,.28],.88),(DOOR,[.21,.19,.16],.55))}
FRONT=-7.10
BACK=7.13
END=12.18
CORE=7.82
RAISED=1.40
STOREY=3.08
LEVELS=[RAISED+STOREY*i for i in range(1,12)]
HIGH=RAISED+12*STOREY
LOW=HIGH-STOREY


def slab(builder,poly,base,height,mat,label):
    builder.plan_prism(poly,base,base+height,mat,label)


def joined_wall(face,bottom,top,holes,thickness,turns=(True,True)):
    """Mitre the inner skins where two exterior faces return around a corner."""
    first=len(face.builder.parts)
    face.wall(bottom,top,holes,thickness=thickness,material=PLASTER)
    for part in face.builder.parts[first:]:
        result=[]
        for vertex in part['vertices']:
            offset=vertex-face.center
            u,depth=offset@face.t,offset@face.n
            if turns[0] and abs(u+face.length/2)<1e-7:
                vertex=vertex-depth*face.t
            elif turns[1] and abs(u-face.length/2)<1e-7:
                vertex=vertex+depth*face.t
            result.append(tuple(vertex))
        part['vertices']=result


def glazing(face,u,z,w,h,lod,columns=3,material=GLASS):
    aperture=opening(u,z,w,h,0)
    face.window(aperture,columns=columns if not lod else min(2,columns),
                rows=3 if not lod else 1,frame=FRAME,glass=material,trim=False)
    assert face.builder.parts[-1]['label'].endswith('window-sill')
    face.builder.parts.pop()
    face.box(u,z-.045,w+.09,.09,.15,.014,STONE,'window sill')
    return aperture


def half_round(radius,wall_y,n):
    coords=[(radius*cos(i*pi/n),wall_y-radius*sin(i*pi/n)) for i in range(n+1)]
    return Polygon([*coords,(-radius,wall_y+.13),(radius,wall_y+.13)])


def balcony(builder,z,lod):
    n=16 if lod else 38
    outer=half_round(1.78,FRONT,n)
    slab(builder,outer,z-.15,.18,RED,'garden balcony slab')
    # A curved solid breast wall, open to the sky and to the apartment.
    ring=outer.difference(half_round(1.62,FRONT,n)).intersection(box(-2,FRONT-2,2,FRONT+.015))
    slab(builder,ring,z+.015,.73,RED,'curved solid balcony')
    slab(builder,ring.buffer(.023,join_style='mitre'),z+.745,.075,RED,'balcony rim')


def oriel(builder,center,lod):
    depth=.73;half=2.06;flat=1.44
    coords=[(center-half,FRONT),(center-flat,FRONT-depth),(center+flat,FRONT-depth),(center+half,FRONT)]
    section=Polygon([*coords,(center+half,FRONT+.15),(center-half,FRONT+.15)])
    slab(builder,section,1.16,.70,PLASTER,'sloping plinth to ground bay')
    for start,end in zip(coords,coords[1:]):
        face=Facade(builder,start,end,'ground splayed oriel')
        hole=glazing(face,0,1.95,face.length-.17,1.62,lod,3 if face.length>1 else 1)
        face.wall(1.82,3.85,[hole],thickness=.17,material=PLASTER)
    slab(builder,section,3.82,.16,RED,'oriel weathering line')
    # The two side hips and front slope meet the window head, as in the entrance photo.
    for start,end in zip(coords,coords[1:]):
        v=[(*start,3.95),(*end,3.95),(center+(end[0]-center)*.84,FRONT+.05,4.27),
           (center+(start[0]-center)*.84,FRONT+.05,4.27)]
        builder.add(v,[(0,1,2),(0,2,3)],RED,'splayed window sloping hood')


def main_front(builder,lod):
    front=Facade(builder,(-CORE,FRONT),(CORE,FRONT),'south garden face')
    holes=[glazing(front,0,RAISED,2.14,2.63,lod,2,DOOR)]
    for side in (-1,1):
        c=side*4.91
        holes.append(box(c-2.03,1.32,c+2.03,3.88))
        oriel(builder,c,lod)
        for offset in (-.62,.62):
            holes.append(glazing(front,c+offset,.43,.97,.47,lod,1))
        front.box(side*2.02,HIGH/2+.67,.20,HIGH+.06,.27,.085,RED,'narrow vertical red strip')
        front.box(side*1.71,HIGH/2+.97,.24,HIGH+.87,.35,.14,RED,'stepped crown rib')
    for z in LEVELS:
        balcony(builder,z,lod)
        holes.append(glazing(front,0,z+.10,1.29,2.00,lod,2,DOOR))
        for side in (-1,1):
            holes.append(glazing(front,side*4.91,z+.64,3.03,1.53,lod,4))
    joined_wall(front,.04,HIGH+.50,holes,.28)
    front.box(0,HIGH+.754,3.08,.512,.40,.05,RED,'centre crown step')
    front.box(0,HIGH+1.35,.95,.68,.36,.07,RED,'central narrow crown')
    # The current doorway has a lowered red curved hood with a pale soffit.
    slab(builder,half_round(1.32,FRONT,18 if lod else 38),3.81,.50,RED,'round head above raised door')
    slab(builder,half_round(1.25,FRONT,18 if lod else 38),3.78,.035,PLASTER,'pale underside of entrance hood')
    for i in range(7):
        radius=2.60-i*.205
        base=.025+i*.185
        slab(builder,half_round(radius-.025,FRONT,18 if lod else 42),base,.15,NOSING,'slightly weathered front riser')
        slab(builder,half_round(radius,FRONT,18 if lod else 42),base+.145,.05,STONE,'exposed semicircular tread')
    slab(builder,half_round(1.13,FRONT,18 if lod else 38),1.24,.18,STONE,'raised door landing')


def side_loggia(builder,side,lod):
    lo,hi=sorted((side*END,side*CORE));w=hi-lo;c=(lo+hi)/2
    if side<0:
        # The western wing has a deep recess closed by this wall at ground level.
        back=Facade(builder,(lo,FRONT+3.60),(hi,FRONT+3.60),'west ground recess')
        back.wall(.04,LEVELS[0],[],thickness=.22,material=PLASTER)
    slab(builder,box(lo+.065,FRONT+.06,hi-.065,BACK-.06),LEVELS[0]-.19,.20,PLASTER,'soffit above ground passage')
    for z in LEVELS[:-1]:
        face=Facade(builder,(lo,FRONT+1.38),(hi,FRONT+1.38),'loggia inner face')
        holes=[glazing(face,0,z+.22,1.98,2.02,lod,3)]
        face.wall(z,z+STOREY,holes,thickness=.22,material=PLASTER)
        slab(builder,box(lo+.065,FRONT+.07,hi-.065,FRONT+1.63),z-.17,.20,PLASTER,'recessed outer balcony floor')
        builder.box((c,FRONT+.085,z+.41),(w,.18,.81),PLASTER,label='side balcony front')
        for x in (lo+.10,hi-.10):
            builder.box((x,FRONT+.65,z+STOREY/2),(.21,1.34,STOREY),PLASTER,label='loggia side wall')
    slab(builder,box(lo+.07,FRONT+.08,hi-.07,BACK-.08),LOW-.18,.22,ROOF,'outer terrace roof')
    for x in (lo+.10,hi-.10):
        builder.box((x,FRONT+.13,LOW+.38),(.28,.40,.82),PLASTER,label='terrace end post')


def rear_and_ends(builder,lod):
    back=Facade(builder,(CORE,BACK),(-CORE,BACK),'north stair facade')
    holes=[]
    for z in [RAISED,*LEVELS]:
        for u in (-5.5,-2.6,.2,3.1,5.8):
            holes.append(glazing(back,u,z+.81,1.18,1.44,lod,2))
    joined_wall(back,.04,HIGH+.30,holes,.25)
    for side in (-1,1):
        lo,hi=sorted((side*END,side*CORE))
        flank=Facade(builder,(hi,BACK),(lo,BACK),'rear outer wing')
        holes=[]
        start=LEVELS[0] if side>0 else .03
        for z in LEVELS[:-1]:
            holes.append(glazing(flank,0,z+.75,1.85,1.52,lod,3))
        joined_wall(flank,start,LOW+.31,holes,.23,(side>0,side<0))
        x=side*END
        edges=((x,FRONT),(x,BACK)) if side>0 else ((x,BACK),(x,FRONT))
        end=Facade(builder,*edges,'side elevation')
        holes=[]
        for z in LEVELS[:-1]:
            for u in (-4.42,-.69,3.46):
                holes.append(glazing(end,u,z+.73,1.36,1.56,lod,2))
        joined_wall(end,.04,LOW+.35,holes,.25,(side<0,side>0))
        # Above the lower outer roof the core has exposed end walls and terrace access.
        x=side*CORE
        edges=((x,FRONT),(x,BACK)) if side>0 else ((x,BACK),(x,FRONT))
        upper=Facade(builder,*edges,'top floor terrace wall')
        joined_wall(upper,LOW,HIGH+.40,[glazing(upper,-1.45,LOW+.15,1.44,2.07,lod,2)],.23)
        # Delimit the open drive on the eastern side without a door across the route.
        inner=Facade(builder,*edges,'side of drive or garden recess')
        joined_wall(inner,.04,LEVELS[0],[],.22)


def add_building(builder,lod=False):
    slab(builder,box(-CORE+.075,FRONT+.075,CORE-.075,BACK-.075),.025,.22,STONE,'central ground plate')
    slab(builder,box(-END+.075,FRONT+3.66,-CORE-.075,BACK-.075),.025,.22,STONE,'west ground plate behind recess')
    main_front(builder,lod)
    for side in (-1,1):side_loggia(builder,side,lod)
    rear_and_ends(builder,lod)
    slab(builder,box(-CORE+.075,FRONT+.075,CORE-.075,BACK-.075),HIGH-.17,.20,ROOF,'top central flat roof')
    slab(builder,box(-2.0,BACK-3.2,.8,BACK-.6),HIGH+.03,.83,PLASTER,'stair roof head')
