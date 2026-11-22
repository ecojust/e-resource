"""East two bays of the front gallery and its east return at 630 Huashan Road.

Metres; X follows the south face to the east, Y follows the east return to the north.
The southeast corner of the outer timber post is the local frame origin.
"""
from math import cos, pi, sin
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'brown structural timber': {'color':[.29,.25,.22],'roughness':.86},
    'weathered timber': {'color':[.39,.35,.31],'roughness':.87},
    'dark timber edge': {'color':[.22,.18,.16],'roughness':.83},
    'wooden soffit': {'color':[.65,.59,.53],'roughness':.87},
    'grey brick': {'color':[.40,.39,.39],'roughness':.93},
    'grey brick variant': {'color':[.46,.45,.43],'roughness':.92},
    'burnt red brick': {'color':[.64,.36,.25],'roughness':.90},
    'glass': {'color':[.30,.34,.36],'roughness':.34,'metallic':.16},
    'window frames': {'color':[.26,.21,.18],'roughness':.78},
    'iron': {'color':[.17,.17,.16],'roughness':.58,'metallic':.45},
    'plinth stone': {'color':[.53,.52,.49],'roughness':.92},
    'floor stone': {'color':[.63,.62,.57],'roughness':.89},
    'terracotta': {'color':[.53,.32,.24],'roughness':.91},
}

WEST=-5.24
NORTH=3.68
POSTS=(-5.11,-2.04,0.0)
GROUND=.86
FLOOR=5.08
EAVE=8.38
INNER_X=-1.93
INNER_Y=3.18

def arc_line(polyline,width):
    from shapely.geometry import LineString
    return LineString(polyline).buffer(width/2,cap_style=2,join_style=2)

def rail_panel(face, lo, hi, base, height, detail, group):
    width=hi-lo
    for z,thick in [(base+.06,.050),(base+height-.07,.040),(base+height,.063)]:
        face.box((lo+hi)/2,z,width,thick,.066,.004,'iron',group+' horizontal')
    pitches=max(3,round(width/.33))
    pieces=[]
    for i in range(pitches):
        a=lo+(i+.5)*width/pitches
        pieces.append(box(a-.012,base+.05,a+.012,base+height))
        if detail:
            pins=[(a-.103,base+.12),(a-.103,base+height-.15),
                  (a-.051,base+height-.106),(a,base+height-.16),
                  (a+.051,base+height-.106),(a+.103,base+height-.15),
                  (a+.103,base+.12),(a+.056,base+.076),
                  (a,base+.13),(a-.056,base+.076),(a-.103,base+.12)]
            pieces.append(arc_line(pins,.020))
    face.prism(unary_union(pieces),-.011,.011,'iron',group+' pickets')

def frame_bay(face,lo,hi,detail,group):
    mid=(lo+hi)/2;width=hi-lo
    for level,cap,bottom in [('lower',3.98,2.97),('upper',8.05,7.37)]:
        arm=.46 if level=='lower' else .38
        stay=unary_union([arc_line([(lo+.075,bottom),(lo+arm,cap)],.085),
                          arc_line([(hi-.075,bottom),(hi-arm,cap)],.085)])
        face.prism(stay,-.066,.066,'brown structural timber',group+' '+level+' diagonal stays')
        face.box(mid,cap+.043,width,.090,.15,0,'brown structural timber',group+' '+level+' head rail')
        if detail and level=='upper':
            for pos,sign in [(lo,1),(hi,-1)]:
                face.box(pos+sign*.36,7.93,.049,.29,.092,-.002,'weathered timber',group+' hanging peg')
                shaped=[(pos+sign*.11,8.025),(pos+sign*.47,8.025),
                        (pos+sign*.31,7.91),(pos+sign*.27,7.91),
                        (pos+sign*.17,7.80),(pos+sign*.11,7.76)]
                insert=Polygon(shaped).difference(Point(pos+sign*.24,7.927).buffer(.050,quad_segs=10))
                face.prism(insert,-.040,.041,'weathered timber',group+' pierced spandrel')
    for z,height,material in [(4.025,.11,'weathered timber'),(4.81,.19,'weathered timber'),(4.98,.15,'dark timber edge')]:
        face.box(mid,z,width,height,.15,.012,material,group+' fascia')
    face.box(mid,4.45,width,.70,.085,-.046,'dark timber edge',group+' recessed fascia')
    for j in range(6 if detail else 3):
        z=4.14+j*(.103 if detail else .205)
        face.box(mid,z,width,.059 if detail else .12,.095,.015,'weathered timber',group+' louvre boards')
    if detail:
        num=max(2,round(width/.79))
        for j in range(1,num):
            face.box(lo+width*j/num,4.43,.048,.70,.12,.045,'brown structural timber',group+' louvre battens')
    rail_panel(face,lo+.081,hi-.081,GROUND,.91,detail,group+' ground')
    rail_panel(face,lo+.084,hi-.084,FLOOR,1.02,detail,group+' upper')

def masonry(builder, detail):
    face=Facade(builder,(-6.0,INNER_Y),(6.0,INNER_Y),'inset brick wall')
    limits=box(WEST,GROUND,INNER_X,7.99)
    holes=[box(-4.58,.93,-3.64,3.34),box(-4.53,5.16,-3.64,7.26)]
    face.prism(limits.difference(unary_union(holes)),-.22,0,'grey brick','two storeys')
    for idx,(opening,lintel) in enumerate(zip(holes,[3.34,7.26])):
        x0,z0,x1,z1=opening.bounds;px=(x0+x1)/2
        face.prism(opening.buffer(.006,join_style=2),-.186,-.175,'glass','dark opening '+str(idx))
        for z in ([z0+.10,z0+.75*(z1-z0),z1] if detail else [z0+.10,z1]):
            face.box(px,z,x1-x0,.051,.062,-.121,'window frames','sash top bottom')
        for x in (x0+.024,px,x1-.024):
            face.box(x,(z0+z1)/2,.048,z1-z0,.072,-.129,'window frames','sash uprights')
        face.box(px,lintel+.111,x1-x0+.18,.228,.092,.018,'burnt red brick','flat brick lintel')
        if detail:
            for j in range(8):
                face.box(x0-.052+j*(x1-x0+.1)/7,lintel+.11,.012,.208,.015,.068,'grey brick variant','lintel joints')
    for z in (1.16,2.67,5.47,7.76):
        strip=box(WEST,z-.09,INNER_X,z+.09).difference(unary_union(holes))
        face.prism(strip,.003,.019,'burnt red brick','horizontal brick courses')
    for level in range(18 if detail else 9):
        z=GROUND+(level+.5)*(7.99-GROUND)/(18 if detail else 9)
        width=.34 if level%2 else .24
        face.box(INNER_X-width/2,z,width,(7.99-GROUND)/(18 if detail else 9)-.009,.040,.005,'burnt red brick','corner quoins')
    east=Facade(builder,(INNER_X,INNER_Y-6),(INNER_X,INNER_Y+6),'return inner corner')
    east.prism(box(0,GROUND,NORTH-INNER_Y,7.99),-.21,0,'burnt red brick','corner brick return')
    if detail:
        for row in range(52):
            z=GROUND+.14*row
            if z>=7.98:break
            for j in range(3):
                x=WEST+.18+.80*j+(.27 if row%2 else 0)
                pane=box(x,z,x+.28,z+.061).intersection(limits).difference(unary_union(holes))
                if pane.area>.001:face.prism(pane,.001,.008,'grey brick variant','burnt scatter')

def add_building(builder,lod=False):
    detail=not lod
    south=Facade(builder,(-6,0),(6,0),'south')
    east=Facade(builder,(0,-5),(0,5),'east')
    slab=box(WEST,-.095,.107,NORTH)
    # The raised porch has a pierced foundation along both street-visible edges.
    for face,a,b,side in [(south,WEST,.105,'south'),(east,-.095,NORTH,'east')]:
        wall=box(a,.035,b,GROUND-.095)
        pitch=.85 if side=='east' else 1.01
        centers=[a+.43+i*pitch for i in range(int((b-a-.45)/pitch)+1)]
        voids=unary_union([Point(x,.43).buffer(.147,quad_segs=12 if detail else 6)for x in centers if x+.18<b])
        face.prism(wall.difference(voids),-.145,0,'plinth stone','vented plinth')
        face.prism(voids,-.250,-.245,'dark timber edge','vent cavity')
        face.box((a+b)/2,GROUND-.058,b-a,.115,.20,.010,'floor stone','foundation coping')
    for z,thickness,label,mat in [(GROUND-.045,.09,'lower porch floor','floor stone'),(FLOOR-.115,.23,'gallery floor','weathered timber'),(8.055,.11,'gallery ceiling','wooden soffit')]:
        builder.prism(slab,z-thickness/2,z+thickness/2,lambda x,y,t:(x,y,t),mat,label)
    for n,(x,y) in enumerate([(i,0)for i in POSTS]+[(0,3.37)]):
        for z0,z1,w,mat,label in [(GROUND,FLOOR-.10,.174,'brown structural timber','lower post'),(FLOOR-.12,8.13,.158,'brown structural timber','upper post'),(GROUND-.012,GROUND+.102,.248,'floor stone','post shoe'),(7.98,8.13,.22,'weathered timber','capital')]:
            builder.box((x,y,(z0+z1)/2),(w,w,z1-z0),mat,label=label+' '+str(n))
    for i,(lo,hi) in enumerate(zip(POSTS,POSTS[1:])):frame_bay(south,lo,hi,detail,'bay '+str(i+1))
    frame_bay(east,0,3.37,detail,'first bay')
    masonry(builder,detail)
    for face,lo,hi in [(south,WEST,.16),(east,-.16,NORTH)]:
        for z,h,w,mat in [(8.16,.16,.27,'weathered timber'),(8.28,.12,.34,'dark timber edge'),(8.365,.10,.39,'terracotta')]:
            face.box((lo+hi)/2,z,hi-lo,h,w,.045,mat,'projecting eave')
    # The gallery has a shallow canopy, meeting the main roof toward the brick backing.
    x0,x1,y0,y1=WEST,.205,-.205,NORTH
    verts=[(x0,y0,8.386),(x1,y0,8.386),(x1,y1,8.386),(INNER_X,y1,8.755),(INNER_X,INNER_Y,8.755),(x0,INNER_Y,8.755)]
    for label,ids in [('front canopy',(0,1,4,5)),('east canopy',(1,2,3,4))]:
        poly=[verts[i]for i in ids]
        n=len(poly);both=poly+[(x,y,z-.08)for x,y,z in poly]
        builder.add(both,[tuple(range(n)),tuple(reversed(range(n,2*n))),*[(j+n,(j+1)%n+n,(j+1)%n,j)for j in range(n)]],'terracotta',label)
