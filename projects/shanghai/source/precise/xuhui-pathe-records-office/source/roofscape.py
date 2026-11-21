"""Intersect the main hipped roof and projecting garden wing, then cut the dormers into the roof skin."""
from math import ceil
import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import split,unary_union
from photo_architecture import Facade,opening

CLAY='Old roof clay'
PAN='Weathered tile troughs'
DARK='Dark eaves timber'
WHITE='Warm dressed stone'
FRAME='Dark window frames'
GLASS='Daylit glazing'

def pieces(shape,kind):
    if shape.is_empty:return []
    if shape.geom_type==kind:return [shape]
    return [p for g in getattr(shape,'geoms',())for p in pieces(g,kind)]


def patch(points):
    poly=Polygon([p[:2]for p in points])
    matrix=np.array([[x,y,1.]for x,y,z in points]);z=np.array([z for x,y,z in points])
    plane=np.linalg.lstsq(matrix,z,rcond=None)[0]
    assert max(abs(matrix@plane-z))<1e-6
    return poly,plane


def hip(bounds,z,ridge,axis,hip_run):
    """Two pitches meet above the slightly kicked-out eave; the hips can be steeper than the long faces."""
    x0,y0,x1,y1=bounds
    def frame(x0,y0,x1,y1,z):return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    e=frame(x0,y0,x1,y1,z);k=frame(x0+.29,y0+.29,x1-.29,y1-.29,z+.11)
    p=[patch([e[i-1],e[i],k[i],k[i-1]])for i in range(4)]
    if axis=='x':
        middle=(y0+y1)/2
        a,b=(x0+hip_run,middle,ridge),(x1-hip_run,middle,ridge)
        high=[a,b,b,a]
    else:
        middle=(x0+x1)/2
        a,b=(middle,y0+hip_run,ridge),(middle,y1-hip_run,ridge)
        high=[a,a,b,b]
    for i in range(4):
        verts=[k[i-1],k[i],high[i]]
        if high[i]!=high[i-1]:verts.append(high[i-1])
        p.append(patch(verts))
    return p


def cut_higher(surface,plane,other,other_plane):
    overlap=surface.intersection(other)
    if overlap.area<1e-8:return surface
    delta=other_plane-plane;mag=np.linalg.norm(delta[:2])
    if mag<1e-9:return surface.difference(overlap) if delta[2]>1e-6 else surface
    anchor=-delta[2]*delta[:2]/(mag*mag);tangent=np.array([-delta[1],delta[0]])/mag
    line=LineString([anchor-1000*tangent,anchor+1000*tangent])
    remove=[]
    for poly in pieces(overlap,'Polygon'):
        for part in split(poly,line).geoms:
            check=part.representative_point()
            if np.dot([check.x,check.y,1.],delta)>1e-8:remove.append(part)
    return surface.difference(unary_union(remove)) if remove else surface


def draw_roof_patch(b,g,s,lod):
    # Snap the plane overlays to one micron, then discard zero-area contacts.
    # A valley may touch a slope along a line but it cannot support a row of tiles.
    surfaces = [part for part in pieces(set_precision(g, 1e-6), 'Polygon') if part.area > .003]
    if not surfaces:
        return
    g = unary_union(surfaces)
    def h(x,y):return s[0]*x+s[1]*y+s[2]
    for part in surfaces:
        if part.area>.003:
            b.prism(part,-.085,0,lambda x,y,t:(x,y,h(x,y)+t),PAN,'Roof • flared clay slopes')
    if g.area<.007:return
    slope=np.array(s[:2]);along=slope/max(np.linalg.norm(slope),1e-7);across=np.array([-along[1],along[0]])
    xmin,ymin,xmax,ymax=g.bounds
    corners=np.array([[xmin,ymin],[xmin,ymax],[xmax,ymin],[xmax,ymax]])
    for direction,spacing,radius,above,material,label in ((along,.205 if lod else .155,.018,.011,CLAY,'Runs of moulded clay tiles'),
                      (across,.42 if lod else .265,.010,.012,CLAY,'Short lapped tile courses')):
        normal=np.array([-direction[1],direction[0]]);projections=corners@normal
        for k in range(int(np.floor(min(projections)/spacing)),ceil(max(projections)/spacing)+1):
            center=normal*(k*spacing)
            line=LineString([center-80*direction,center+80*direction])
            for seg in pieces(g.intersection(line),'LineString'):
                if seg.length<.09:continue
                sx0,sy0,sx1,sy1=seg.bounds
                if sx0<xmin-.00001 or sx1>xmax+.00001 or sy0<ymin-.00001 or sy1>ymax+.00001:
                    raise ValueError('Tile run extends beyond its roof slope')
                points=[(x,y,h(x,y)+above) for x,y in (seg.coords[0],seg.coords[-1])]
                b.tube(points,radius,material,4 if lod else 6,'Roof • '+label)


def dormer(b,spec,roof_height,lod):
    side,center,front,span,reach,opening_height=spec
    if side=='north':
        face=Facade(b,(center-span/2,front),(center+span/2,front),'Northern dormer')
    elif side=='east':
        face=Facade(b,(front,center+span/2),(front,center-span/2),'Eastern dormer')
    else:
        face=Facade(b,(center+span/2,front),(center-span/2,front),'Garden dormers')
    origin=face.point(0,0,0)
    base=roof_height(origin[0],origin[1])-.035;head=base+opening_height
    aperture=opening(0,base+.065,span*.64,opening_height-.20)
    face.prism(box(-span/2,base-.10,span/2,head).difference(aperture),-.15,.014,WHITE,'Dormer • rendered front and reveals')
    clear=aperture.buffer(-.027,join_style=2);bars=[]
    for frac in (-.17,.17):bars.append(box(frac*span-.009,base,frac*span+.009,head))
    mid=base+opening_height*.52;bars.append(box(-span,mid-.012,span,mid+.012))
    face.prism(aperture.difference(clear.difference(unary_union(bars))),-.12,-.073,FRAME,'Dormer • iron glazing bars')
    face.prism(aperture,-.144,-.132,GLASS,'Dormer • glass')
    for hand in (-1,1):
        nearer=face.point(hand*span/2,0,0);rear=face.point(hand*span/2,0,-reach)
        y0=roof_height(*nearer[:2])-.065;y1=roof_height(*rear[:2])-.065
        vertices=[face.point(hand*span/2,z,d) for d,z in ((0.,y0),(-reach,y1),(-reach,max(head+.09,y1+.012)),(0.,head))]
        b.add(vertices,[(0,1,2,3)],WHITE,'Dormer • sloping cheek')
    extended=span+.18
    pts=[face.point(u,z,d)for u,d,z in [(-extended/2,.09,head),(extended/2,.09,head),(extended/2,-reach,head+.09),(-extended/2,-reach,head+.09)]]
    b.add([list(v)for v in pts]+[list(v+[0,0,.061])for v in pts],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],CLAY,'Dormer • shallow tiled hood')
    face.box(0,head+.013,extended,.061,.087,.063,DARK,'Dormer • front drip')
    xy=[face.point(u,0,d)[:2]for u,d in [(-span/2,0),(span/2,0),(span/2,-reach),(-span/2,-reach)]]
    return Polygon(xy)


def build_roofs(b,D,lod):
    width=D['width'];depth=D['wall_depth'];e=D['wall_eave'];half=width/2
    wing=D['garden_east_width'];extension=D['garden_wing_projection'];tower_x=D['north_tower_center']
    main=hip((-half-.51,-.52,half+.51,depth+.52),e+.09,D['roof_ridge'],'x',2.78)
    cross=hip((-half-.52,depth-4.65,-half+wing+.43,depth+extension+.36),e+.13,e+3.32,'y',1.72)
    tower=hip((tower_x-2.27,-.70,tower_x+2.27,2.63),D['north_tower_eave']+.025,D['north_tower_ridge'],'x',1.82)
    patches=main+cross+tower
    def height(x,y):
        probe=Point(x,y)
        return max(s@[x,y,1.] for g,s in patches if g.buffer(1e-7).covers(probe))
    cuts=[]
    for spec in [('north',4.18,.57,1.03,1.88,.82),('east',2.58,-half+.46,1.07,1.34,.92),('east',5.38,-half+.50,.91,1.32,.84)]:
        cuts.append(dormer(b,spec,height,lod))
    for x in [half-1.52,half-4.44,half-7.36]:
        cuts.append(dormer(b,('south',x,depth-.49,1.11,1.65,.91),height,lod))
    # The garden facade supplies the glazed attic face; here its small hood meets the cross roof.
    cx=-half+wing/2;front=depth+extension;top=e+D.get('garden_attic_front_height',1.17);aw=wing*.60
    cuts.append(box(cx-aw/2,front-.72,cx+aw/2,front+.02))
    caps=hip((cx-aw*.56,front-.89,cx+aw*.56,front+.14),top,top+.70,'y',.44)
    cuts.append(box(tower_x-2.02,-.39,tower_x+2.02,2.21))
    boundary=unary_union(cuts)
    for i,(g,s)in enumerate(patches):
        usable=g
        for j,(other,sp)in enumerate(patches):
            if j!=i and g.intersects(other):usable=cut_higher(usable,s,other,sp)
            if usable.is_empty:break
        if i<len(main)+len(cross):usable=usable.difference(boundary)
        else:usable=usable.difference(unary_union(cuts[:-1]))
        if not usable.is_empty:draw_roof_patch(b,usable,s,lod)
    for g,s in caps:draw_roof_patch(b,g,s,lod)
    # One tall pale chimney rises behind the northern dormer, visible in both 2013 and 2021.
    x,y=5.03,3.04;bottom=height(x,y)-.24;top=D['roof_ridge']+.35
    b.box((x,y,(top+bottom)/2),(.61,.67,top-bottom),WHITE,label='Western chimney • stack')
    for z in [top-.93,top-.42,top-.055]:
        b.box((x,y,z),(.65,.71,.10),'Stone joints',label='Western chimney • ashlar bands')
    b.box((x,y,top+.075),(.72,.76,.13),WHITE,label='Western chimney • cap')
