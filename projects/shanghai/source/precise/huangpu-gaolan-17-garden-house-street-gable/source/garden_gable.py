"""The street gable recorded behind the No. 17 stone gatepost.

Metres. X runs to the right of a person facing the house; Y runs into the
house. Geometry stops at the short roof and side-wall section that joins the
retained original building. The low oriel has three separately glazed faces.
"""
from math import atan2, cos, pi, sin, sqrt
from random import Random
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

ROUGH='Grey pebble-dash'; GRIT='Aggregate grains'; BASE='Pale plinth'; BOARD='Weathered dark timber'
SHUTTER='Red-brown louvers'; FRAME='Casing and shutter frames'; GLASS='Shaded glazing'
TILE='Dark terracotta tiles'; RIDGE='Terracotta ridge caps'; BRICK='Salmon brick arch'; GUTTER='Dark rainwater goods'
MATERIALS={name:dict(color=rgb,roughness=rough)for name,rgb,rough in [
 (ROUGH,[.426,.414,.382],.97),(GRIT,[.528,.511,.463],.97),(BASE,[.639,.609,.537],.91),
 (BOARD,[.206,.166,.141],.89),(SHUTTER,[.346,.162,.115],.81),(FRAME,[.262,.137,.103],.78),
 (GLASS,[.158,.162,.150],.41),(TILE,[.284,.204,.171],.92),(RIDGE,[.443,.236,.172],.90),
 (BRICK,[.593,.380,.300],.89),(GUTTER,[.226,.210,.179],.83)]}
HALF=2.94
EAVE=7.54
PEAK=10.91
DEPTH=6.15

def cube(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)

def raised_line(f,p0,p1,width,back,front,mat,label):
    f.prism(LineString([p0,p1]).buffer(width/2,cap_style=2),back,front,mat,label)

def material_patch(f,surface,lod):
    """A fraction of the stones stand proud; the wall still reads as render at distance."""
    rng=Random(1709)
    verts=[];faces=[]
    x0,z0,x1,z1=surface.bounds
    for _ in range(190 if lod else 3900):
        x,z=rng.uniform(x0,x1),rng.uniform(z0,z1)
        if not surface.contains(Point(x,z)):continue
        dx=rng.uniform(.011,.037);dz=rng.uniform(.009,.031);p=len(verts)
        verts.extend([f.point(x-dx,z-dz*.25,.0015),f.point(x+dx*.55,z-dz,.0015),
                      f.point(x+dx,z+dz*.8,.002),f.point(x-dx*.18,z+dz*.27,rng.uniform(.008,.024))])
        faces.extend([(p,p+1,p+3),(p+1,p+2,p+3),(p+2,p,p+3)])
    if verts:f.builder.add(verts,faces,GRIT,f.label+'/Pebble aggregate')

def offcenter_front():
    return Polygon([(-HALF,.025),(HALF,.025),(HALF,EAVE),(-.12,PEAK),(-HALF,EAVE)])

def shutters(f,c,z,w,h,lod,label,depth=0):
    # The December picture shows the leaves together. In April four open leaves
    # expose the two sash windows; this model uses the closed photographed state.
    opening=box(c-w/2,z,c+w/2,z+h)
    f.prism(opening,depth-.178,depth-.157,GLASS,label+' glazing')
    outer=opening.difference(opening.buffer(-.045,join_style=2))
    f.prism(outer,depth-.135,depth+.013,FRAME,label+' casing')
    for j in (-1,1):
        center=c+j*w*.238;ow=w*.455
        leaf=box(center-ow/2,z+.044,center+ow/2,z+h-.044)
        f.prism(leaf,depth-.081,depth-.052,SHUTTER,label+' leaves')
        frame=leaf.difference(leaf.buffer(-.043,join_style=2))
        f.prism(frame,depth-.051,depth+.002,FRAME,label+' leaf edges')
        if not lod:
            n=max(7,int(h/.075))
            for k in range(1,n):
                height=z+.058+(k/n)*(h-.116)
                f.prism(box(center-ow/2+.05,height-.013,center+ow/2-.05,height+.012),
                        depth-.05,depth-.017,SHUTTER,label+' slats')
        f.prism(box(center-ow/2+.03,z+h*.49-.027,center+ow/2-.03,z+h*.49+.027),
                depth-.045,depth-.005,FRAME,label+' mid rail')
    f.prism(box(c-w/2-.072,z-.077,c+w/2+.072,z-.012),depth-.033,depth+.143,BASE,label+' sill')

def tile_plane(b,corners,label,lod):
    p,q,r,s=corners
    indices=[(0,1,2),(0,2,3)] if (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])>0 else [(0,2,1),(0,3,2)]
    b.add(corners,indices,TILE,label+' field')
    def part(t,u):
        return tuple((1-u)*((1-t)*p[i]+t*q[i])+u*((1-t)*s[i]+t*r[i]) for i in range(3))
    width=sqrt(sum((p[i]-q[i])**2 for i in range(3)));fall=sqrt(sum((p[i]-s[i])**2 for i in range(3)))
    count=max(3,round(fall/(.44 if lod else .24)));n=max(4,round(width/(.70 if lod else .235)))
    for row in range(count):
        offset=row/count
        if not lod:
            a=part(0,offset);z=part(1,offset)
            b.tube([a,z],.017,TILE,5,label+' lap edges')
        for col in range(n):
            t=(col+.5*(row%2))/n
            a=list(part(t,offset));z=list(part(t,(row+1)/count));a[2]+=.009;z[2]+=.013
            b.tube([a,z],.018 if lod else .022,TILE,4 if lod else 6,label+' roll joints')

def roof(b,front,lod):
    outer=3.24;e=7.50;z=11.00;front_y=-.39;back=DEPTH
    for side,sign in [('East',-1),('West',1)]:
        x=sign*outer
        tile_plane(b,[(x,front_y,e),(x,back,e),(-.12,back,z),(-.12,front_y,z)],side+' pitch',lod)
        barge=LineString([(x,e),(-.12,z)]).buffer(.111,cap_style=2)
        front.prism(barge,.18,.421,BOARD,side+' bargeboard')
        b.tube([(x,front_y,e-.14),(x,back,e-.14)],.074,GUTTER,8 if lod else 12,side+' eaves gutter')
        for i in range(6):
            y=.25+i*.86
            b.add([(sign*HALF,y-.046,e-.38),(x,y-.046,e-.15),(sign*HALF,y-.046,e-.13),
                   (sign*HALF,y+.046,e-.38),(x,y+.046,e-.15),(sign*HALF,y+.046,e-.13)],
                  [(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],BOARD,side+' rafter feet')
    segments=5 if lod else 17
    for i in range(segments):
        y0=front_y+(back-front_y)*i/segments;y1=front_y+(back-front_y)*(i+1)/segments
        b.tube([(-.12,y0,z+.03),(-.12,y1,z+.03)],.061,RIDGE,8,'Clay ridge caps')

def oriel(b,front,lod):
    points=[(-1.23,0),(-.89,-.455),(.89,-.455),(1.23,0)]
    footprint=Polygon(points+[(-1.23,0)])
    b.prism(footprint,.74,.85,lambda x,y,z:(x,y,z),BASE,'Oriel stone apron')
    for i,(p,q) in enumerate(zip(points,points[1:])):
        f=Facade(b,p,q,'Oriel '+str(i+1))
        w=f.length
        casing=box(-w/2,.85,w/2,2.82).difference(box(-(w-.062)/2,.95,(w-.062)/2,2.67))
        f.prism(casing,-.055,0,FRAME,'Wood casing')
        shutters(f,0,.95,w-.062,1.72,lod,'Bay')
    corners=[(-1.40,.085,2.87),(-1.00,-.60,2.86),(1.00,-.60,2.86),(1.40,.085,2.87)]
    e,f,g,h=corners;top_left=(-.50,.075,3.39);top_right=(.50,.075,3.39)
    b.add([e,f,g,h,top_left,top_right],[(0,1,4),(1,2,5,4),(2,3,5)],TILE,'Oriel hipped hood')
    for p,q in [(e,f),(f,g),(g,h)]:
        b.tube([p,q],.052,BOARD,6,'Oriel lower fascia')
    for p,q in [(f,top_left),(g,top_right),(top_left,top_right)]:
        b.tube([p,q],.046,RIDGE,6,'Oriel hip rolls')
    for i in range(5 if lod else 14):
        t=(i+.5)/(5 if lod else 14);x=-1+2*t
        b.tube([(x,-.60,2.875),(x*.50,.075,3.402)],.021,TILE,5,'Oriel tile laps')

def brick_arc(front,lod):
    # A shallow segmental relieving arch is flush with the roughcast wall. It
    # is intentionally separated from the smaller hipped hood below it.
    span=1.36;rise=.25;base=3.92;radius=(span*span+rise*rise)/(2*rise);cz=base+rise-radius
    angle=atan2(span,radius-rise);n=12 if lod else 29
    for i in range(n):
        lo=-angle+2*angle*(i+.025)/n;hi=-angle+2*angle*(i+.975)/n
        pts=[(rr*sin(a),cz+rr*cos(a))for a,rr in [(lo,radius),(hi,radius),(hi,radius+.125),(lo,radius+.125)]]
        front.prism(Polygon(pts),.001,.032,BRICK,'Segmental brick relieving arch')

def add_building(b,lod=False):
    front=Facade(b,(-HALF,0),(HALF,0),'Gable')
    pane=[box(c-.49,5.09,c+.49,6.72) for c in (-.655,.655)]
    attic=box(-.48,8.56,.27,9.52)
    small=box(-1.82,1.49,-1.44,2.52)
    foot=box(-1.21,.73,1.21,2.80)
    holes=pane+[attic,small,foot]
    surface=front.wall(.025,PEAK,holes,.21,ROUGH,outline=offcenter_front())
    material_patch(front,surface.buffer(-.045),lod)
    front.prism(box(-HALF,.03,HALF,.325),.003,.038,BASE,'Ground plinth')
    for j,c in enumerate((-.655,.655)):
        shutters(front,c,5.09,.98,1.63,lod,'Paired upper '+str(j+1))
    shutters(front,-.105,8.56,.75,.96,lod,'Attic')
    shutters(front,-1.63,1.49,.38,1.03,lod,'Small side sash')
    trim=offcenter_front().intersection(box(-HALF,EAVE-.035,HALF,PEAK))
    front.prism(box(-HALF,EAVE-.085,HALF,EAVE+.073),.006,.079,BOARD,'Gable tie')
    for x in [-2.04,-1.35,-.52,.31,1.14,1.96]:
        timber=trim.intersection(box(x-.063,EAVE,x+.063,PEAK-.02)).difference(attic)
        front.prism(timber,.006,.072,BOARD,'Exposed vertical timbers')
    for name,x,sgn in [('East',-HALF,-1),('West',HALF,1)]:
        p,q=((x,DEPTH),(x,0)) if sgn<0 else ((x,0),(x,DEPTH))
        f=Facade(b,p,q,name+' return')
        side_window=box(-1.59,5.1,-.45,6.71)
        lo=box(-1.57,1.23,-.47,2.79)
        cuts=[side_window,lo] if sgn>0 else []
        patch=f.wall(.025,EAVE,cuts,.20,ROUGH)
        material_patch(f,patch.buffer(-.07),lod)
        f.prism(box(-DEPTH/2,.025,DEPTH/2,.325),.005,.037,BASE,'Plinth return')
        if sgn>0:
            shutters(f,-1.02,5.1,1.14,1.61,lod,'Upper return')
            shutters(f,-1.02,1.23,1.10,1.56,lod,'Lower return')
            b.tube([(x+.075,.11, .31),(x+.075,.11,7.11),(x+.18,.11,7.32),(x+.26,.11,7.40)],.051,GUTTER,7 if lod else 12,'Rainwater downpipe')
    roof(b,front,lod);brick_arc(front,lod);oriel(b,front,lod)
