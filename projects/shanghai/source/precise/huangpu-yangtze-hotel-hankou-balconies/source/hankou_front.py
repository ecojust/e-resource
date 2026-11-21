"""Three balcony stacks above the street entrance of the Yangtze Hotel, March 2024."""
from math import cos, sin, pi
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade

CREAM = 'ivory sand render'
BOARD = 'warm grey limestone'
RIM = 'pale cast stone coping'
IRON = 'charcoal balcony iron'
DARK = 'dark bronze entrance framing'
GLASS = 'blue grey window glass'
AMBER = 'amber vestibule glass'
LEAVES = 'leaf green planter'
FLOWERS = 'deep rose flower clusters'
RED = 'vermilion flower petals'
PALETTE = {name:dict(color=color,roughness=rough) for name,color,rough in (
    (CREAM,[.82,.82,.76],.92),(BOARD,[.65,.62,.56],.85),
    (RIM,[.86,.85,.79],.81),(IRON,[.15,.17,.18],.64),
    (DARK,[.17,.13,.12],.55),(GLASS,[.25,.33,.36],.35),
    (AMBER,[.59,.38,.18],.29),(LEAVES,[.20,.32,.17],.93),
    (FLOWERS,[.58,.075,.095],.85),(RED,[.77,.12,.13],.83))}
PITCH = 4.76
AXES = (-PITCH,0.,PITCH)
WIDTH = 2.70 * PITCH
FLOORS = (4.53,8.32,12.10,15.89)
HEAD = 19.57

def rect(x0,z0,x1,z1):
    return box(x0,z0,x1,z1)

def rail_field(f,length,z,lod,name):
    """Paired open V's and vertical pickets are visible in the 2024 side photograph."""
    width=length/2
    bars=[rect(-width,z,width,z+.06),rect(-width,z+.91,width,z+.966)]
    posts=[-width,0,width] if length<1 else [-width,-width/3,width/3,width]
    for a,c in zip(posts,posts[1:]):
        bars.append(rect(a-.018,z,a+.018,z+.92))
        mid=(a+c)/2
        for shift in ([.0] if lod else [.0,.095]):
            bars.append(LineString([(a+.02,z+.84-shift),(mid,z+.17-shift/2),
                                    (c-.02,z+.84-shift)]).buffer(.012 if not lod else .019,
                                                                  cap_style=2,join_style=2))
    bars.append(rect(width-.018,z,width+.018,z+.92))
    f.prism(unary_union(bars),-.018,.018,IRON,name)

def rose_spray(builder,axis,base,lod,label):
    # Hanging clusters are detachable from the structural rail. This is the 2024 red display.
    by_material={LEAVES:[[],[]],FLOWERS:[[],[]],RED:[[],[]]}
    count=11 if lod else 25
    for i in range(count):
        t=i/(count-1)
        x=axis-1.22+2.44*t
        front=1.19 if abs(x-axis)<.93 else 1.19-(abs(x-axis)-.93)*.89
        z=base+.20+.042*sin(i*2.3)
        for j,mat in enumerate([LEAVES,FLOWERS] if lod else [LEAVES,FLOWERS,RED]):
            xx=x+(j-1)*.035
            cy=-front-.055*j
            cz=z-.057*j+.047*sin(i*.96+j*1.3)
            width=(.135 if lod else .092)*(1+.15*cos(i))
            height=(.20 if j==0 else .122)*(1+.19*sin(i*2))
            if i%4==1:height*=1.4
            points,faces=by_material[mat];first=len(points)
            points.extend([(xx,cy,cz+height),(xx,cy,cz-height)]+[
                (xx+width*cos(k*pi/3),cy+.071*sin(k*pi/3),cz)for k in range(6)])
            for k in range(6):
                a=first+2+k;b=first+2+(k+1)%6
                faces.extend([(first,a,b),(first+1,b,a)])
    for mat,(verts,faces) in by_material.items():
        if verts:builder.add(verts,faces,mat,label+' '+mat)

def balcony(builder,axis,base,lod,index):
    label=f'balcony {index}'
    outer=[(-1.40,.015),(-1.40,-.78),(-.92,-1.20),(.92,-1.20),(1.40,-.78),(1.40,.015)]
    edge=[(axis+x,y)for x,y in outer]
    plan=Polygon(edge);builder.plan_prism(plan,base-.21,base,RIM,label+' faceted slab')
    for x in [-.61,.61]:
        # Sloping bracket visible from the underside, with the thinner tip toward the street.
        prof=Polygon([(0,base-.20),(-.82,base-.20),(-.82,base-.32),(-.27,base-.48),(0,base-.48)])
        builder.prism(prof,axis+x-.095,axis+x+.095,lambda y,z,d:(d,y,z),BOARD,label+' bracket')
    for k,(a,b) in enumerate(zip(edge,edge[1:])):
        f=Facade(builder,a,b,'balcony rail')
        rail_field(f,f.length,base,lod,label+f' panel {k+1}')
    rose_spray(builder,axis,base,lod,label)

def glazed(f,x,bottom,width,height,lod,label):
    outer=rect(x-width/2,bottom,x+width/2,bottom+height);inner=outer.buffer(-.043,join_style=2)
    glass=inner.difference(unary_union([rect(x-.021,bottom,x+.021,bottom+height),
            rect(x-width/2,bottom+height*.74,x+width/2,bottom+height*.74+.035)]))
    if not lod:
        extra=[rect(x-width*.25-.012,bottom+height*.74,x-width*.25+.012,bottom+height),
               rect(x+width*.25-.012,bottom+height*.74,x+width*.25+.012,bottom+height),
               rect(x-width/2,bottom+height*.87,x+width/2,bottom+height*.87+.018)]
        glass=glass.difference(unary_union(extra))
    f.prism(outer,-.155,-.142,GLASS,label+' glazing')
    f.prism(outer.difference(glass),-.14,-.075,IRON,label+' steel bars')
    return outer

def entrance(builder,f,lod):
    door_half=2.13
    o=rect(-door_half,0,door_half,3.55)
    wings=[(-2.13,-.89),(.89,2.13)]
    for left,right in wings:
        # The photograph shows projecting, curved glazed sidelights flanking the paired door leaves.
        profile=[]
        for k in range(7 if not lod else 4):
            t=k/(6 if not lod else 3);x=left+(right-left)*t
            profile.append((x,.22-.31*sin(pi*t)))
        for j,(a,b) in enumerate(zip(profile,profile[1:])):
            section=Facade(builder,a,b,'curved sidelight')
            section.prism(rect(-section.length/2,.20,section.length/2,3.48),
                          -.023,.006,AMBER,'amber curved panel')
            for z,h in ((.18,.19),(2.61,.12),(3.12,.10),(3.46,.07)):
                section.prism(rect(-section.length/2,z,section.length/2,z+h),.006,.064,DARK,'sidelight bronze rail')
            if not lod:
                section.prism(rect(-.014,.35,.014,3.46),.006,.024,DARK,'sidelight astragal')
    door=rect(-.89,.035,.89,3.48)
    f.prism(door,-.46,-.435,AMBER,'paired closed entrance glass')
    keys=[rect(-.045,0,.045,3.50),rect(-.9,.12,.9,.31),rect(-.9,2.44,.9,2.60),
          rect(-.9,2.88,.9,3.04),rect(-.9,3.40,.9,3.50)]
    f.prism(door.difference(door.buffer(-.075,join_style=2).difference(unary_union(keys))),
            -.435,-.365,DARK,'double entrance door frame')
    for x in (-2.16,-.91,.91,2.16):
        f.prism(rect(x-.055,.035,x+.055,3.54),-.45,.065,DARK,'vestibule brass toned jamb')
    # A lobed canopy has a higher central front and swept returns to the wall.
    edge=[(-2.67,.02),(-2.67,-.82),(-2.48,-1.10),(-1.74,-1.17),
          (-1.16,-1.33),(-.62,-1.52),(.62,-1.52),(1.16,-1.33),
          (1.74,-1.17),(2.48,-1.10),(2.67,-.82),(2.67,.02)]
    builder.plan_prism(Polygon(edge),3.59,3.68,DARK,'canopy underside')
    for j,(a,b) in enumerate(zip(edge,edge[1:])):
        panel=Facade(builder,a,b,'canopy edge')
        rise=.16*(1-min(abs((a[0]+b[0])/2)/2.67,1))
        h=3.97+rise
        rail_field_height=rect(-panel.length/2,3.68,panel.length/2,h)
        cuts=[]
        if panel.length>.28:
            for k in range(2 if lod else 4):
                cx=-panel.length/2+panel.length*(k+.5)/(2 if lod else 4)
                q=min(.095,panel.length/(7 if lod else 13))
                cuts.append(Polygon([(cx-q,3.81),(cx,3.90+rise*.5),(cx+q,3.81),(cx,3.72)]))
        panel.prism(rail_field_height.difference(unary_union(cuts)),.0,.047,IRON,'openwork dark valance')
        panel.prism(rect(-panel.length/2,h,panel.length/2,h+.055),.0,.065,DARK,'curved front crest')
    for x in (-2.43,2.43):
        builder.tube([(x,-.03,3.10),(x,-1.00,3.58)],.041,IRON,6,'support to canopy')
    return o

def add_building(builder,lod):
    f=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'Hankou frontage')
    openings=[entrance(builder,f,lod)]
    for k,axis in enumerate(AXES):
        for i,base in enumerate(FLOORS):
            openings.append(glazed(f,axis,base+.02,.91 if lod else .94,2.41,lod,'balcony door'))
            balcony(builder,axis,base,lod,(k+1)*10+i+1)
    for axis in (-PITCH/2,PITCH/2):
        for base in FLOORS:
            sill=base+(1.18 if base==FLOORS[0] else .83)
            openings.append(glazed(f,axis,sill,.90,1.77,lod,'companion window'))
            f.prism(rect(axis-.51,sill-.08,axis+.51,sill),-.04,.11,RIM,'stone sill')
    # The lower stone skin stops before the flanking shop windows in the frontal photograph.
    door_zone=rect(-3.78,0,3.78,4.50)
    f.prism(door_zone.difference(unary_union(openings)),-.49,.008,BOARD,'ground stone wall with true entrance opening')
    for j in range(1,6):
        stripe=rect(-3.78,j*.70,3.78,j*.70+.018).difference(unary_union(openings))
        f.prism(stripe,.009,.018,CREAM,'ashlar course')
    f.prism(rect(2.75,2.48,2.94,2.73),.012,.043,LEAVES,'green street address tablet')
    f.prism(rect(3.01,2.34,3.46,2.68),.012,.046,RIM,'small pale wall tablet')
    upper=rect(-WIDTH/2,4.50,WIDTH/2,HEAD)
    f.prism(upper.difference(unary_union(openings)),-.18,.012,CREAM,'balcony wall with real door and window reveals')
    for mid in (-PITCH/2,PITCH/2):
        for x in (mid-.68,mid+.68):
            f.prism(rect(x-.051,5.43,x+.051,HEAD),.012,.085,RIM,'edge of recessed window bay')
    fascia=rect(-WIDTH/2,4.55,WIDTH/2,5.40).difference(unary_union(openings))
    f.prism(fascia,.035,.117,RIM,'zigzag band background')
    marks=[]
    for k in range(-14,15):
        x=k*.62
        marks.append(LineString([(x-.30,5.17),(x,4.91),(x+.30,5.17)]).buffer(.038,cap_style=2,join_style=2))
    f.prism(unary_union(marks).intersection(fascia),.117,.166,BOARD,'raised chevrons')
    for z in (4.51,5.39):
        f.prism(rect(-WIDTH/2,z,WIDTH/2,z+.072).difference(unary_union(openings)),
                .10,.20,RIM,'course framing chevrons')
    # The photograph shows separate flat square-ended fins at the top of the three stacks.
    for axis in AXES:
        for x in (axis-.92,axis+.92):
            if not lod:f.prism(rect(x-.105,17.28,x+.105,HEAD),.014,.16,RIM,'upper pier vertical fin')
