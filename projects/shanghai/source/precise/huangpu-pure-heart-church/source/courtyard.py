"""Brick sanctuary facades and stair balcony around the re-entrant northeast court."""
from math import ceil, cos, pi, sin, sqrt
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from sign_lettering import lettering_shapes

BRICK='russet face brick'
ARCH='red arch brick'
MORTAR='shadowed bed joint'
STONE='washed grey stone'
CAP='pale cement cap'
WOOD='chestnut sash'
DARK='deep opening'
GLASS='brown violet glazing'
AMBER='amber glass'
TILE='weathered roof tile'
METAL='dark roof drainage'
GOLD='gilt tablet lettering'
PALETTE={
 BRICK:{'color':[.50,.292,.219],'roughness':.92},ARCH:{'color':[.405,.202,.163],'roughness':.90},
 MORTAR:{'color':[.366,.265,.221],'roughness':.96},STONE:{'color':[.51,.511,.473],'roughness':.93},
 CAP:{'color':[.69,.672,.60],'roughness':.88},WOOD:{'color':[.24,.132,.112],'roughness':.79},
 DARK:{'color':[.104,.092,.085],'roughness':.90},GLASS:{'color':[.205,.177,.190],'metallic':.12,'roughness':.37},
 AMBER:{'color':[.43,.243,.132],'metallic':.08,'roughness':.34},TILE:{'color':[.273,.217,.192],'roughness':.89},
 METAL:{'color':[.19,.185,.169],'metallic':.30,'roughness':.62},GOLD:{'color':[.68,.505,.254],'metallic':.53,'roughness':.43}
}
EAVE=7.38
LEVEL=3.06
LAND_END=4.36
STAIR_SIDE=1.40
RUN=4.93
RISERS=17
ARM_N=11.00
ARM_E=12.36
RELIEF=1.22

def point(e,n):
    """Source concave corner at (0,0); +X northwest, +Y southwest into church."""
    return ((n-e)/sqrt(2),-(e+n)/sqrt(2))

def area(points):
    return Polygon([point(e,n) for e,n in points])

def face(builder,a,b,label):
    return Facade(builder,point(*a),point(*b),label)

def arch(u,sill,width,top,rise,detail=22):
    r=width/2;spring=top-rise
    curve=[(u+r*cos(pi*i/detail),spring+rise*sin(pi*i/detail)) for i in range(detail+1)]
    return Polygon([(u-r,sill),(u+r,sill),*curve])

def radial_header(f,u,spring,r,rise,lod,label):
    # Individual wedge-shaped arch bricks follow the shallow ellipse, including its springing.
    count=13 if lod else 23
    for i in range(count):
        a=(i+.10)*pi/count;b=(i+.90)*pi/count
        poly=Polygon([(u+r*cos(a),spring+rise*sin(a)),(u+(r+.18)*cos(a),spring+(rise+.18)*sin(a)),
                      (u+(r+.18)*cos(b),spring+(rise+.18)*sin(b)),(u+r*cos(b),spring+rise*sin(b))])
        f.prism(poly,.003,.048,ARCH,label+' arch voussoirs')

def add_window(f,u,sill,width,top,rise,major,lod,label):
    r=width/2;spring=top-rise
    opening=arch(u,sill,width,top,rise,16 if lod else 30)
    f.prism(opening.buffer(.017),-.265,-.245,GLASS,label+' glass')
    outer=opening.buffer(-.020,join_style=2)
    inner=opening.buffer(-(.104 if major else .079),join_style=2)
    trellis=[]
    for fraction in ([1/3,2/3] if major else [.5]):
        x=u-r+width*fraction
        trellis.append(box(x-.039,sill-.02,x+.039,spring+.02))
    rows=(6 if not lod else 4) if major else (4 if not lod else 3)
    for k in range(1,rows+1):
        z=sill+(spring-sill)*k/rows
        trellis.append(box(u-r,z-.033,u+r,z+.033))
    # The two curved mullions rise from the spring transom to the arch, visible in the angled photograph.
    if major:
        for s in (-1,1):
            path=LineString([(u+s*r/3,spring),(u+s*r*.34,spring+rise*.39),
                             (u+s*r*.47,spring+rise*.71),(u+s*r*.67,spring+rise*.89)])
            trellis.append(path.buffer(.039,cap_style=2,join_style=2))
        for k in (0,2):
            x=u-r+width*(k+.5)/3
            row=rows//2
            amber=box(x-width/6-.003,sill+(spring-sill)*row/rows,
                      x+width/6+.003,sill+(spring-sill)*(row+1)/rows).intersection(inner)
            f.prism(amber,-.239,-.234,AMBER,label+' warm glazing')
    grid=outer.difference(inner.difference(unary_union(trellis)))
    f.prism(grid,-.18,-.092,WOOD,label+' timber window grid')
    trim=opening.buffer(.15,join_style=2).difference(opening)
    f.prism(trim,-.012,.035,BRICK,label+' recessed brick reveal')
    radial_header(f,u,spring,r,rise,lod,label)
    f.box(u,sill-.068,width+.23,.135,.28,.03,CAP,label+' projecting sill')

def courses(f,surface,lod):
    # Narrow bed joints stay on intact brickwork. Heads, sills, glazing and doors are cut out.
    inset=surface.buffer(-.028,join_style=2)
    result=[];pitch=.245 if lod else .113
    for i in range(1,ceil(EAVE/pitch)):
        z=i*pitch
        stripe=box(-f.length/2+.01,z-.0045,f.length/2-.01,z+.0045).intersection(inset)
        if not stripe.is_empty:result.append(stripe)
    if result:f.prism(unary_union(result),.0012,.0058,MORTAR,'brick bed joints')

def add_wing(builder,north,lod):
    title='North wing' if north else 'East wing'
    length=ARM_N if north else ARM_E
    f=face(builder,(0,0),(0,length),title) if north else face(builder,(length,0),(0,0),title)
    station=lambda along:along-length/2 if north else length/2-along
    # Stations along the two perpendicular courtyard walls, from the common inside corner.
    windows=[(2.61,3.03,1.17,5.94,.57,False),(8.03,1.49,3.24,6.38,1.10,True)] if north else [
        (1.86,3.12,1.05,5.63,.53,False),(4.59,3.03,1.25,5.94,.60,False),
        (9.21,1.48,2.73,6.18,.97,True)]
    holes=[arch(station(s),sill,w,top,rise,16 if lod else 30)for s,sill,w,top,rise,major in windows]
    lower=box(station(8.55)-.49,.21,station(8.55)+.49,1.33) if north else None
    if lower is not None:holes.append(lower)
    surface=f.wall(0,EAVE,holes,thickness=.51,material=BRICK)
    courses(f,surface,lod)
    base=box(-length/2,0,length/2,.35)
    if lower is not None:base=base.difference(lower)
    f.prism(base,.006,.074,STONE,'base plinth')
    if lower is not None:
        f.prism(lower.buffer(.015),-.186,-.153,WOOD,'low secondary opening')
        f.prism(lower.buffer(.093,join_style=2).difference(lower),.013,.080,CAP,'pale lower door frame')
    for i,(s,sill,w,top,rise,major) in enumerate(windows):
        add_window(f,station(s),sill,w,top,rise,major,lod,'large arched window' if major else 'upper arched bay '+str(i+1))
    for s in ([.25,5.54,length-.29] if north else [.27,3.18,6.54,length-.36]):
        u=station(s);f.box(u,3.80,.37,7.12,.19,.058,BRICK,'flat brick pilaster')
        f.box(u,.32,.45,.62,.25,.078,STONE,'pilaster base')
        f.box(u,EAVE-.22,.47,.22,.29,.09,CAP,'pilaster pale capital')
    f.box(0,EAVE-.105,length+.1,.20,.27,.055,WOOD,'dark fascia board')
    # Only the near roof strip is reconstructed. Its high, rear edge is a section.
    roof=Polygon([(-length/2-.12,EAVE),(length/2+.12,EAVE),(length/2+.12,EAVE+.13),(-length/2-.12,EAVE+.13)])
    def roof_point(u,z,depth):
        return f.point(u,z-depth*.26,depth)
    builder.prism(roof,-RELIEF,.19,roof_point,TILE,title+'/roof strip')
    f.line((-length/2,EAVE-.06,.22),(length/2,EAVE-.06,.22),.061,METAL,8,'half-round eave gutter')
    f.line((station(length*.48),.41,.145),(station(length*.48),EAVE-.10,.145),.054,METAL,8,'down pipe')
    if not lod:
        for i in range(1,ceil(length/.25)):
            u=-length/2+i*.25
            if u>=length/2:break
            f.line((u,EAVE+.085,.16),(u,EAVE+.13+RELIEF*.26,-RELIEF),.023,TILE,6,'roof tile seam')
    # Plain return at the verified end separates the modeled garden wall from the retained city mass.
    ret=face(builder,(0,length),(-RELIEF,length),title+' end') if north else face(builder,(length,-RELIEF),(length,0),title+' end')
    ret.wall(0,EAVE,thickness=.22,material=BRICK)
    ret.box(0,.23,RELIEF,.46,.20,.012,STONE,'end plinth')
    return f

def stair(builder,north):
    lab='north stair' if north else 'east stair'
    pos=(lambda cross,along:(cross,along)) if north else (lambda cross,along:(along,cross))
    def footprint(a,b,t0,t1):return area([pos(a,t0),pos(b,t0),pos(b,t1),pos(a,t1)])
    far=LAND_END+RUN;step=RUN/RISERS;rise=LEVEL/RISERS
    for i in range(RISERS):
        along=LAND_END+i*step;z=LEVEL-i*rise
        tread=footprint(.09,STAIR_SIDE,along,along+step)
        builder.plan_prism(tread,0,z,STONE,lab+'/seventeen treads')
        nose=footprint(.09,STAIR_SIDE+.015,along+step-.050,along+step+.025)
        builder.plan_prism(nose,z-.050,z+.009,CAP,lab+'/stone nosings')
    # Solid outer strings are visibly battered plaster parapets; the photographed staircase has no iron fence.
    rail=face(builder,pos(STAIR_SIDE,LAND_END),pos(STAIR_SIDE,far),lab+' outer balustrade')
    if not north:rail=face(builder,pos(STAIR_SIDE,far),pos(STAIR_SIDE,LAND_END),lab+' outer balustrade')
    l=rail.length/2;upper,bottom=(LEVEL+.76,.76)if north else(.76,LEVEL+.76)
    side=Polygon([(-l,0),(l,0),(l,bottom),(-l,upper)])
    rail.prism(side,-.12,.11,STONE,'solid sloping parapet')
    coping=Polygon([(-l,upper-.045),(l,bottom-.045),(l,bottom+.060),(-l,upper+.060)])
    rail.prism(coping,-.15,.15,CAP,'sloped coping')
    u=l if north else -l;rail.box(u,.43,.31,.86,.34,.005,STONE,'square stair foot')
    rail.box(u,.875,.35,.075,.37,.005,CAP,'foot cap')

def entrance(builder,lod):
    # Solid floor lies above the entrance tunnel. Keep the aperture genuinely empty at walking height.
    deck=area([(0,0),(LAND_END,0),(LAND_END,STAIR_SIDE),(STAIR_SIDE,LAND_END),(0,LAND_END)])
    builder.plan_prism(deck,LEVEL-.19,LEVEL,STONE,'landing/upper floor')
    front=face(builder,(LAND_END,STAIR_SIDE),(STAIR_SIDE,LAND_END),'central portal')
    width=front.length;opening=arch(0,0,1.90,2.56,.50,22)
    surf=front.wall(0,LEVEL-.145,[opening],thickness=.45,material=BRICK)
    courses(front,surf,lod)
    head=opening.buffer(.175,join_style=2).difference(opening).intersection(box(-1.18,.02,1.18,2.85))
    front.prism(head,.006,.055,ARCH,'brick archivolt')
    radial_header(front,0,2.06,.95,.50,lod,'central shallow arch')
    # Vestibule ends at the documented depth of the relief, with a plain dark section.
    for sign in (-1,1):
        front.box(sign*1.01,1.37,.13,2.74,1.33,-1.03,BRICK,'tunnel side wall')
    front.prism(box(-1.13,0,1.13,2.68),-1.78,-1.74,DARK,'vestibule section')
    for sign in (-1,1):
        front.box(sign*(width/2-.16),.41,.34,.82,.50,.025,STONE,'brick portal base')
    front.box(0,LEVEL+.43,width,.86,.26,-.01,STONE,'balcony front')
    front.box(0,LEVEL+.44,width-.16,.686,.095,.153,CAP,'inscription tablet')
    front.box(0,LEVEL+.889,width+.11,.115,.42,.02,CAP,'balcony coping')
    plaque=Path(__file__).with_name('fonts')/'DachangCourtyardPlaque.otf'
    for glyph,poly in lettering_shapes('清心堂',2.32,.43,font=plaque):
        front.prism(translate(poly,yoff=LEVEL+.445),.197,.235,GOLD,'three separately extruded characters '+glyph)
    for north in (True,False):
        stair(builder,north)
    return front

def add_courtyard(builder,lod):
    add_wing(builder,True,lod)
    add_wing(builder,False,lod)
    # Join the two intersecting roof strips at their interior diagonal. Each triangle
    # has the exact slope and height of the contiguous wing plane at its seam.
    for coords in [[(0,0),(-RELIEF,0),(-RELIEF,-RELIEF)],[(0,0),(-RELIEF,-RELIEF),(0,-RELIEF)]]:
        levels=[EAVE+.13+.26*max(-e,-n) for e,n in coords]
        points=[(*point(e,n),z) for (e,n),z in zip(coords,levels)]
        vertices=points+[(x,y,z-.13)for x,y,z in points]
        builder.add(vertices,[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],TILE,'Joined roof valley')
    entrance(builder,lod)
