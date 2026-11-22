"""Photogrammetrically aligned clay tilework above the garden gable and the three-facet oriel.

Coordinates use the centre of the attic sill as origin, X to the photograph's right,
Y towards the interior, Z up. Dimensions are estimated in metres.
"""
from collections import defaultdict
from math import ceil, cos, floor, pi, sin
import numpy as np

CLAY = '480 terracotta pan tile'
SUN_CLAY = '480 sun-warmed burnt clay'
WEATHERED = '480 weathered brown pan'
UNDER_TILE = '480 deep clay lap and exposed lower edge'
HIP_CAP = '480 curved terracotta hip cap'
HIP_EDGE = '480 shadowed rim of overlapping cap'
ROOF_MATERIALS = {
    CLAY: {'color': [.350, .119, .065], 'roughness': .92},
    SUN_CLAY: {'color': [.428, .162, .093], 'roughness': .90},
    WEATHERED: {'color': [.266, .098, .064], 'roughness': .96},
    UNDER_TILE: {'color': [.095, .047, .034], 'roughness': .98},
    HIP_CAP: {'color': [.447, .162, .089], 'roughness': .90},
    HIP_EDGE: {'color': [.270, .090, .060], 'roughness': .95},
}

# Same 800 × 600 garden-camera matrix used for all four attic windows.
PROJECTION = np.array([
    [432.2157908551818, 636.6821833008293, 50.99632673545427, 12706.18799101128],
    [-129.0089081280357, 326.797868422364, -633.5101992517576, 3816.669564410169],
    [-.4174018782073773, .905328140694124, .07846419397581456, 22.387008949328376],
])
# (photographic x, photographic y, model depth). These mark the edges of the pans.
PHOTO_ANCHORS = {
    'gable eave left': (526.8, 109.8, -.28),
    'gable eave right': (602.1, 101.1, -.28),
    'gable hip apex': (573.6, 65.0, 1.00),
    'oriel upper left': (550.2, 174.4, -.018),
    'oriel upper right': (579.6, 171.45, -.018),
    'oriel front eave left': (531.2, 202.2, -.90),
    'oriel front eave right': (585.6, 198.6, -.90),
    'oriel left wing eave': (507.3, 207.3, -.11),
    'oriel right wing eave': (621.7, 200.4, -.11),
}

def on_depth_plane(u, v, depth):
    plane = PROJECTION[:, [0, 2, 3]].copy()
    plane[:, 2] += depth * PROJECTION[:, 1]
    p = np.linalg.solve(plane, np.array([u, v, 1.0]))
    return np.array([p[0] / p[2], depth, p[1] / p[2]])

ANCHORS = {name: on_depth_plane(*controls) for name,controls in PHOTO_ANCHORS.items()}

def unit(v):
    return v / np.linalg.norm(v)

def tile_face(builder, name, a, b, c, d, courses, pitch, far):
    """Tile one tapering slope, with fixed-width pans clipped by its two hips.

    a,b are the low edge; c,d are the high edge. c==d gives a triangular face.
    Independent islands are grouped by course and firing colour for Blender editing.
    """
    axis = unit(b-a)
    width = np.linalg.norm(b-a)
    normal = unit(np.cross(b-a, .5*(c+d)-a))
    assert normal[2] > .03
    high_left, high_right = np.dot(c-a, axis), np.dot(d-a, axis)

    def span(t):
        return high_left*t, width*(1-t)+high_right*t

    def world(s,t):
        left, right = span(t)
        u = np.clip((s-left)/max(right-left,1e-11), 0., 1.)
        return (1-u)*((1-t)*a+t*c)+u*((1-t)*b+t*d)

    corners = [a,b,d,c] if np.linalg.norm(d-c) > .001 else [a,b,c]
    size = len(corners)
    bed = [p-normal*.036 for p in corners]+[p-normal*.008 for p in corners]
    faces = [tuple(range(size-1,-1,-1)), tuple(range(size,2*size))]
    faces.extend((i,(i+1)%size,(i+1)%size+size,i+size) for i in range(size))
    builder.add(bed,faces,UNDER_TILE,name+' bed and eave')

    def flute(x):
        # An interlocking pan has a raised longitudinal roll and a shallow trough.
        return .004 + .022*(.5+.5*cos(2*pi*(x-.13)))**1.55

    for j in range(courses):
        groups = defaultdict(lambda: ([],[]))
        t0,t1 = j/courses, (j+1)/courses
        # The head of each lower tile extends behind the upper tile.
        t1 = min(1.,t1+.038/courses)
        t_levels = [t0,t1] if far else [t0,t0+(t1-t0)*.16,t1]
        bounds = [span(t) for t in (t0,t1)]
        lows,highs = zip(*bounds)
        offset = pitch*.10
        for col in range(floor((min(lows)-offset)/pitch),ceil((max(highs)-offset)/pitch)):
            start = col*pitch+offset
            phase = (col*11+j*7+len(name))%17
            mat = SUN_CLAY if phase in (2,8,10,13) else WEATHERED if phase in (0,4,14) else CLAY
            # Intersect the tile's finite width with each straight hip, including
            # the exact height where a diagonal edge passes the edge of this pan.
            active_lo,active_hi=t0,t1
            for origin,slope in ((width-start, high_right-width),(start+pitch,-high_left)):
                if abs(slope)<1e-12:
                    if origin < -1e-10:active_hi=active_lo
                elif slope>0:
                    active_lo=max(active_lo,-origin/slope)
                else:
                    active_hi=min(active_hi,-origin/slope)
            if active_hi-active_lo < 1e-8:continue
            active_levels=[active_lo]+[t for t in t_levels if active_lo+1e-8<t<active_hi-1e-8]+[active_hi]
            vertices, faces = groups[mat]
            # Each strip is clipped at each height independently. The last course can taper to a point.
            xs = [0., .13, .48, .79, 1.] if far else [0.,.07,.14,.245,.39,.53,.67,.80,.93,1.]
            rings = []
            for t in active_levels:
                left,right = span(t)
                # Clamp all samples when a tile terminates at a hip. Degenerate quads are discarded by Builder.
                ss = [np.clip(start+x*pitch,max(left,start),min(right,start+pitch)) for x in xs] if min(right,start+pitch)>max(left,start) else [np.clip(start+.5*pitch,left,right)]*len(xs)
                alpha = (t-t0)/(t1-t0)
                deep = .014*(1-alpha) # protruding lower lip against the next course
                ring=[]
                for s in ss:
                    u = np.clip((s-start)/pitch,0,1)
                    ring.append(len(vertices))
                    vertices.append(world(s,t)+normal*(flute(u)+deep))
                rings.append(ring)
            for low,high in zip(rings,rings[1:]):
                for q in range(len(xs)-1):
                    faces.append((low[q],low[q+1],high[q+1],high[q]))
            # Dark, downturned leading faces are separate from the bright upper surfaces.
            apron, recess = groups[UNDER_TILE]
            edge0 = rings[0]
            for q in range(len(xs)-1):
                p0,p1 = vertices[edge0[q]],vertices[edge0[q+1]]
                k=len(apron);apron.extend((p0,p1,p1-normal*.017,p0-normal*.017))
                recess.append((k,k+3,k+2,k+1))
        for material,(vertices,faces) in groups.items():
            if faces:
                tile_kind={CLAY:'clay',SUN_CLAY:'sunlit',WEATHERED:'weathered',UNDER_TILE:'underside'}[material]
                builder.add(vertices,faces,material,f'{name}, course {j+1:02d} {tile_kind}')
    return normal

def cap_run(builder,name,low,high,radius,units,far):
    """Separate overlapping arched cap tiles, proceeding uphill along a diagonal hip."""
    tangent=unit(high-low)
    flank=unit(np.cross(np.array([0.,0.,1.]),tangent))
    outward=unit(np.cross(tangent,flank))
    if outward[2]<0:outward=-outward
    pieces=4 if far else 8
    angles=np.linspace(0.,pi,pieces+1)
    for i in range(units):
        lower=i/units;upper=min(1.,(i+1.10)/units)
        rows=[];vertices=[];faces=[]
        for t,rad in ((lower,radius*1.04),(upper,radius*.87)):
            base=(1-t)*low+t*high+.008*outward
            row=[]
            for a in angles:
                row.append(len(vertices));vertices.append(base+flank*rad*cos(a)+outward*(.71*rad*sin(a)))
            rows.append(row)
        for u in range(pieces):
            faces.append((rows[0][u],rows[0][u+1],rows[1][u+1],rows[1][u]))
        builder.add(vertices,faces,HIP_CAP,f'{name}, arched cap {i+1:02d}')
        edges=[];f=[]
        for pt in vertices[:pieces+1]:edges.extend((pt,pt-outward*.020))
        for k in range(pieces):f.append((2*k,2*k+1,2*k+3,2*k+2))
        builder.add(edges,f,HIP_EDGE,f'{name}, lower lip of cap {i+1:02d}')

def add_roofs(builder,lod=False):
    """Add only the half-hip and the three tiled faces over the oriel; no wall or window geometry."""
    # Called with the ordinary project Builder; expose the palette for authors who combine material dictionaries.
    for material,definition in ROOF_MATERIALS.items():
        builder.palette.setdefault(material,dict(definition))
    p=ANCHORS
    ga,gb,tip=p['gable eave left'],p['gable eave right'],p['gable hip apex']
    tile_face(builder,'Half-hip at top of garden gable',ga,gb,tip,tip,7,.120,lod)
    cap_run(builder,'Left hip of garden gable',ga,tip,.079,9,lod)
    cap_run(builder,'Right hip of garden gable',gb,tip,.079,8,lod)
    wl,al,ar,wr=[p[k]for k in ('oriel left wing eave','oriel front eave left','oriel front eave right','oriel right wing eave')]
    top_l,top_r=p['oriel upper left'],p['oriel upper right']
    tile_face(builder,'Left return of oriel roof',wl,al,top_l,top_l,5,.145,lod)
    tile_face(builder,'Front slope of oriel roof',al,ar,top_l,top_r,5,.145,lod)
    tile_face(builder,'Right return of oriel roof',ar,wr,top_r,top_r,5,.145,lod)
    cap_run(builder,'Left projecting hip above oriel',al,top_l,.087,6,lod)
    cap_run(builder,'Right projecting hip above oriel',ar,top_r,.087,6,lod)
    # The two short outer hips read most clearly along the eaves at the ends of the side returns.
    cap_run(builder,'Left end of oriel roof',wl,top_l,.060,6,lod)
    cap_run(builder,'Right end of oriel roof',wr,top_r,.060,6,lod)
