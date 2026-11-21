"""The garden elevation of West Park Mansions and the two north-facing lightwells."""
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

STUCCO = 'warm grey roughcast'
LINTEL = 'pale grey rendered lintel'
BRICK = 'exposed reddish brick'
SHADE = 'weathered green grey window frame'
GLASS = 'muted blue grey apartment glazing'
CLEAR = 'light grey enclosed balcony glass'
IRON = 'iron balustrade'
CONCRETE = 'weathered concrete pergola'
FLOOR = 'grey gallery paving'
ROOF = 'dark flat roof finish'
DARK = 'brown painted entrance timber'
PALETTE = {name: {'color': rgb, 'roughness': rough} for name,rgb,rough in [
    (STUCCO,[.70,.66,.58],.93),(LINTEL,[.68,.66,.61],.89),
    (BRICK,[.48,.27,.20],.90),(SHADE,[.28,.34,.32],.73),
    (GLASS,[.21,.28,.29],.32),(CLEAR,[.35,.41,.40],.34),
    (IRON,[.24,.25,.22],.60),(CONCRETE,[.52,.51,.47],.86),
    (FLOOR,[.49,.46,.41],.88),(ROOF,[.35,.36,.33],.86),
    (DARK,[.29,.22,.17],.78)]}

SOUTH = -9.46
WEST, EAST = -14.10, 14.10
LEFT_TOWER, RIGHT_TOWER = -11.68, 11.45
CENTRE = 6.58
REAR = 10.03
ROOF_Z = 26.30
GARDEN_FLOORS = [1.05,4.24,7.39,10.54,13.69,16.84,19.99,23.14]


def sash(face, u, bottom, width, height, lod, glass=GLASS, tone=SHADE, columns=None):
    hole=box(u-width/2,bottom,u+width/2,bottom+height)
    face.window(hole, columns=columns or (2 if lod else 3), rows=2 if lod else 3,
                frame=tone, glass=glass, trim=False, label='recessed metal sash')
    face.box(u,bottom-.07,width+.18,.13,.24,.035,LINTEL,'concrete sill')
    return hole


def brick_corners(face, positions, height, lod):
    # The 2014 photograph shows alternating reddish bands at the outer corners.
    for side,u in positions:
        count=round(height/.51)
        for k in range(count):
            width=.28 if k%2 else .51
            centre=u+side*width/2
            face.box(centre,.34+k*.51,width,.21,.045,.018,BRICK,'exposed brick quoin')


def rail(face,u,bottom,width,lod):
    span=width-.12
    for z in [.16,.96]:face.box(u,bottom+z,span,.055,.07,-.215,IRON,'balcony rail')
    n=7 if lod else 17
    for k in range(n):
        t=(k+.5)/n-.5
        face.box(u+t*span,bottom+.56,.039,.78,.053,-.214,IRON,'vertical rail bar')


def joined_wall(face, bottom, top, holes, start_turn, end_turn, thickness=.30):
    """Mitre the hidden ends of walls wherever two exterior faces meet at right angles."""
    first = len(face.builder.parts)
    face.wall(bottom, top, holes, thickness=thickness, material=STUCCO)
    for part in face.builder.parts[first:]:
        vertices = []
        for vertex in part['vertices']:
            offset = vertex - face.center
            u, depth = offset @ face.t, offset @ face.n
            shift = 0.
            if abs(u + face.length / 2) < 1e-7:
                shift = -depth * start_turn
            elif abs(u - face.length / 2) < 1e-7:
                shift = depth * end_turn
            vertices.append(tuple(vertex + shift * face.t))
        part['vertices'] = vertices


def south_end(builder, x0,x1,side,lod):
    face=Facade(builder,(x0,SOUTH),(x1,SOUTH),'garden end bay')
    holes=[]
    for i,z in enumerate(GARDEN_FLOORS):
        h=1.68 if i<6 else 1.58
        holes.append(sash(face,0,z+.72,2.48,h,lod))
    joined_wall(face,.05,ROOF_Z+.22,holes,int(side>0),int(side<0),.48)
    edge=(x0 if side>0 else x1)-(x0+x1)/2
    brick_corners(face,[(side,edge)],ROOF_Z,lod)
    face.box(0,ROOF_Z+.20,x1-x0,.16,.35,.025,LINTEL,'tower roof coping')


def recess_frame(face,u,z,w,h,arch,lod):
    hole=opening(u,z,w,h,arch,9 if lod else 22)
    if arch:
        band=hole.buffer(.105,join_style=2).difference(hole)
        face.prism(band,-.045,.026,LINTEL,'shallow balcony arch')
    return hole


def south_gallery(builder,lod):
    face=Facade(builder,(-CENTRE,SOUTH),(CENTRE,SOUTH),'garden balcony wall')
    depth=1.16
    rear=Facade(builder,(-CENTRE,SOUTH+depth),(CENTRE,SOUTH+depth),'recessed garden wall')
    holes=[];inner=[];step=2*CENTRE/3
    for level,z in enumerate(GARDEN_FLOORS[:6]):
        for i in range(3):
            u=(i-1)*step;w=step-.53
            if level==0:
                if i==1:
                    door=box(u-1.56,z-.05,u+1.56,z+2.68)
                    holes.append(door);inner.append(sash(rear,u,z-.03,2.86,2.53,lod,tone=DARK,columns=3))
                else:
                    holes.append(sash(face,u,z+.75,w-.41,1.69,lod))
                continue
            is_arch=level==5
            bottom=z+.16
            hole=recess_frame(face,u,bottom,w,2.60,.53 if is_arch else 0,lod)
            holes.append(hole)
            # The 2014 photograph records a mixture of glazed and open balconies.
            # A glazed enclosure remains recessed behind the original wall opening.
            open_balcony=(level,i) in {(1,2),(2,1),(2,2),(3,1)}
            if open_balcony:
                rail(face,u,bottom,w,lod)
                inner.append(sash(rear,u,z+.59,w-.48,1.85,lod))
            else:
                glazing=Facade(builder,(-CENTRE,SOUTH+.22),(CENTRE,SOUTH+.22),'enclosed balcony')
                glazing.window(hole,columns=2 if lod else 4,rows=1 if lod else 2,
                               frame=SHADE,glass=CLEAR,trim=False,label='enclosure')
            builder.plan_prism(box(u-w/2,SOUTH+.04,u+w/2,SOUTH+depth),z-.03,z+.15,FLOOR,'gallery deck')
            for sx in [u-w/2,u+w/2]:
                builder.box((sx,SOUTH+depth/2,z+1.46),(.09,depth,2.82),STUCCO,label='balcony return')
    # The six early upper arches have been infilled around smaller rectangular
    # windows; the relief above each remains faintly visible in the 2014 photograph.
    for i in range(6):
        u=(i-2.5)*2*CENTRE/6
        holes.append(sash(face,u,GARDEN_FLOORS[6]+.81,1.60,1.48,lod))
        outline=opening(u,GARDEN_FLOORS[6]+.64,1.95,2.17,.47,9 if lod else 22)
        band=outline.buffer(.047,join_style=2).difference(outline)
        cap=band.intersection(box(u-1.1,GARDEN_FLOORS[6]+2.25,u+1.1,GARDEN_FLOORS[6]+2.90))
        face.prism(cap,-.026,.018,LINTEL,'infilled arch trace')
        holes.append(sash(face,u,GARDEN_FLOORS[7]+.68,1.58,1.65,lod))
    face.wall(.06,ROOF_Z,holes,thickness=.32,material=STUCCO)
    rear.wall(.07,GARDEN_FLOORS[6]-.08,inner,thickness=.23,material=STUCCO)
    face.box(0,ROOF_Z-.05,2*CENTRE,.18,.36,.03,LINTEL,'attic coping')


def pergola(builder,x):
    # Both ends carry separate flat open grilles rather than a central loggia.
    width,depth=4.24,3.35;yc=SOUTH+2.17
    for dx in [-width/2,0,width/2]:
        for dy in [-depth/2,depth/2]:
            builder.box((x+dx,yc+dy,ROOF_Z+1.12),(.24,.25,2.15),CONCRETE,label='pergola posts')
    for dy in [-depth/2,depth/2]:
        builder.box((x,yc+dy,ROOF_Z+2.17),(width+.83,.29,.27),CONCRETE,label='pergola longitudinal beams')
    for i in range(6):
        dx=(i-2.5)*width/5
        builder.box((x+dx,yc,ROOF_Z+2.38),(.22,depth+.88,.18),CONCRETE,label='open pergola rafters')


def wall_with_windows(builder,a,b,label,height,bays,lod,start_turn,end_turn,small=False):
    face=Facade(builder,a,b,label);holes=[]
    for i,z in enumerate(GARDEN_FLOORS):
        if z+2.56>height:continue
        for j,(u,w) in enumerate(bays):
            h=1.23 if small else 1.55
            holes.append(sash(face,u,z+.85,w,h,lod,columns=1 if w<1.12 and lod else 2))
    joined_wall(face,.04,height,holes,start_turn,end_turn)
    face.box(0,height-.015,face.length,.17,.38,.027,LINTEL,'parapet coping')
    return face


def north_and_sides(builder,lod):
    # The rear center pier and both tower ends project past two recessed
    # window strips, observed from opposite Changning Road stations in 2021.
    side_front=-7.91
    rim=[(RIGHT_TOWER,SOUTH),(RIGHT_TOWER,side_front),(EAST,side_front),(EAST,REAR),
         (6.95,REAR),(6.95,5.39),(2.48,5.39),(2.48,8.30),(-2.72,8.30),
         (-2.72,5.39),(-7.42,5.39),(-7.42,REAR),(WEST,REAR),(WEST,side_front),
         (LEFT_TOWER,side_front),(LEFT_TOWER,SOUTH)]
    perimeter = [(-CENTRE,SOUTH),(CENTRE,SOUTH),*rim]
    turns = {}
    for i,corner in enumerate(perimeter):
        prev = perimeter[i-1]
        nxt = perimeter[(i+1) % len(perimeter)]
        dx, dy = corner[0]-prev[0], corner[1]-prev[1]
        cross = dx*(nxt[1]-corner[1]) - dy*(nxt[0]-corner[0])
        turns[corner] = int(cross>0) - int(cross<0)
    for i,(a,b) in enumerate(zip(rim,rim[1:])):
        length=((a[0]-b[0])**2+(a[1]-b[1])**2)**.5
        extent=ROOF_Z-.10 if i not in [0,1,2,12,13,14] else ROOF_Z-1.22
        if i in [2,12]:bays=[(-6.55,1.22),(-3.54,1.72),(.25,1.62),(3.50,1.72),(6.67,1.21)]
        elif i in [3,11]:bays=[(-1.55,.67),(1.38,1.53)]
        elif i in [5,9]:bays=[(0,2.82)]
        elif i==7:bays=[(0,1.44)]
        elif length>3.1:bays=[(0,1.54)]
        elif length>2.1:bays=[(0,1.04)]
        else:bays=[]
        face=wall_with_windows(builder,a,b,'rear and side '+str(i),extent,bays,lod,turns[a],turns[b],small=i in [3,7,11])
        if i in [3,11]:
            direction=1 if i==3 else -1
            brick_corners(face,[(direction,-direction*face.length/2)],extent,lod)
    return Polygon([(-CENTRE,SOUTH),(CENTRE,SOUTH),*rim,(LEFT_TOWER,SOUTH)])


def lightwell_bases(builder,lod):
    # The 2021 road photographs show low built space beneath both upper wells.
    # The shop fronts farther north have no verified parcel link to this owner.
    bases=[]
    for x0,x1,top in [(-7.42,-2.72,5.94),(2.48,6.95,5.14)]:
        ground=box(x0,5.38,x1,8.28)
        outer=Facade(builder,(x1,8.28),(x0,8.28),'north low base')
        opening=sash(outer,.10,3.03,1.46,1.25,lod)
        outer.wall(.04,top,[opening],thickness=.27,material=STUCCO)
        for x in [x0,x1]:
            builder.box((x,6.83,top/2),(.13,2.90,top-.08),STUCCO,label='lightwell lower sidewall')
        builder.plan_prism(ground,top-.10,top+.10,ROOF,'lightwell lower roof')
        bases.append(ground)
    return bases


def add_building(builder,lod=False):
    south_end(builder,LEFT_TOWER,-CENTRE,1,lod)
    south_gallery(builder,lod)
    south_end(builder,CENTRE,RIGHT_TOWER,-1,lod)
    plan=north_and_sides(builder,lod)
    # Full solid base and continuous roof footprints meet the cut facades. The
    # lower roofs of the narrow outside returns are stepped independently.
    ground=plan
    for base in lightwell_bases(builder,lod):
        ground=ground.union(base)
    builder.plan_prism(ground,.025,.22,STUCCO,'continuous plinth')
    main=plan.intersection(box(LEFT_TOWER,-20,RIGHT_TOWER,20))
    ends=plan.difference(main)
    builder.plan_prism(main,ROOF_Z-.30,ROOF_Z-.02,ROOF,'main roof membrane')
    builder.plan_prism(ends,ROOF_Z-1.37,ROOF_Z-1.14,ROOF,'side roof membrane')
    # Close the one-metre roof step between the tower and the outside returns.
    for x in [LEFT_TOWER,RIGHT_TOWER]:
        builder.box((x,(REAR-7.91)/2,ROOF_Z-.69),(.20,REAR+7.91,1.29),STUCCO,label='roof setback riser')
    for x in [(LEFT_TOWER-CENTRE)/2,(RIGHT_TOWER+CENTRE)/2]:pergola(builder,x)
    # The garden entry canopy is visible below the apartments in 2014.
    builder.box((0,SOUTH-.51,3.78),(4.78,1.32,.22),CONCRETE,label='entry canopy')
    for x in [-1.96,1.96]:
        builder.box((x,SOUTH-.96,2.02),(.25,.26,3.34),BRICK,label='entry canopy columns')
