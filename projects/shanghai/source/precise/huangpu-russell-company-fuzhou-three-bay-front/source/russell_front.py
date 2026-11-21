"""North three-bay ashlar elevation of Russell & Co., with the current raised Fuzhou Road frontage."""
from math import cos,pi,sin,sqrt
from pathlib import Path
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union
from shapely import set_precision
from photo_architecture import Facade
from stone_mapping import STONE,stone_uv

JOINT='Pale mortar joints'
DRESS='Dark cut stone arch trim'
EDGE='Lighter dressed stone arris'
GLASS='Upper sash reflective glass'
DOOR_GLASS='Dark street door glazing'
FRAME='Aged pale aluminium window frame'
BLUE='Blue east door joinery'
WHITE='Ivory middle door joinery'
DARK='Black west door joinery'
IRON='Dark iron window and terrace supports'
RAIL='Painted cream landing iron'
LEAD='Zinc roof edge and gutter'
SOFFIT='Weathered pale eave and modillion'
STEP='Grey granite landing and stairs'
PLANTER='Buff stone planting enclosure'
SOIL='Dark planted bed soil'
GREEN='Low evergreen planting'
PIPES='Off-white drain and cable covers'
GALV='Pale condenser metal'
DARK_INTAKE='Condenser dark intake'
WOOD='Brown boarded terrace skirt'
PALETTE={
    STONE:{'color':[1.,1.,1.],'texture':str(Path(__file__).with_name('russell-weathered-stone.png')),'roughness':.94},
    JOINT:{'color':[.58,.54,.48],'roughness':.99},DRESS:{'color':[.108,.081,.068],'roughness':.91},
    EDGE:{'color':[.159,.130,.106],'roughness':.88},GLASS:{'color':[.192,.211,.195],'metallic':.16,'roughness':.30},
    FRAME:{'color':[.71,.70,.63],'metallic':.16,'roughness':.52},DOOR_GLASS:{'color':[.044,.064,.065],'metallic':.14,'roughness':.28},
    BLUE:{'color':[.017,.123,.247],'roughness':.54},
    WHITE:{'color':[.76,.735,.646],'roughness':.59},DARK:{'color':[.17,.143,.117],'roughness':.58},
    IRON:{'color':[.17,.172,.154],'metallic':.30,'roughness':.67},RAIL:{'color':[.76,.74,.661],'metallic':.21,'roughness':.65},
    LEAD:{'color':[.29,.295,.28],'metallic':.40,'roughness':.69},SOFFIT:{'color':[.675,.644,.571],'roughness':.86},
    STEP:{'color':[.46,.437,.392],'roughness':.91},PLANTER:{'color':[.58,.492,.376],'roughness':.93},
    SOIL:{'color':[.201,.207,.146],'roughness':1.},GREEN:{'color':[.185,.228,.16],'roughness':.98},
    PIPES:{'color':[.72,.713,.653],'roughness':.68},GALV:{'color':[.65,.637,.567],'metallic':.24,'roughness':.7},
    DARK_INTAKE:{'color':[.218,.221,.204],'metallic':.19,'roughness':.69},WOOD:{'color':[.27,.211,.164],'roughness':.83}}
EAST=.24
WEST=8.65
AXES=(1.535,4.45,7.365)
LANDING=1.56
EAVES=11.24


def semicircular(x,width,bottom,shoulder,rise,lod):
    count=14 if lod else 28
    crown=[(x+width*.5*cos(i*pi/count),shoulder+rise*sin(i*pi/count))for i in range(count+1)]
    return Polygon([(x-width/2,bottom),(x+width/2,bottom),*crown])


def pointed(x,width,bottom,shoulder,rise,lod):
    """Two circular arcs meet in a measurable Gothic point, with vertical spring tangents."""
    half=width/2
    shift=(rise*rise-half*half)/(2*half)
    radius=half+shift
    count=10 if lod else 19
    top=[]
    for i in range(2*count+1):
        u=half-half*i/count
        z=shoulder+sqrt(max(0.,radius**2-(abs(u)+shift)**2))
        top.append((x+u,z))
    return Polygon([(x-half,bottom),(x+half,bottom),*top])


def rail_line(face,points,r,mat,label,lod):
    face.builder.tube([face.point(*q)for q in points],r,mat,5 if lod else 8,label)


def lower_opening(face,x,index,lod):
    width=(1.88,1.89,1.79)[index]
    floor=LANDING if index<2 else 1.29
    shoulder=3.76;rise=.99
    cut=semicircular(x,width,floor,shoulder,rise,lod)
    hu=semicircular(x,width+.365,floor-.03,shoulder,rise+.188,lod)
    trim=semicircular(x,width+.112,floor-.01,shoulder,rise+.059,lod)
    face.prism(hu.difference(cut),-.038,.062,DRESS,'Ground voussoirs')
    face.prism(trim.difference(cut),.061,.113,EDGE,'Inner circular moulding')
    # Discrete bedding joints are visible in the arched stones around all three doors.
    for j in range(1,12):
        az=pi*j/12
        rail_line(face,[(x+(width/2+rr)*cos(az),shoulder+(rise+rr)*sin(az),.064)for rr in (.064,.18)],.009,JOINT,'Segment lines in the round arches',lod)
    mat=(BLUE,WHITE,DARK)[index]
    face.prism(cut,-.300,-.277,DOOR_GLASS,'Recessed lower glazing')
    rim=cut.difference(cut.buffer(-.075,join_style='mitre'))
    bars=[box(x-width/2,shoulder-.065,x+width/2,shoulder+.066),
          box(x-.033,floor+.016,x+.033,shoulder+.015)]
    for sign in [-1,1]:
        side=x+sign*width*.29
        bars.append(box(side-.019,floor+.01,side+.019,shoulder-.02))
    if index==1:
        # Paired curved fanlight rails meet at the head of the centre mullion.
        for sign in [-1,1]:
            pts=[(x+sign*.685*t,shoulder+.02+.70*(2*t-t*t),-.158)for t in (0,.13,.28,.46,.67,.85,1.)]
            rail_line(face,pts,.03,WHITE,'White curved fanlight rails',lod)
    elif index==2:
        for sign in [-1,1]:
            rail_line(face,[(x,shoulder-.01,-.161),(x+sign*.62,shoulder+.65,-.161)],.035,DARK,'West fanlight spokes',lod)
    else:
        face.box(x,4.15,.54,.49,.043,-.189,FRAME,'Unlettered pale sign backing')
    if index==0:
        for sign in [-1,1]:
            bars.append(box(x+sign*.52-.030,floor+.014,x+sign*.52+.030,shoulder-.04))
    face.prism(unary_union([rim,cut.intersection(unary_union(bars))]),-.220,-.14,mat,'Ground door frames '+str(index+1))
    face.box(x,floor-.045,width+.13,.09,.46,-.045,STEP,'Dressed thresholds')
    return cut


def splayed_sash(face,x,index,lod):
    bottom=5.92;shoulder=7.85;tip=9.58
    cut=pointed(x,2.01,bottom,shoulder,tip-shoulder,lod)
    out=pointed(x,2.33,bottom-.05,shoulder,tip-shoulder+.19,lod)
    second=pointed(x,2.16,bottom-.022,shoulder,tip-shoulder+.084,lod)
    face.prism(out.difference(cut),-.025,.085,DRESS,'Outer Gothic hoods')
    face.prism(second.difference(cut),.071,.144,EDGE,'Inner Gothic mouldings')
    # Behind the projecting metal sashes, the two eastern tympana retain
    # masonry. The west opening shows a small pale two-light window above.
    face.prism(cut,-.27,-.20,STONE,'Stone tympana')
    if index==2:
        z0,z1=8.41,8.87
        face.box(x,(z0+z1)/2,.54,z1-z0,.06,-.136,FRAME,'West upper fanlight frame')
        for dx in [-.123,.123]:face.box(x+dx,(z0+z1)/2,.204,z1-z0-.105,.05,-.092,GLASS,'Two small upper lights')
    sx=1.03;sw=.73;d1=.19;d2=.51
    cross=[(x-sx,d1),(x-sw,d2),(x+sw,d2),(x+sx,d1)]
    for z,h,mat,label in [(5.955,.13,IRON,'Projecting boxed sills'),(8.18,.11,FRAME,'Pale folded sash heads')]:
        plan=Polygon([(u,-d)for u,d in cross]+[(x+sx,.10),(x-sx,.10)])
        face.builder.plan_prism(plan,z-h/2,z+h/2,mat,label)
    for k,((u0,d0),(u1,d_1)) in enumerate(zip(cross,cross[1:])):
        segment=Facade(face.builder,(u0,-d0),(u1,-d_1),f'Upper bay {index+1}.{k+1}')
        half=segment.length/2;z0,z1=6.03,8.12
        pane=box(-half,z0,half,z1)
        outer=pane.difference(pane.buffer(-.047,join_style='mitre'))
        if k==1:
            outer=unary_union([outer,box(-.030,z0,.030,z1)])
            if index!=1:
                for mul in (-.39,.39):outer=unary_union([outer,box(mul-.013,z0,mul+.013,z1)])
        segment.prism(pane,-.07,-.042,GLASS,'Glazing')
        segment.prism(outer,-.046,.009,FRAME,'Sash rails')
        if index==0:
            for dz in (.18,.51):
                segment.box(0,z0+dz,segment.length+.015,.043,.060,.095,IRON,'Balconette handrails')
            if not lod:
                for j in range(max(1,round(segment.length/.125))):
                    u=-half+.06+j*.125
                    if u<half-.025:segment.box(u,z0+.342,.022,.33,.044,.092,IRON,'Balconette balusters')
        elif k==1:
            segment.box(0,z0+.081,segment.length,.19,.058,.048,IRON,'Dark base plates')
    return cut


def stone_courses(face,holes,lod):
    main=box(EAST,0,WEST,10.91).difference(unary_union(holes))
    face.prism(main,-.36,-.028,JOINT,'Masonry rear and lime beds')
    pitch=.419
    for row in range(27):
        z=row*pitch
        for col in range(-1,10):
            start=EAST+(col+(row%2)*.51)*1.052
            block=box(start+.012,z+.010,start+1.052-.011,z+pitch-.009)
            piece=set_precision(main.intersection(block),.0001)
            if not piece.is_empty and piece.area>.00005:
                face.prism(piece,-.026,.009+(row%3)*.001,STONE,'Ashlar course %02d'%row)


def canopy(face,lod):
    span=WEST-EAST;mid=(WEST+EAST)/2
    for z,h,depth,advance,mat in [(10.62,.11,.23,.078,EDGE),(10.73,.13,.30,.10,DRESS),
            (10.98,.13,.62,.268,SOFFIT),(11.105,.135,.80,.337,SOFFIT),(11.215,.072,.84,.353,LEAD)]:
        face.box(mid,z,span,h,depth,advance,mat,'Projecting cornice courses')
    for i in range(18):
        x=EAST+.25+i*(span-.50)/17
        face.box(x,10.883,.131,.225,.433,.169,SOFFIT,'Eave modillions')
        if not lod:face.box(x,10.817,.109,.137,.278,.218,DRESS,'Modillion lower necks')
    face.box(mid,11.087,span,.175,2.03,-.995,LEAD,'Short roof return')
    # The steel back closes onto the existing six-metre source mass. No
    # roof form, rear window or courtyard architecture is visible from this side.
    face.box(mid,8.70,span,4.77,.11,-1.96,LEAD,'Unadorned inner roof joint')
    for x in (EAST+.052,WEST-.052):face.box(x,8.70,.105,4.77,2.05,-.990,LEAD,'Short roof-end joint')


def landing(face,lod):
    b=face.builder;low=LANDING
    b.plan_prism(box(.32,-1.015,5.98,-.02),0,low-.065,WOOD,'Raised landing skirt')
    b.plan_prism(box(.27,-1.105,6.03,.16),low-.074,low,STEP,'Stone landing')
    for z in (.19,.40,.62,.85,1.07,1.30):
        face.box(3.15,z,5.61,.018,.026,1.026,IRON,'Horizontal skirt joints')
    # The separate everyday 17 entrance stands on the pale addition to the
    # west. Here the stairs follow the east landing's outside edge.
    treads=9;stair_x0=.32;stair_x1=1.19
    for i in range(treads):
        depth=1.06+(treads-i)*.215
        b.plan_prism(box(stair_x0,-depth,stair_x1,-depth+.218),0,(i+1)*low/treads,STEP,'East approach treads')
    # Raised planter with an inset bed rather than a full block at walking level.
    outer=box(1.20,-2.94,5.91,-1.085);inner=outer.buffer(-.115,join_style='mitre')
    b.plan_prism(outer.difference(inner),0,.49,PLANTER,'Stone planter curb')
    b.plan_prism(inner,.09,.41,SOIL,'Planted bed')
    if not lod:
        for j in range(6):
            for k in range(2):
                x=1.54+j*.726+.048*(k%2);d=1.52+.61*k+.03*(j%3)
                b.plan_prism(Polygon([(x-.28,-d-.13),(x-.19,-d-.27),(x+.18,-d-.23),(x+.29,-d-.05),(x+.15,-d+.22),(x-.22,-d+.18)]),.40,.50+.037*((j+k)%3),GREEN,'Low bed planting')
    else:b.plan_prism(inner.buffer(-.09,join_style='mitre'),.39,.51,GREEN,'Low bed planting')
    for x0,x1,d0,d1 in [(1.16,5.94,1.10,1.10),(.35,.35,2.97,1.07)]:
        z0=low if d0==d1 else .16;z1=low
        for h in [.13,.83,.97]:
            rail_line(face,[(x0,z0+h,d0),(x1,z1+h,d1)],.023,RAIL,'Landing and stair rails',lod)
        pieces=max(3,round((abs(x1-x0)+abs(d1-d0))/.39))
        for i in range(pieces+1):
            t=i/pieces;x=x0+(x1-x0)*t;d=d0+(d1-d0)*t;z=z0+(z1-z0)*t
            rail_line(face,[(x,z+.02,d),(x,z+.96,d)],.021,RAIL,'Landing rail uprights',lod)
    for i in range(5):
        x=1.22+.92*i;d=1.102
        for sign in [-1,1]:
            pts=[(x+.89*t,low+.49+sign*.303*sin(pi*t),d)for t in [j/(8 if lod else 14)for j in range((8 if lod else 14)+1)]]
            rail_line(face,pts,.012,RAIL,'Curved landing railing',lod)
    b.plan_prism(box(6.46,-.66,8.27,.06),0,1.28,STEP,'West door landing')


def services(face,lod):
    for x in (.43,5.98):
        rail_line(face,[(x,10.77,.28),(x,10.53,.15),(x,5.29,.15),(x,4.83,.21),(x,.53,.21)],.049,PIPES,'Painted rainwater pipes',lod)
        if not lod:
            for z in (2.63,4.26,6.82,8.75):face.box(x,z,.154,.033,.129,.09,IRON,'Iron pipe straps')
    for x,z in [(.63,5.43),(3.32,6.46),(4.45,8.51),(8.32,9.14),(6.32,2.07)]:
        face.box(x,z,.58,.40,.33,.175,GALV,'Wall-mounted condensers')
        ring=Polygon([(x+.12+.127*cos(2*pi*i/20),z+.127*sin(2*pi*i/20))for i in range(20)])
        face.prism(ring,.34,.355,DARK_INTAKE,'Condenser fans')
        if not lod:
            for radius in [.056,.103]:
                pts=[(x+.12+radius*cos(2*pi*i/20),z+radius*sin(2*pi*i/20),.361)for i in range(21)]
                rail_line(face,pts,.008,GALV,'Fan wire guards',lod)


def add_building(builder,lod=False):
    face=Facade(builder,(-5.,0.),(5.,0.),'Fuzhou north')
    cuts=[]
    for i,x in enumerate(AXES):
        cuts.append(lower_opening(face,x,i,lod))
        cuts.append(splayed_sash(face,x,i,lod))
    stone_courses(face,cuts,lod);canopy(face,lod);landing(face,lod);services(face,lod)
    for item in builder.parts:
        if item['material']==STONE:
            item['texcoords']=[(u,1-v)for u,v in (stone_uv(item['label'],pt)for pt in item['vertices'])]
