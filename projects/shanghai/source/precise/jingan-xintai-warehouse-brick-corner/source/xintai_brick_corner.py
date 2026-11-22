"""Two adjoining bays of the east elevation of the Xintai warehouse, 57 Xintai Road.

Local X runs rightwards in the published photograph; Y points into the building
and Z rises from the threshold. Exterior masonry is complete through the
reveal. Window joinery and interior finishing are separate components.
"""
from collections import defaultdict
from math import asin, ceil, cos, floor, pi, sin
from shapely import box, constrained_delaunay_triangles
from shapely.geometry import Polygon
from shapely.ops import unary_union

GREY='Xintai blue-grey brick and lime joint'
RED='Xintai warm orange-red rubbed brick'
SHADOW='Xintai recessed grey mortar'
STONE='Xintai pale stone sill and coping'
IRON='Xintai black tie-rod end plates'
REVEAL='Xintai inner blue-grey brick reveal'
GREY_FACES=['Xintai grey face '+s for s in ('slate','cool ash','warm ash','blue stone','pale kiln')]
RED_FACES=['Xintai red brick '+s for s in ('light-fired','burnt','weathered')]
def paint(rgb,roughness=.94):
    return dict(color=[n/255 for n in rgb],roughness=roughness)
MATERIALS={
    GREY:paint((135,142,133)),RED:paint((174,99,78)),SHADOW:paint((77,89,86)),
    STONE:paint((163,163,145)),IRON:paint((52,53,46),.76),REVEAL:paint((96,107,102)),
    **dict(zip(GREY_FACES,map(paint,[(105,121,116),(116,130,124),(125,134,123),(106,126,123),(136,144,132)]))),
    **dict(zip(RED_FACES,map(paint,[(184,107,85),(162,86,69),(175,99,78)])))
}
BAY=3.75
WIDTH=2*BAY
HEIGHT=11.40
DEPTH=.485
RETURN=1.12
F=lambda x,z,d:(x,-d,z)
def corner(u,z,d):return (WIDTH+d,u,z)
# (centre, sill, half width, spring, rise, radial ring thickness, red surround)
def openings():
    return [
        (BAY*.5,.005,.976,2.83,.217,.235,True),(BAY*1.5,.005,.979,2.85,.204,.228,False),
        (BAY*.5,5.62,.934,6.79,.224,.265,True),(BAY*1.5,4.77,.925,6.79,.245,.215,False),
        (BAY*.5,9.12,.940,10.22,.185,.233,True),(BAY*1.5,8.93,.929,10.30,.183,.204,False)
    ]

def masonry(b,shape,back,front,m,mapper,label):
    if not shape.is_empty:b.prism(shape,back,front,mapper,m,label)
def band(b,x0,x1,z0,z1,back,front,m,mapper,label):
    masonry(b,box(x0,z0,x1,z1),back,front,m,mapper,label)
def arch(opening,samples):
    c,sill,h,spring,rise,th,red=opening
    radius=(h*h+rise*rise)/(2*rise);theta=asin(h/radius);cz=spring+rise-radius
    def arc(t,d=0):
        angle=(t-.5)*2*theta
        return c+(radius+d)*sin(angle),cz+(radius+d)*cos(angle)
    pts=[arc(i/samples)for i in range(samples+1)]
    return arc,Polygon([(c-h,sill),(c+h,sill),*reversed(pts)])
def running_bond(b,field,width,height,plane,lod,label,red_base=False):
    """Build faces for full/stretchers and headers, with individually clipped jambs."""
    groups=defaultdict(lambda:([],[]))
    bw=.244;course=.089
    row_count=ceil(height/course)
    for r in range(row_count):
        z0=r*course+.005;z1=min(height,(r+1)*course-.005)
        if z1<=z0:continue
        # Regular courses of shorter headers tie successive leaves of this bonded wall.
        step=bw if r%6 else .132
        offset=(r%2)*step*.5
        for i in range(floor(-offset/step),ceil((width-offset)/step)):
            a=max(0.,offset+i*step+.005);bb=min(width,offset+(i+1)*step-.005)
            if bb<=a:continue
            face=box(a,z0,bb,z1)
            if not field.intersects(face):continue
            if lod:
                # The reduced role has continuous wall masonry. Selected darker
                # headers and stretchers keep the bond visible at thumbnail scale.
                if (i*7+r*11)%6:continue
            if field.covers(face):
                shapes=[list(face.exterior.coords)[:4]]
            else:
                clipped=face.intersection(field)
                if clipped.is_empty or clipped.area<1e-7:continue
                shapes=[list(x.exterior.coords)[:3]for x in constrained_delaunay_triangles(clipped).geoms if x.area>1e-7]
            tones=RED_FACES if red_base and .81<z0<3.70 else GREY_FACES
            mat=tones[(i*13+r*19+i*r)%len(tones)]
            vertices,faces=groups[mat]
            for coords in shapes:
                # Positive winding faces the exterior. Shapely box rings and CDT
                # polygons differ in orientation, so use their signed area.
                area=sum(x*coords[(j+1)%len(coords)][1]-y*coords[(j+1)%len(coords)][0]for j,(x,y)in enumerate(coords))
                if area<0:coords=list(reversed(coords))
                start=len(vertices);vertices.extend(plane(x,z,.003)for x,z in coords);faces.append(tuple(range(start,start+len(coords))))
    for m,(v,f) in groups.items():b.add(v,f,m,label+' — bonded masonry faces')
def ring(b,o,far):
    c,sill,h,spring,rise,th,red=o
    arc,cut=arch(o,32);count=15 if o[1]<.01 else 13
    for j in range(count):
        left=(j+.026)/count;right=(j+.974)/count
        ts=[left,right] if far else [left,(left+right)*.5,right]
        wedge=Polygon([arc(t,0)for t in ts]+[arc(t,th)for t in reversed(ts)])
        m=RED_FACES[(j*7)%3]if red else GREY_FACES[(j*7)%5]
        masonry(b,wedge,-.120,.036 if red else .018,m,F,'Radially jointed shallow segmental brick arch')
    if red and sill>.1:
        for sign in [-1,1]:
            side=c+sign*h
            band(b,min(side,side+sign*.182),max(side,side+sign*.182),spring-.287,spring+.008,-.072,.037,RED,F,'Red quoin stepping down at the springing')
    return cut
def pilaster(b,c,far):
    half=.40
    left=max(0,c-half);right=min(WIDTH,c+half)
    band(b,left,right,3.86,11.08,-.03,.088,RED,F,'Red brick pilaster, stepped horizontal divisions')
    for k in range(12):
        lo=3.872+k*.578
        # Two individual red brick faces form each red rustication unit.
        if lo>11.00:break
        hi=min(lo+.543,11.08);m=RED_FACES[(k+round(c*2))%3]
        band(b,left,right,lo,hi,.080,.126,m,F,'Projecting red pilaster course')
        if not far:
            band(b,left,right,lo+.26,lo+.268,.125,.128,RED,F,'Fine mortar at the middle of a brick course')
    for z in (3.98,7.77):
        band(b,max(left,c-.09),min(right,c+.09),z-.085,z+.085,.121,.152,IRON,F,'Small square dark iron tie plate')
    band(b,max(left,c-.28),min(right,c+.28),7.30,7.44,.122,.155,IRON,F,'Oblong tie at the raised intermediate stringcourse')
def add_warehouse_corner(b,lod=False):
    """Add the final two full bays of the right wing and 1.12 m of its end return."""
    b.palette.update({k:dict(v)for k,v in MATERIALS.items()})
    ext=box(0.,0.,WIDTH,HEIGHT)
    holes=[arch(o,32)[1]for o in openings()]
    field=ext.difference(unary_union(holes))
    masonry(b,field,-DEPTH,0.,GREY,F,'Solid bonded wall with six real arched reveals')
    running_bond(b,field,WIDTH,HEIGHT,F,lod,'East wall')
    # A butt joint at the corner shares the same planes. The east wall already
    # covers the first wall thickness at the corner; extend the return beyond.
    side=box(0.,0.,RETURN,HEIGHT)
    masonry(b,box(DEPTH,0.,RETURN,HEIGHT),-DEPTH,0.,GREY,corner,'North end return of the corner brickwork')
    band(b,0,RETURN,.81,3.70,0.,.002,RED,corner,'Red ground-storey brickwork on the end face')
    running_bond(b,side,RETURN,HEIGHT,corner,lod,'Return at the end of the wing',red_base=True)
    for o in openings():
        ring(b,o,lod)
        c,sill,h,spring,rise,th,red=o
        if sill>.10:
            band(b,c-h-.085,c+h+.085,sill-.097,sill-.026,-.07,.110,STONE,F,'Dressed pale sill below arched window')
        if red and sill>.10:
            band(b,c-h+.067,c+h-.067,sill-.365,sill-.098,-.023,.035,RED,F,'Continuous rectangular red-brick apron')
            for sg in [-1,1]:
                a=c+sg*(h-.09);band(b,a-.085,a+.085,sill-.438,sill-.287,-.02,.047,RED_FACES[1],F,'Short projecting apron end')
    for z in (.36,1.06,1.81,2.57,3.29):
        # Ground-floor grey masonry is broken by narrow continuous dark channels;
        # clip each strip against actual front openings to preserve their full depth.
        strip=field.intersection(box(0,z,WIDTH,z+.045))
        masonry(b,strip,0.,.009,SHADOW,F,'Recessed horizontal shadow in ground-storey brickwork')
        band(b,0,RETURN,z,z+.045,0.,.009,SHADOW,corner,'Ground-storey channel around the corner')
    for lo,hi,depth,m in [(3.71,3.86,.156,STONE),(3.67,3.71,.084,GREY),(7.57,7.67,.095,RED),(7.67,7.79,.143,RED_FACES[0]),(11.03,11.17,.175,SHADOW),(11.17,11.40,.270,STONE)]:
        band(b,0,WIDTH,lo,hi,-.068,depth,m,F,'Continuous horizontal stringcourse across both openings')
        band(b,-depth,RETURN,lo,hi,-.069,depth,m,corner,'Horizontal course with a true return at the corner')
    for c in (0,BAY,WIDTH):pilaster(b,c,lod)
    for i in range(34):
        x=.31+i*.212
        if min(abs(x-c)for c in (0,BAY,WIDTH))<.39:continue
        band(b,x-.045,x+.045,7.48,7.58,.006,.082,RED_FACES[1],F,'Small brick dentil beneath the red belt')
    # Short continuation of the corner pier on the second face.
    band(b,0,.34,3.86,11.03,-.032,.084,RED,corner,'Red corner pilaster turns at the north end')
    for j in range(12):
        lo=3.872+j*.578
        band(b,-.11,.34,lo,min(lo+.543,11.03),.074,.122,RED_FACES[j%3],corner,'Red masonry course returning past the corner')
