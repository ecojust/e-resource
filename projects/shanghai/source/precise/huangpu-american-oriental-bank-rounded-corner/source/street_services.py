"""Exterior condensers and rainwater pipes visible in Huangpu's 2023 survey.

Coordinates on a Facade are u along the wall, z up and d towards the street.
The condenser z is the centre of the complete cabinet, including a twin unit.
Rainwater pipe centre lines use the same metre-based world frame as the building.
"""
from math import cos, pi, sin, tau
import numpy as np
from shapely.geometry import Polygon, box

ENAMEL = 'Outdoor unit weathered ivory enamel'
EDGE = 'Outdoor unit pale folded edge'
FAN = 'Outdoor unit charcoal fan'
GUARD = 'Outdoor unit grey fan guard'
MOUNT = 'Outdoor unit galvanized brackets'
HOSE = 'Service pipe dark insulation'
DRAIN = 'Rainwater pipe dark painted metal'
SERVICE_MATERIALS = {
    ENAMEL: {'color': [.677, .686, .661], 'roughness': .73, 'metallic': .15},
    EDGE: {'color': [.728, .733, .705], 'roughness': .62, 'metallic': .21},
    FAN: {'color': [.134, .148, .146], 'roughness': .79},
    GUARD: {'color': [.301, .321, .309], 'roughness': .71, 'metallic': .31},
    MOUNT: {'color': [.335, .340, .314], 'roughness': .75, 'metallic': .31},
    HOSE: {'color': [.190, .178, .151], 'roughness': .92},
    DRAIN: {'color': [.163, .162, .145], 'roughness': .66, 'metallic': .26},
}


def _circle(u, z, r, segments):
    return [(u + r*cos(i*tau/segments), z + r*sin(i*tau/segments))
            for i in range(segments)]


def _fan_mesh(face, u, z, radius, front, lod):
    """Positive angular winding in the u-z plane faces the street."""
    n = 12 if lod else 20
    depth = min(.053, radius*.18)

    def wheel(profile, material, label):
        # Traverse from the outer rim towards the centre. This gives the conical
        # inside wall an inward radial normal and the wire rings a street-facing top.
        verts = [face.point(x, y, d) for r, d in profile
                 for x, y in _circle(u, z, r*radius, n)]
        faces = [(k*n+i, k*n+(i+1)%n, (k+1)*n+(i+1)%n, (k+1)*n+i)
                 for k in range(len(profile)-1) for i in range(n)]
        face.builder.add(verts, faces, material, face.label + '/' + label)

    wheel([(1.,front),(.94,front+.004),(.88,front-depth)],
          EDGE, 'Pressed circular inlet')
    back = front-depth
    plate = Polygon(_circle(u, z, radius*.89, n))
    face.prism(plate, back-.010, back+.001, FAN, 'Fan recess back')
    guard = front-.011
    for r in ((.76,) if lod else (.81,.62,.43)):
        wheel([(r+.021,guard-.004),(r,guard+.002),(r-.022,guard-.004)],
              GUARD, 'Rolled fan guard rings')
    # Four flat radial stays hold the guard off the dark recess. The photographed
    # centre is much lighter than the opening on both the single and twin units.
    for i in range(4):
        a = (i+.5)*pi/2
        ux, uz = cos(a), sin(a)
        half = max(.004,radius*.022)
        strip = Polygon([(u + r*ux - side*uz, z + r*uz + side*ux)
                         for r, side in ((radius*.14,-half),(radius*.89,-half),
                                         (radius*.89,half),(radius*.14,half))])
        face.prism(strip,guard-.008,guard-.001,GUARD,'Fan guard stays')
    hub = Polygon(_circle(u,z,radius*.155,8 if lod else 12))
    face.prism(hub,back+.001,guard+.004,EDGE,'Fan centre cap')


def add_outdoor_unit(face, u, z, width, height, lod, double=False):
    """Add one wall-mounted single- or twin-fan enclosure at a surveyed position."""
    if min(width,height)<=0:
        raise ValueError('Condenser dimensions must be positive')
    tiers = 2 if double else 1
    tier = height/tiers
    radius = min(width*.325,tier*.418)
    gap = min(.095,width*.105)
    depth = min(width*.389,tier*.48)
    front = gap+depth
    setback = min(.053,radius*.18)+.021
    bottom = z-height/2
    fan_u = u-width*.105
    centres = [bottom+tier*(i+.5) for i in range(tiers)]
    segments = 12 if lod else 20
    cabinet = box(u-width/2,bottom,u+width/2,bottom+height)
    for h in centres:
        cabinet = cabinet.difference(Polygon(_circle(fan_u,h,radius,segments)))
    face.box(u,z,width,height,depth-setback,gap+(depth-setback)/2,
             ENAMEL,'Condenser cabinet back and sides')
    face.prism(cabinet,front-setback,front,ENAMEL,'Punched condenser face')
    for h in centres:
        _fan_mesh(face,fan_u,h,radius,front,lod)
    if not lod:
        face.box(u+width*.346,z,width*.008,height*.94,.004,front+.002,
                 MOUNT,'Service cover seam')
    lip = min(.017,height*.027)
    face.box(u,z+height/2,width+lip,lip,depth+lip,gap+depth/2,
             EDGE,'Folded top casing lip')

    for side in (-1,1):
        pos = u+side*width*.31
        span = gap+depth*.88
        face.box(pos,bottom-.020,.04,.036,span,span/2,MOUNT,'Wall bracket rail')
        face.box(pos,bottom-.117,.044,.248,.031,.010,MOUNT,'Bracket wall plate')
        if not lod:
            points = [face.point(pos,bottom-.224,.020),
                      face.point(pos,bottom-.036,span*.78)]
            face.builder.tube(points,.013,MOUNT,5,face.label+'/Bracket diagonal')
    if not lod:
        # The short return between the cabinet and the wall is visible; the
        # onward pipe run varies by bay and is not repeated with every cabinet.
        end = u+width*.45
        route = [face.point(end,bottom+.045,gap+.07),
                 face.point(end,bottom-.047,gap+.06),
                 face.point(end+.038,bottom-.092,gap+.038),
                 face.point(end+.077,bottom-.092,.024),
                 face.point(end+.085,bottom-.056,.006)]
        face.builder.tube(route,.014,HOSE,6,face.label+'/Short insulated return')


def add_downpipe(builder, points, lod):
    """Follow the supplied pipe route with continuous swept, rounded elbows."""
    path = np.asarray(points,dtype=float)
    if path.ndim!=2 or path.shape[1]!=3 or len(path)<2 or not np.isfinite(path).all():
        raise ValueError('Supply two or more finite three-dimensional pipe points')
    spans = np.linalg.norm(np.diff(path,axis=0),axis=1)
    if np.any(spans<.001):
        raise ValueError('Successive pipe points must be distinct')
    rounded = [path[0]]
    for i in range(1,len(path)-1):
        a, corner, b = path[i-1:i+2]
        incoming, outgoing = (corner-a)/spans[i-1], (b-corner)/spans[i]
        if np.dot(incoming,outgoing)<-.995:
            raise ValueError('A reversing downpipe needs a measured return radius')
        if np.dot(incoming,outgoing)>.9995:
            continue
        offset = min(.19,spans[i-1]*.28,spans[i]*.28)
        start, end = corner-incoming*offset, corner+outgoing*offset
        rounded.append(start)
        steps = 2 if lod else 5
        for j in range(1,steps+1):
            t = j/steps
            rounded.append((1-t)**2*start+2*t*(1-t)*corner+t*t*end)
    rounded.append(path[-1])
    # Transport a radial axis through the bends. This keeps the short sections
    # from changing cross-section orientation when the pipe turns vertical.
    radii = []
    nodes = np.array(rounded)
    segments = 7 if lod else 12
    for i, node in enumerate(nodes):
        tangent = nodes[min(i+1,len(nodes)-1)]-nodes[max(i-1,0)]
        tangent /= np.linalg.norm(tangent)
        previous = radii[-1] if radii else np.eye(3)[np.argmin(abs(tangent))]
        axis = previous-np.dot(previous,tangent)*tangent
        axis /= np.linalg.norm(axis)
        radii.append(axis)
    vertices = []
    for i, (node, axis) in enumerate(zip(nodes,radii)):
        tangent = nodes[min(i+1,len(nodes)-1)]-nodes[max(i-1,0)]
        tangent /= np.linalg.norm(tangent)
        perp = np.cross(tangent,axis)
        vertices.extend(node+.053*(axis*cos(k*tau/segments)+perp*sin(k*tau/segments))
                        for k in range(segments))
    faces = [tuple(reversed(range(segments))),
             tuple((len(nodes)-1)*segments+j for j in range(segments))]
    for i in range(len(nodes)-1):
        for j in range(segments):
            left = i*segments+j
            right = i*segments+(j+1)%segments
            faces.append((left,right,right+segments,left+segments))
    builder.add(vertices,faces,DRAIN,'Measured rainwater downpipe')
