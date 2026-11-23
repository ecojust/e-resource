"""Wukang Road 129. A swept section for the photographed grey doorway surround.

The door argument is the established rough-opening polygon in facade (u,z).
Facade.point(u,z,d) advances outward at positive d. The new visible opening
sits inside the rough opening. The two dated references are recorded separately.
"""
import math
import numpy as np

GREY = 'Wukang 129 | grey painted archivolt'
PALETTE = {GREY: {'color': [.209, .233, .245], 'roughness': .86}}


def fitted_bounds(door):
    left, foot, right, head = door.bounds
    width = right - left
    height = head - foot
    center = (left + right) / 2 + .008 * width
    radius = .392 * width
    spring = foot + height * .710
    bottom = foot + .006 * height
    return {'center': center, 'radius': radius, 'spring': spring, 'bottom': bottom,
            'inner_crown': spring + radius, 'outer_crown': spring + radius + .270 * width,
            'width_scale': width, 'wood_face': -.045 * width}


def _sweep(builder, facade, fit, profile, stations, pitch_count, label):
    # Each cross-section forms a closed loop, including the rear of the casing.
    # A right-handed curved sweep joins sections continuously around both spring points.
    scale = fit['width_scale']
    radius = fit['radius']
    upright = fit['spring'] - fit['bottom']
    guide = radius + .164 * scale
    arc = math.pi * guide
    total = 2 * upright + arc
    vertices = []
    faces = []
    for distance, phase in stations:
        end_fade = min(1., distance / (.055*scale), (total-distance) / (.055*scale))
        for r, depth, groove, shear in profile:
            s = min(total, max(0., distance + shear * scale * end_fade))
            offset = radius + r * scale
            if s <= upright:
                u, z = fit['center']-offset, fit['bottom']+s
            elif s < upright + arc:
                angle = (s-upright)/guide
                u = fit['center'] - offset*math.cos(angle)
                z = fit['spring'] + offset*math.sin(angle)
            else:
                u, z = fit['center']+offset, fit['bottom']+total-s
            # The door sill sits above the pavement. Both 2017 and 2026
            # show the foot of the outer casting descending beside that sill.
            end_distance=min(s,total-s)
            z-=.084*scale*min(1.,r/.11)*max(0.,1.-end_distance/(.18*scale))
            if groove:
                crest = (1.+math.cos(2*math.pi*phase*pitch_count))/2.
                depth -= groove*crest**3
            vertices.append(facade.point(u,z,depth*scale))
    count = len(profile)
    for i in range(len(stations)-1):
        for j in range(count):
            a = i*count+j
            b = i*count+(j+1)%count
            faces.append((a,b,b+count,a+count))
    # Cap from the two rear corners using ear clipping. A profile may be concave
    # across its stepped beads, so a fan from the first corner would overlap.
    from shapely.geometry import Polygon
    from shapely import constrained_delaunay_triangles
    for i in (0,len(stations)-1):
        sect=[(p[0], p[1]-p[2]) for p in profile]
        polygon=Polygon(sect)
        index={tuple(value):k for k,value in enumerate(sect)}
        for triangle in constrained_delaunay_triangles(polygon).geoms:
            ids=[index[tuple(pt)] + i*count for pt in list(triangle.exterior.coords)[:3]]
            xy=np.array([sect[q%count] for q in ids])
            a,b=xy[1]-xy[0],xy[2]-xy[0]
            if (a[0]*b[1]-a[1]*b[0]>0) != (i==len(stations)-1):ids.reverse()
            faces.append(tuple(ids))
    # Orient the entire closed component in the physical ENU frame.
    v=np.asarray(vertices,float);tri=[]
    for f in faces:
        tri.extend((f[0],f[k],f[k+1]) for k in range(1,len(f)-1))
    tri=np.asarray(tri,dtype=int)
    volume=np.einsum('ij,ij->i',v[tri[:,0]],np.cross(v[tri[:,1]],v[tri[:,2]])).sum()
    if volume<0:faces=[f[::-1] for f in faces]
    builder.add(vertices,faces,GREY,facade.label+'/'+label)


def add_archivolt(builder,facade,door,lod=False):
    fit=fitted_bounds(door); scale=fit['width_scale']
    guide=fit['radius']+.164*scale
    straight=fit['spring']-fit['bottom']
    length=2*straight+math.pi*guide
    # 2017 and 2026 photos give individual grooves at .037–.042 m on the
    # straight legs; one pitch is measured on the approximate given facade scale.
    count=round(length/(.0398*scale))
    arc_steps=26 if lod else 52
    plain_stations=[(0.,0.)]+[(straight+math.pi*guide*j/arc_steps,0.) for j in range(arc_steps+1)]+[(length,0.)]
    mould=[(0,-.066),(.096,-.066),(.096,.046),(.088,.052),(.084,.040),
           (.075,.036),(.071,.050),(.061,.055),(.051,.051),(.048,.032),
           (.042,.029),(.037,.041),(.028,.044),(.019,.040),(.015,.023),
           (.010,.020),(0,.003)]
    _sweep(builder,facade,fit,[(r,d,0.,0.) for r,d in mould],plain_stations,0,'inner-two-rounds-and-reveal')
    outer=[(.220,-.037),(.270,-.037),(.270,.006),(.263,.023),(.253,.043),(.238,.059),(.220,.065)]
    _sweep(builder,facade,fit,[(r,d,0.,0.) for r,d in outer],plain_stations,0,'rounded-outer-shoulder')
    # Front groove dies into the shoulders; its changing transverse phase gives
    # the same diagonal direction on both legs, then rotates round the arch.
    flutes=[(.089,-.031,0.,0.),(.225,-.031,0.,0.),(.225,.064,0.,.029),
            (.213,.075,.002,.027),(.193,.087,.008,.024),(.169,.094,.013,.015),
            (.146,.091,.014,0.),(.125,.081,.011,-.014),(.107,.062,.007,-.025),
            (.096,.052,.002,-.030),(.089,.050,0.,-.031)]
    if lod:
        flutes=[flutes[i] for i in (0,1,2,4,5,7,8,10)]
    samples=count*(5 if lod else 8)
    stations=[(length*i/samples,i/samples) for i in range(samples+1)]
    _sweep(builder,facade,fit,flutes,stations,count,'continuous-diagonal-reeded-roll')
    return fit
