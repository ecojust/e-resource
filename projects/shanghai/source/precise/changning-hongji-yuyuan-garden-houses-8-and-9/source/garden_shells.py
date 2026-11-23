"""Cut each masonry envelope to the measured window profiles and underside of its own roof."""
from math import hypot

from shapely import set_precision
from shapely.affinity import affine_transform
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import eight_gable
from garden_fabric import BRICK, CREAM, PLINTH, RENDER
import house_eight_entrances
import house_nine_sashes
import nine_portico
import nine_side_facades
import roof_8
import roof_9


def footprint(number, layout):
    width=layout['wall_width']
    if number==8:
        # Sloping east roof stops at the aerial step. The low front additions
        # and the faceted café porch have their own individually pierced walls.
        ranges=[box(0,0,width,13.00), Polygon([(-5.70,6.31),(9.88,7.47),(9.88,14.30),(-5.70,13.14)]),
                Polygon([(-1.18,12.70),(7.92,12.70),(7.92,20.96),(-1.18,20.04)]),
                box(-5.70,6.045,-2.90,7.60), box(-3.66,5.10,.16,7.60)]
    else:
        back=nine_portico.dimensions()['door_plane_y']
        ranges=[box(0,0,width,23.24),box(-2.16,.28,.13,23.08),
                box(-3.01,.276,.12,4.63),box(-2.64,8.21,.12,13.32),
                box(-2.84,15.19,.12,21.90),box(width-.11,back,13.40,10.43),
                box(width-.11,12.83,11.58,21.17),box(11.44,14.96,13.15,19.04)]
    return orient(unary_union(ranges),sign=1.)


def boundaries(shape):
    if shape.is_empty:
        return
    if hasattr(shape,'geoms'):
        for g in shape.geoms:
            yield from boundaries(g)
    else:
        yield from shape.coords


def wall_profile(a, c, sections):
    beam=LineString([a,c]);length=beam.length
    marks={0.,round(length,7)}
    for _,poly,_ in sections:
        for coord in boundaries(beam.intersection(poly.boundary)):
            marks.add(round(beam.project(Point(coord)),7))
    edges=sorted(marks);ranges=[]
    dx,dy=(c[0]-a[0])/length,(c[1]-a[1])/length
    for start,end in zip(edges,edges[1:]):
        if end-start<1e-6:continue
        mid=(start+end)/2;pt=Point(a[0]+dx*mid,a[1]+dy*mid)
        planes=[p for _,poly,p in sections if poly.buffer(1e-7).covers(pt)]
        if not planes:
            raise ValueError(f'Masonry outside measured roof at {pt.wkt}')
        h=max(planes,key=lambda p:p[0]*pt.x+p[1]*pt.y+p[2])
        def z(s):
            return h[0]*(a[0]+dx*s)+h[1]*(a[1]+dy*s)+h[2]-.079
        ranges.append(Polygon([(start,-.044),(end,-.044),(end,z(end)),(start,z(start))]))
    return set_precision(unary_union(ranges), .00001).simplify(.000011, preserve_topology=True)


def front_holes(holes):
    return [('y',0.,poly) for poly in holes.values()]


def collect_holes(number,layout,north):
    if number==8:
        cuts=front_holes(eight_gable.front_openings(layout))
        g=house_eight_entrances.north_wall_opening(layout)
        cuts.append(('x',g['face_x'],box(g['y0'],g['z0']-.03,g['y1'],g['z1'])))
        return cuts
    cuts=front_holes(house_nine_sashes.front_openings(layout))
    cuts.extend(('x',x,outline) for _,x,outline in nine_side_facades.south_openings())
    porch=nine_portico.dimensions()['door_plane_y']
    cuts.extend([('y',porch,nine_portico.rear_wall_opening()),('y',porch,porch_sash())])
    for window in north:
        a,c=window['a'],window['c']
        fixed,axis=('x',0) if abs(a[0]-c[0])<1e-4 else ('y',1)
        s0,s1=sorted((a[1-axis],c[1-axis]))
        cuts.append((fixed,a[axis],box(s0,window['low'],s1,window['high'])))
    return cuts


def porch_sash():
    return box(8.387,3.47,10.468,4.935)


def add_shell(b,number,layout,north=()):
    plan=footprint(number,layout)
    sections=(roof_8 if number==8 else roof_9).roof_sections(layout)
    cuts=collect_holes(number,layout,north)
    b.plan_prism(plan,-.087,-.043,PLINTH,f'{number} | building ground slab')
    b.plan_prism(plan.buffer(-.16,join_style=2),2.72,2.87,PLINTH,f'{number} | upper floor plate')
    if number==9:
        # The smaller north gable terminates below the stepped-back large gable.
        # Its upper wall is exposed above the low roof, inside the ground outline.
        infill=set_precision(roof_9.rear_gable_infill(layout),.00001).simplify(.000011)
        b.prism(infill,11.38,11.58,lambda y,z,x:(x,y,z),RENDER,'9 | exposed stepped-back north gable')
    coords=list(plan.exterior.coords)
    for i,(a,c) in enumerate(zip(coords,coords[1:]),1):
        length=hypot(c[0]-a[0],c[1]-a[1]);dx=(c[0]-a[0])/length;dy=(c[1]-a[1])/length
        def map_point(s,z,d):
            return a[0]+dx*s+dy*d,a[1]+dy*s-dx*d,z
        profile=wall_profile(a,c,sections)
        for axis,pos,cut in cuts:
            horizontal=axis=='y';j=1 if horizontal else 0
            if max(abs(a[j]-pos),abs(c[j]-pos))>.001:continue
            coeff=dx if horizontal else dy
            shift=-a[1-j]*coeff
            profile=profile.difference(affine_transform(cut,[coeff,0.,0.,1.,shift,0.]))
        label=f'{number} | wall {i:02d}'
        if number==8:
            storeys=[(-.05,.56,PLINTH,'plinth'),(.56,4.397,BRICK,'brickwork'),(4.397,20.,CREAM,'render')]
            # The transverse café gable is consistently painted white. The
            # avenue-facing main west gable keeps its measured brick/render boundary.
            if max(a[0],c[0])<=-.10 and max(a[1],c[1])<13.70:
                storeys=[(-.05,.30,PLINTH,'plinth'),(.30,20.,CREAM,'café render')]
            if max(abs(a[1]-6.045),abs(c[1]-6.045))<.001 and min(a[0],c[0])< -5.60:
                storeys=[(-.05,.56,PLINTH,'sign wall plinth'),(.56,3.79,BRICK,'café sign wall'),
                         (3.79,20.,CREAM,'pale café eaves')]
        else:
            storeys=[(-.05,.565,PLINTH,'plinth'),(.565,20.,RENDER,'pebbled render')]
        for low,high,material,name in storeys:
            clipped=profile.intersection(box(-.1,low,length+.1,high))
            for polygon in getattr(clipped,'geoms',[clipped]):
                if polygon.geom_type=='Polygon' and polygon.area>1e-7:
                    b.prism(polygon,-.204,0.,map_point,material,label+' '+name)
