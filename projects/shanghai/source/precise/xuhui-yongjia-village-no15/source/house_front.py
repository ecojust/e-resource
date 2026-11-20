"""No. 15, Lane 580 Yongjia Road. Local X runs east along the garden front, Y into the house."""
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

WEST, EAST = -4.65, 4.65
FRONT, COURT = 0., -2.86
EAVE = 6.27
ROOF_CUT = 1.10
END_DEPTH = 4.10
PORCH_X, PORCH_Y = -3.54, -1.38
MATERIALS = {
    'ivory roughcast': [.775,.728,.611], 'red oxide base': [.355,.085,.056],
    'wine sash': [.304,.108,.084], 'recessed glass': [.216,.256,.252],
    'green enamel': [.052,.216,.163], 'ivory numerals': [.873,.841,.720],
    'weathered concrete': [.676,.662,.606], 'grey porch tile': [.232,.249,.249],
    'timber eaves': [.174,.149,.123], 'dark iron': [.112,.132,.13],
    'dark door': [.207,.157,.123], 'neutral section': [.653,.640,.590],
}
PALETTE = {k: {'color': color, 'roughness': .40 if k in ('recessed glass','green enamel') else .83}
           for k,color in MATERIALS.items()}


def panel(frame, u, z, width, height, columns, rows, bars=False):
    profile=opening(u,z,width,height)
    frame.prism(profile,-.15,-.13,'recessed glass','glass reveal')
    inner=profile.buffer(-.058,join_style='mitre')
    frame.prism(profile.difference(inner),-.14,-.015,'wine sash','recessed timber sash')
    for i in range(1,columns):
        frame.box(u+width*(i/columns-.5),z+height/2,.036,height,.055,-.075,'wine sash','vertical glazing bars')
    for j in range(1,rows):
        frame.box(u,z+height*j/rows,width,.033,.055,-.08,'wine sash','horizontal glazing bars')
    frame.box(u,z-.036,width+.12,.072,.14,.034,'weathered concrete','projecting window sill')
    if bars:
        for j in range(1,10):
            frame.box(u+width*(j/10-.5),z+height*.50,.017,height*.97,.019,.056,'dark iron','window guard rods')
        for j in (.22,.73):
            frame.box(u,z+height*j,width+.025,.027,.024,.058,'dark iron','window guard rails')


def fence(builder,a,b,modules,lod,label):
    """The precast units have a diamond centre framed by four linked octagonal openings."""
    face=Facade(builder,a,b,label);length=face.length;width=length/modules
    bottom,top=.27,1.22
    face.box(0,.135,length,.27,.18,0,'red oxide base','rendered plinth')
    face.box(0,top+.055,length+.04,.11,.245,0,'weathered concrete','cap')
    holes=[]
    for i in range(modules):
        x=-length/2+(i+.5)*width
        for j in range(2):
            z=bottom+.234+j*.471;w=width*.335;h=.192
            holes.append(Polygon([(x-w*.49,z-h),(x+w*.49,z-h),(x+w,z-h*.42),
                                  (x+w,z+h*.43),(x+w*.49,z+h),(x-w*.49,z+h),
                                  (x-w,z+h*.43),(x-w,z-h*.42)]))
        if i: # Smaller diamonds between the four adjoining octagonal cells.
            x-=width/2;z=(bottom+top)/2
            holes.append(Polygon([(x,z-.125),(x+width*.23,z),(x,z+.125),(x-width*.23,z)]))
    face.prism(box(-length/2,bottom,length/2,top).difference(unary_union(holes)),-.063,.063,
               'weathered concrete','open concrete screen')
    if not lod:
        # Shallow cast returns distinguish the two sides of each real opening.
        for hole in holes:
            lip=hole.buffer(.014,join_style='mitre').difference(hole)
            face.prism(lip,.063,.075,'weathered concrete','cast edges of pierced units')
    for u in (-length/2,length/2):
        face.box(u,.70,.165,1.40,.205,0,'weathered concrete','end pier')
    if not lod:
        for i in range(1,modules):
            face.box(-length/2+i*width,1.269,.007,.099,.252,0,'neutral section','cap joint')


def number_plate(face,u,z):
    face.box(u,z,.305,.216,.027,.025,'green enamel','enamel street number')
    face.prism(box(u-.139,z-.094,u+.139,z+.094).difference(box(u-.135,z-.09,u+.135,z+.09)),
               .040,.043,'weathered concrete','thin enamel border')
    for xy in [[(-.090,.030),(-.068,.052),(-.068,-.048)],[(-.091,-.048),(-.045,-.048)],
               [(.064,.052),(.007,.052),(.004,.005),(.039,.009),(.059,.002),(.068,-.014),
                (.066,-.035),(.053,-.049),(.030,-.053),(.006,-.048),(-.002,-.039)]]:
        line=LineString([(u+x,z+y)for x,y in xy]).buffer(.0065,cap_style='square',join_style='round')
        face.prism(line,.041,.046,'ivory numerals','street number 15')


def porch(builder,lod):
    w=2.18;depth=-PORCH_Y;center=PORCH_X
    face=Facade(builder,(center-w/2,PORCH_Y),(center+w/2,PORCH_Y),'entry porch/garden')
    end=Facade(builder,(center+w/2,PORCH_Y),(center+w/2,0),'entry porch/east')
    west=Facade(builder,(center-w/2,0),(center-w/2,PORCH_Y),'entry porch/west reveal')
    outline=Polygon([(-w/2,0),(w/2,0),(w/2,2.47),(0,3.15),(-w/2,2.47)])
    holes=[opening(x,.07,.715,2.25,.38,18)for x in (-.48,.48)]
    face.wall(0,3.15,holes,.135,'ivory roughcast',outline=outline)
    end.wall(0,2.47,[opening(.05,.07,.82,2.01,.34,18)],.12,'ivory roughcast')
    west.wall(0,2.47,[opening(0,.07,.78,2.01,.34,18)],.12,'ivory roughcast')
    number_plate(end,-.516,1.78)
    builder.box((center,PORCH_Y/2,.065),(w,depth,.13),'weathered concrete',label='porch/threshold slab')
    roof=Facade(builder,(center-1,PORCH_Y-.145),(center+1,PORCH_Y-.145),'entry porch/roof')
    for sign in (-1,1):
        roof.prism(Polygon([(0,3.14),(sign*1.19,2.402),(sign*1.19,2.512),(0,3.251)]),
                   -depth-.22,0,'grey porch tile','two pitched tile sheets')
        n=4 if lod else 11
        for k in range(1,n):
            a=sign*1.18*k/n;zz=3.24-abs(a)*.62
            roof.box(a,zz,.057,.046,depth+.18,-depth*.49,'grey porch tile','raised tile courses')
    for dx in (-.45,.45):
        face0=Facade(builder,(center-1,0),(center+1,0),'porch recess')
        face0.box(dx,1.09,.74,2.10,.05,-.177,'dark door','recessed door leaf')
        for z in (.65,1.64):
            face0.box(dx,z,.61,.74,.018,-.143,'timber eaves','door rail and panel')


def east_end(builder,lod):
    east=Facade(builder,(EAST,0),(EAST,END_DEPTH),'curved east parapet')
    # The photographed plain end wall rises in two shallow lobes above the tiled eave.
    z=[(0,6.80),(.16,6.84),(.50,6.67),(.94,6.62),(1.24,6.68),(1.48,6.78),
       (1.76,6.73),(2.05,6.55),(2.29,6.50),(2.63,6.62),(2.87,6.79),
       (3.13,6.80),(3.38,6.65),(3.64,6.31),(END_DEPTH,5.97)]
    half=END_DEPTH/2;center=1.19
    holes=[opening(center,.77,.72,1.40),opening(center,3.94,.77,1.35)]
    outline=Polygon([(-half,0),(half,0)]+[(u-half,v)for u,v in reversed(z)])
    east.wall(0,7,holes,.26,'ivory roughcast',outline=outline)
    if not lod:
        profile=LineString([(u-half,v)for u,v in z]).buffer(.025,cap_style='flat',join_style='round')
        east.prism(profile.intersection(outline),-.035,.028,'weathered concrete','cap following gable top')
    for h in holes:
        a,b,c,d=h.bounds;panel(east,(a+c)/2,b,c-a,d-b,2,2)
    east.box(0,.195,END_DEPTH,.39,.035,.012,'red oxide base','red base finish')
    for yc in [3.72]:
        builder.box((EAST+.035,yc,3.04),(.075,.075,6.08),'dark iron',label='side wall/east drainpipe')
    # Rear and west edges of the partial section stay editable and visually quiet.
    builder.box((EAST-.42,(END_DEPTH+ROOF_CUT)/2,2.91),(.12,END_DEPTH-ROOF_CUT,5.82),
                'neutral section',label='east return/interior backing')
    builder.box((EAST-.23,END_DEPTH-.04,2.91),(.46,.08,5.82),'neutral section',label='east return/rear cut')


def house(builder,lod):
    front=Facade(builder,(WEST,FRONT),(EAST,FRONT),'south garden wall')
    upper=[(-2.01,1.05),(.15,1.45),(2.94,1.55)]
    lower=[(-1.86,.77),(.15,1.67),(2.94,1.71)]
    doors=[opening(PORCH_X+d,0,.78,2.18) for d in (-.45,.45)]
    holes=doors+[opening(u,3.86,w,1.63)for u,w in upper]+[opening(u,.78,w,1.71)for u,w in lower]
    front.wall(0,EAVE,holes,.23,'ivory roughcast')
    front.box(0,.155,EAST-WEST,.31,.04,.007,'red oxide base','red plinth finish')
    for i,(u,w) in enumerate(upper):panel(front,u,3.86,w,1.63,3,4)
    for i,(u,w) in enumerate(lower):panel(front,u,.78,w,1.71,3,2,i>0 and not lod)
    for u in (-1.05,4.49):
        builder.lathe((u,-.048),[(.06,.043),(5.91,.043)],'dark iron',8 if lod else 14,'south wall/drainpipes')
        if not lod:
            for z in [1.1,2.8,4.6,5.8]:front.box(u,z,.118,.045,.136,.025,'dark iron','drainpipe clamps')
    # A shallow canopy is visible over the two broad ground-floor windows in the 2014 view.
    for u,w in lower[1:]:
        hood=Facade(builder,(u+w/2+.17,0),(u+w/2+.17,.44),'ground windows/canopy')
        canopy=Polygon([(-.66,2.87),(-.19,2.96),(-.19,3.005),(-.66,2.915)])
        hood.prism(canopy,-w-.34,0,'weathered concrete','shallow awning')
        for x in [u-w*.40,u+w*.40]:
            edge=Facade(builder,(x,0),(x,.40),'ground windows/brackets')
            edge.prism(Polygon([(-.20,2.52),(-.20,2.89),(-.56,2.82)]),-.026,.026,'dark iron','awning side bracket')
    front.box(0,EAVE-.038,EAST-WEST+.17,.105,.295,.075,'timber eaves','overhanging eave')
    side=Facade(builder,(EAST,0),(EAST,ROOF_CUT),'south roof band')
    roof=Polygon([(-ROOF_CUT/2-.20,EAVE+.003),(ROOF_CUT/2,EAVE+.40),(ROOF_CUT/2,EAVE+.48),(-ROOF_CUT/2-.20,EAVE+.087)])
    side.prism(roof,-(EAST-WEST),-.27,'grey porch tile','visible south roof pitch')
    if not lod:
        for i in range(36):
            x=WEST+.11+i*(EAST-WEST-.45)/35
            section=Facade(builder,(x,0),(x,ROOF_CUT),'south roof band')
            tile=Polygon([(-ROOF_CUT/2-.15,EAVE+.105),(ROOF_CUT/2,EAVE+.48),
                          (ROOF_CUT/2,EAVE+.502),(-ROOF_CUT/2-.15,EAVE+.127)])
            section.prism(tile,-.016,.016,'grey porch tile','tile edge')
    builder.box((0,ROOF_CUT-.04,EAVE/2),(EAST-WEST,.08,EAVE),'neutral section',label='south elevation/rear cut')
    builder.box((WEST+.04,ROOF_CUT/2,EAVE/2),(.08,ROOF_CUT,EAVE),'neutral section',label='south elevation/west cut')
    porch(builder,lod);east_end(builder,lod)
    fence(builder,(WEST,COURT),(EAST-.25,COURT),14,lod,'garden/front fence')
    fence(builder,(EAST-.25,COURT),(EAST-.25,-.15),4,lod,'garden/return fence')
