"""South front of the former Central Trust headquarters, in facade-local metres."""
from math import cos, sin, pi
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

STONE='Trust pale artificial stone'
CARVED='Trust incised artificial stone'
BED='Trust cut joint shade'
GLAZING='Trust smoky office glass'
FRAME='Trust bronze painted steel'
ADDITION='Trust pale 1990s stone facing'
COURT='Trust pale lightwell render'
ZINC='Trust weathered grey sheet'
FLOOR='Trust warm grey terrazzo'
IRON='Trust gallery ironwork'
MATERIALS={name:{'color':rgb,'roughness':rough} for name,rgb,rough in [
    (STONE,[.63,.595,.515],.85),(CARVED,[.70,.655,.565],.78),(BED,[.34,.323,.294],.86),
    (GLAZING,[.245,.302,.298],.36),(FRAME,[.135,.144,.136],.51),(ADDITION,[.61,.585,.52],.87),
    (COURT,[.745,.747,.695],.92),(ZINC,[.39,.404,.39],.73),(FLOOR,[.59,.555,.48],.72),(IRON,[.088,.09,.083],.49)]}
AXES=(-8.55,-6.70,-4.72,-1.90,0.,1.90,4.72,6.70,8.55)
LEVELS=((7.3,9.9),(11.6,14.2),(16.0,18.1),(20.2,22.0))
UPPER_LEVELS=((24.85,26.18),(27.62,28.86))
HEIGHT=30.70
UPPER_SETBACK=.50

def rectangle(face,x,z,w,h,back,front,mat,label):
    face.box(x,z,w,h,front-back,(back+front)/2,mat,label)

def recess(face,slot,width=.10,d=.095):
    surround=slot.buffer(width,join_style='mitre').difference(slot)
    face.prism(surround,-.055,d,CARVED,'window border')

def cast_panel(face,x,z,width,height,middle,lod,top=False):
    """Raised border around an inset panel, optionally bearing the central relief."""
    field=box(x-width/2,z-height/2,x+width/2,z+height/2)
    face.prism(field,-.02,.027,BED,'relief shadow bed')
    lip=field.difference(field.buffer(-.070,join_style='mitre'))
    face.prism(lip,.025,.093,CARVED,'spandrel border')
    face.prism(field.buffer(-.083,join_style='mitre'),.023,.046,STONE,'inset stone field')
    if not middle:return
    rr=min(.19,height*.33)
    for i in range(8 if not lod else 6):
        a=2*pi*i/(8 if not lod else 6)
        points=[(x+rad*cos(a+angle),z+rad*sin(a+angle))for rad,angle in
                [(rr*.09,0),(rr*.51,-.48),(rr,-.1),(rr*.89,.21),(rr*.49,.43)]]
        face.prism(Polygon(points),.046,.105,CARVED,'fan relief on spandrel')
    if top:return
    for direction in (-1,1):
        stem=[(x+direction*(.08+t*width*.32),z-.04+.055*sin(pi*t))for t in [i/6 for i in range(7)]]
        face.prism(LineString(stem).buffer(.018,quad_segs=2),.046,.086,CARVED,'foliate spandrel stems')
        for t in (.35,.64,.85):
            u=x+direction*(.08+t*width*.32)
            leaf=Polygon([(u,z+.003),(u+direction*.12,z+.102),(u+direction*.26,z+.128),(u+direction*.16,z+.033)])
            face.prism(leaf,.048,.092,CARVED,'spandrel leaves')

def glazing(face,x,b,t,width,style,central=False):
    slot=opening(x,b,width,t-b)
    face.prism(slot.buffer(.013,join_style='mitre'),-.335,-.315,GLAZING,'glass in reveal')
    grid=slot.buffer(-.025,join_style='mitre')
    inner=grid.buffer(-.058,join_style='mitre')
    height=t-b
    levels=[t-min(.63,height*.26)]
    if style in ('bank','secondary'):levels=[b+height*.29,b+height*.69]
    bars=[box(x-width/2,z-.027,x+width/2,z+.027)for z in levels]
    if central or style=='secondary':bars.append(box(x-.029,b,x+.029,t))
    if style in ('bank','secondary'):
        # The surviving steel fanlights have crossed diagonal straps.
        panels=2 if central else 1
        for idx in range(panels):
            left=x-width/2+idx*width/panels+.065;right=x-width/2+(idx+1)*width/panels-.065
            for z0,z1 in [(levels[-1]+.04,t-.07),*([(b+.07,levels[0]-.04)]if style=='bank'else[])]:
                for a,b1 in [(left,right),(right,left)]:
                    bars.append(LineString([(a,z0),(b1,z1)]).buffer(.015,cap_style='flat'))
    face.prism(grid.difference(inner.difference(unary_union(bars))),-.27,-.206,FRAME,'steel grilles and mullions')
    if style=='secondary':
        face.box(x,(b+t)/2,.067,height,.075,-.16,FRAME,'secondary door meeting stile')
        face.box(x+.16,1.15,.036,.32,.10,-.13,IRON,'secondary door pull')
        rectangle(face,x,.045,width+.08,.09,-.52,.14,FLOOR,'secondary threshold')
    else:
        rectangle(face,x,b-.066,width+.19,.13,-.1,.164,CARVED,'projecting sill')
    return slot

def cumulative_cornice(face,rows):
    for z,h,extension,mat in rows:
        rectangle(face,0,z,face.length+.1,h,-.15,extension,mat,'continuous cornice')

def add_front(builder,lod,width,add_portal,portal_width,portal_height):
    face=Facade(builder,(0,0),(width,0),'Beijing')
    ground_holes=[box(-portal_width/2,-.03,portal_width/2,portal_height)]
    for i in (0,1,2,6,7,8):
        center=i%3==1; secondary=i==7
        x=AXES[i]; w=1.81 if center else .94
        hole=glazing(face,x,.08 if secondary else 1.04,4.86,w,'secondary'if secondary else'bank',center)
        ground_holes.append(hole);recess(face,hole,.115,.064)
        if not secondary:cast_panel(face,x,.57,w+.16,.55,False,lod)
    for x in (-6.7,6.7):
        rectangle(face,x,5.25,4.94,.46,-.045,.083,CARVED,'ground lintel panels')
    ground=box(-width/2,0,width/2,6.68)
    face.prism(ground.difference(unary_union(ground_holes)),-.52,0,STONE,'ground wall cut at three entries')
    for side in (-1,1):
        low,high=(side*(width/2-.96),side*width/2)
        for z in (.47,1.15,1.82,2.50,3.17,3.84,4.51,5.18):
            face.prism(box(min(low,high),z-.018,max(low,high),z+.018),0,.018,BED,'ashlar bed on outer pier')
    cumulative_cornice(face,[(6.10,.16,.17,CARVED),(6.24,.13,.26,BED),(6.38,.17,.36,CARVED),(6.56,.17,.52,CARVED)])
    add_portal(face,lod)
    original=[]
    for b,t in LEVELS:
        for i,x in enumerate(AXES):
            center=i%3==1;w=1.83 if center else .99
            hole=glazing(face,x,b,t,w,'office',center);original.append(hole)
        for j in range(3):
            x=AXES[j*3+1]
            # Each bay has one continuous lintel above the group of three apertures.
            rectangle(face,x,t+.115,5.32,.20,-.08,.145,CARVED,'upper three-window lintels')
    face.prism(box(-width/2,6.68,width/2,23.92).difference(unary_union(original)),-.49,0,STONE,'original four office storeys')
    for z in (10.70,15.05,19.20):
        for i,x in enumerate(AXES):
            middle=i%3==1
            cast_panel(face,x,z,2.20 if middle else 1.10,.68,middle,lod)
    for x in (-3.34,3.34):
        rectangle(face,x,14.72,.78,16.10,-.05,.10,CARVED,'tall separating piers')
        cast_panel(face,x,21.30,.68,1.25,True,lod,True)
        for sign in (-1,1):rectangle(face,x+sign*.37,14.68,.045,16.05,.08,.15,BED,'pier reveal')
    cumulative_cornice(face,[(22.65,.14,.17,CARVED),(22.87,.28,.23,STONE),(23.09,.13,.34,BED),
                             (23.29,.22,.48,CARVED),(23.52,.17,.60,STONE),(23.79,.27,.73,CARVED),(24.07,.21,.79,CARVED),
                             (24.29,.20,.88,CARVED),(24.46,.12,.94,CARVED)])
    upper=Facade(builder,(0,UPPER_SETBACK),(width,UPPER_SETBACK),'Addition')
    holes=[]
    for b,t in UPPER_LEVELS:
        for i,x in enumerate(AXES):
            center=i%3==1
            w=1.80 if center else .95
            holes.append(glazing(upper,x,b,t,w,'addition',center))
    upper.prism(box(-width/2,24.40,width/2,HEIGHT-.20).difference(unary_union(holes)),-.43,0,ADDITION,'two added storeys')
    for z in (26.58,27.14,29.51):
        rectangle(upper,0,z,width,.034,-.02,.02,BED,'added storey horizontal joints')
    cumulative_cornice(upper,[(30.28,.15,.16,BED),(30.47,.23,.28,CARVED),(30.64,.12,.35,CARVED)])
    rectangle(face,0,24.49,width,.12,-UPPER_SETBACK-.08,.90,CARVED,'top of old cornice')
