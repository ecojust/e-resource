"""The conserved block's contemporary roof and its distinct December 2018 study."""
from shapely.geometry import box
from gongyi_materials import RIDGE, STONE, TILE, TRIM, paint

PANEL='Gongyi 3 | grey blue roof panels'
JOINT='Gongyi 3 | dark roof joints'
PAVING='Gongyi 3 | buff roof terrace'
PALE='Gongyi 3 | light grey roof covers'
DARK='Gongyi 3 | charcoal roof field'
PALETTE={PANEL:paint((116,133,140),.65,.16),JOINT:paint((73,80,79),.81,.13),
         PAVING:paint((159,137,120),.92),PALE:paint((155,160,153),.91),DARK:paint((88,88,79),.92)}


def facet(b, top, thickness, material, name):
    # Each sloping facet has a closed underside and side walls, even at the hip.
    # All input rings are checked in XY before extrusion.
    a=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(top,top[1:]+top[:1]))
    if a<0:top=list(reversed(top))
    n=len(top);verts=top+[(x,y,z-thickness) for x,y,z in top]
    faces=[tuple(range(n)),tuple(reversed(range(n,n*2)))]
    faces.extend((j,n+j,n+(j+1)%n,(j+1)%n) for j in range(n))
    b.add(verts,faces,material,name)


def raised_strip(b, length, eave, lod):
    front=.45;back=4.54;middle=2.45
    start=.20;end=length-.20;rise=1.02;hip=.72
    a=(start,front,eave);b0=(end,front,eave);c=(end,back,eave);d=(start,back,eave)
    r=(start+hip,middle,eave+rise);s=(end-hip,middle,eave+rise)
    for name,verts in [('street',[a,b0,s,r]),('terrace',[s,c,d,r]),('south',[d,a,r]),('north',[b0,c,s])]:
        facet(b,verts,.085,PANEL,'Raised roof | '+name)
    for name,points in [('cap',[r,s]),('south edge',[a,r,d]),('north edge',[b0,s,c])]:
        b.tube(points,.037 if name=='cap' else .026,JOINT,6 if lod else 9,'Raised roof | '+name)
    # The post-repair architect's photograph shows a regular seam pattern
    # across the street slope. The backside repetitions are an inference.
    count=round((end-start)/1.19)
    for i in range(1,count):
        x=start+i*(end-start)/count
        if start+hip<=x<=end-hip:
            b.tube([(x,front,eave+.012),(x,middle,eave+rise+.012)],.012,JOINT,5 if lod else 7,'Raised roof | street joint')
            if not lod:
                b.tube([(x,middle,eave+rise+.012),(x,back,eave+.012)],.013,JOINT,6,'Raised roof | terrace joint')


def contemporary(b,lod,layout):
    length=layout['bay_edges'][-1];depth=layout['rear_depth'];h=layout['street_cornice_z']
    # Aerial features are recorded as roof surfaces. Their uses and absolute
    # heights cannot be recovered from the straight-down photographs.
    b.plan_prism(box(.045,.12,length-.045,depth),h-.36,h-.19,PAVING,'Terrace surface')
    raised_strip(b,length,h+.03,lod)
    b.box((length/2,4.80,h-.125),(length-.18,.21,.18),PALE,label='Kerb parallel to street')
    # Ratios refer to the same front span measured on the two recent overhead views.
    for name,lo,hi,front,back,top,material in [
        ('southern light cover',.084,.231,.466,.985,.31,PALE),
        ('southern dark field',.231,.327,.456,.982,.26,DARK),
        ('northern dark surround',.683,.872,.459,.982,.24,DARK),
        ('northern light cover',.872,.989,.481,.979,.32,PALE),
        ('northern inset rectangles',.711,.847,.792,.966,.29,PALE),
    ]:
        f=box(length*lo,depth*front,length*hi,depth*back)
        b.plan_prism(f,h-.18,h+top,material,'Terrace | '+name)
    # The April 2025 orthophoto separates two pale bands with a dark gap.
    # Panel seams are legible only in the rear band.
    b.plan_prism(box(33.1,7.2,38.6,9.15),h+.241,h+.294,PALE,
                 'Terrace | streetward northern inset')
    for i in range(1,4):
        x=length*(.711+.136*i/4)
        b.box((x,.879*depth,h+.297),(.036,.174*depth,.018),JOINT,label='Northern roof | longitudinal joint')
    b.box((length*.779,depth*.879,h+.297),(.136*length,.040,.018),JOINT,label='Northern roof | transverse joint')
    for name,shape in [('rear',box(0,depth-.12,length,depth)),
                       ('south',box(0,.19,.14,depth)),('north',box(length-.14,.19,length,depth))]:
        b.plan_prism(shape,h-.20,h+.13,STONE,'Roof parapet | '+name)


def december_2018(b,lod,layout):
    length=layout['bay_edges'][-1];depth=layout['rear_depth'];z=layout['street_cornice_z']-.44
    y0=.3;y1=6.7;middle=3.65
    for side,y in [('street',y0),('yard',y1)]:
        facet(b,[(.10,y,z),(length-.10,y,z),(length-.10,middle,z+1.12),(.10,middle,z+1.12)],.10,TILE,'2018 | '+side+' pitch')
    for name,lo,hi in [('south',.015,.359),('middle',.436,.551),('north',.650,.904)]:
        x0,x1=lo*length,hi*length;x=(x0+x1)*.5;ridge=z+1.65 if name!='middle' else z+1.06
        for side,edge in [('south',x0),('north',x1)]:
            facet(b,[(edge,middle,z),(x,middle,ridge),(x,depth,ridge),(edge,depth,z)],.10,TILE,'2018 return | '+name+' '+side)
        b.tube([(x,middle,ridge),(x,depth,ridge)],.072,RIDGE,7 if lod else 12,'2018 return | '+name+' ridge')
    b.tube([(.10,middle,z+1.12),(length-.10,middle,z+1.12)],.078,RIDGE,7 if lod else 12,'2018 | street ridge')
