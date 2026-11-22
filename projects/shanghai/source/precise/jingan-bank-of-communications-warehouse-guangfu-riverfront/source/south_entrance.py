"""South river gate at Guangfu Road 195, reconstructed from the registered front and oblique photographs."""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

M = Path(__file__).resolve().parents[1] / 'measurements'
OBS = json.loads((M / 'portal-stone-observations.json').read_bytes())
LETTERS = json.loads((M / 'portal-inscription-contours.json').read_bytes())['inscriptions']
STONE = 'River entrance | grey washed aggregate'
EDGE = 'River entrance | light washed-stone arris'
RECESS = 'River entrance | shaded stone recess'
BRONZE = 'River entrance | dark applied warehouse lettering'
BLACK = 'River entrance | dark metal fittings'
GOLD = 'River entrance | pale brass brand face'


def finish(rgb, roughness, metallic=0):
    rgb = np.asarray(rgb, dtype=float) / 255
    linear = np.where(rgb > .04045, ((rgb + .055) / 1.055) ** 2.4, rgb / 12.92)
    return {'color': linear.tolist(), 'roughness': roughness, 'metallic': metallic}


PALETTE = {
    STONE: finish([162,160,155], .88), EDGE: finish([179,176,169], .83),
    RECESS: finish([134,132,127], .9), BRONZE: finish([67,61,55], .53, .36),
    BLACK: finish([57,55,54], .64,.21), GOLD: finish([204,185,135], .44,.40),
}


@lru_cache(maxsize=1)
def calibrated_frame():
    return json.loads((M / 'south-entrance-metric.json').read_bytes())


def image_frame(frame=None):
    """Take a pixel→(X,Z) homography, or a caller-supplied metric portal width."""
    frame = calibrated_frame() if frame is None else frame
    if 'reference_pixel_to_xz' in frame:
        matrix = np.asarray(frame['reference_pixel_to_xz'],dtype=float)
    else:
        width = float(frame['clear_width_m'])
        sx = width / 143.5
        sz = float(frame.get('vertical_scale_m_per_pixel', sx))
        matrix = np.array([[sx, 0, -542.75*sx], [0, -sz, 738.5*sz], [0,0,1]])
    def xz(uv):
        q = matrix @ [*uv, 1]
        x,z = q[:2] / q[2]
        if 'vertical_response' in frame:
            vr=frame['vertical_response']; dy=vr['reference_v']-uv[1]
            z=vr['numerator']*dy/(1+vr['denominator']*dy)
        return np.array([x,z])
    width = np.linalg.norm(xz([614.5,738.5])-xz([471,738.5]))
    return xz, width, float(frame.get('tower_face_y', 0.))


def polygon_uv(points, xz):
    return Polygon([xz(pt) for pt in points])


def openings(frame=None):
    """Return nine steel-window envelopes and the pedestrian/vehicle opening in local metres."""
    xz,_,_=image_frame(frame)
    windows=[]
    for top, sill in OBS['window_rows_top_sill']:
        for left,right in OBS['window_clear_cells']:
            windows.append(polygon_uv([[left,top],[right,top],[right,sill],[left,sill]],xz))
    return windows, polygon_uv([[471,654.5],[614.5,654.2],[614.5,738.5],[471,738.5]],xz)


def add_south_entrance(b, lod=False, frame=None, window_openings=None):
    """Build the two stepped towers, window surrounds, inscribed stone lintel and open gate.

    Optional window_openings are the nine shared (X,Z) polygons in storey-then-bay order.
    Their companion glazing is a separate editable component.
    """
    low = lod is True or lod == 'lod'
    xz,width,y0=image_frame(frame)
    windows,clear = openings(frame)
    if window_openings is not None:
        if len(window_openings)!=9: raise ValueError('Nine registered openings are required')
        windows=[p if isinstance(p,Polygon) else Polygon(p) for p in window_openings]
    def point(x,z,d): return x,y0-d,z
    def extrude(poly, back, front, material, name):
        b.prism(poly,back*width,front*width,point,material,name)
    def plane(points,back,front,mat,name):
        extrude(polygon_uv(points,xz),back,front,mat,name)
    def plate(left,top,right,bottom,back,front,mat,name):
        plane([(left,top),(right,top),(right,bottom),(left,bottom)],back,front,mat,name)
    def uv_pol(points): return polygon_uv(points,xz)

    # The two tower heads and the lower middle crown have separately visible steps.
    silhouette=OBS['crown_uv']
    crown=uv_pol(silhouette+[[690,739],[393.2,739]])
    def cut(left,right):
        return uv_pol([[left,138],[right,138],[right,744],[left,744]])
    # Faces of the broad strips, their setbacks and narrow arrises are separate editable solids.
    west=[393.2,398.5,452.9,459.2,470.8,474.4]
    east=[611.6,615.0,624.6,630.8,683.2,690.0]
    canopy=uv_pol(OBS['gate_front_outer']+[[630.,750.],[455.,750.]])
    window_void=unary_union(windows)
    for name,stops,ds in [('West',west,[-.013,0,-.006,-.013,-.027]),
                          ('East',east,[-.027,-.013,-.006,0,-.013])]:
        for index,(left,right,front) in enumerate(zip(stops,stops[1:],ds),1):
            shape=crown.intersection(cut(left,right)).difference(canopy).difference(window_void)
            extrude(shape,-.085,front,STONE,f'{name} stone tower | stepped strip {index}')
    middle=crown.intersection(cut(west[-1],east[0])).difference(window_void).difference(canopy)
    extrude(middle,-.069,-.008,STONE,'Three-bay centre | window surrounds and stepped upper crown')
    # Add a broad sub-backing behind the plaque, with a continuous void under the frame.
    plate(455.,587.7,630.,617.1,-.085,.004,STONE,'Inscribed field | continuous stone backing')
    sill=uv_pol(OBS['plaque_cap']+OBS['plaque_cap_lower'][::-1]).difference(window_void)
    extrude(sill,-.024,.018,EDGE,'Three windows | stepped sill above the inscription')
    # Ring profiles are open at the bottom. Each mitered jamb and the header is an independent closed solid.
    outer=np.asarray(OBS['gate_front_outer']); inner=np.asarray(OBS['gate_splayed_inner'])
    profiles=[(0.,.001),(.13,.018),(.35,.029),(.68,.029),(.85,.018),(1.,-.007)]
    if low: profiles=[profiles[i] for i in (0,2,3,5)]
    def vertices(r,front):
        return [np.array([x,y0-front*width,z]) for x,z in [xz(uv) for uv in (outer+(inner-outer)*r)]]
    strips=[vertices(r,front) for r,front in profiles]
    strips += [vertices(1.,-.085),vertices(0.,-.085)]
    for i,title in enumerate(('west jamb','splayed lintel','east jamb')):
        verts=np.array([p for contour in strips for p in (contour[i],contour[i+1])])
        count=len(strips);faces=[]
        for k in range(count): faces.append([2*k,2*k+1,2*((k+1)%count)+1,2*((k+1)%count)])
        from shapely import constrained_delaunay_triangles
        # End caps are concave. Triangulate their profile in its own two-dimensional coordinates.
        profile=[(r,depth) for r,depth in profiles]+[(1.,-.085),(0.,-.085)]
        ppoly=Polygon(profile)
        for tri in constrained_delaunay_triangles(ppoly).geoms:
            ids=[profile.index(tuple(q)) for q in list(tri.exterior.coords)[:-1]]
            if tri.exterior.is_ccw != ppoly.exterior.is_ccw: ids=ids[::-1]
            faces.append([2*k for k in ids])
            faces.append([2*k+1 for k in ids[::-1]])
        # A reflection between the west jamb and east jamb changes volume sign.
        triangles=np.asarray([(f[0],f[j],f[j+1]) for f in faces for j in range(1,len(f)-1)])
        aa,bb,cc=verts[triangles].transpose(1,0,2)
        if np.einsum('ij,ij->',aa,np.cross(bb,cc))<0:triangles=triangles[:,::-1]
        b.add(verts,triangles,EDGE,f'Mitered entrance frame | {title}')
    # A pale transverse beam and the dark transom are individually visible in both eras.
    plane(OBS['lower_transverse_lintel'],-.091,-.013,EDGE,'Deep opening | pale transverse beam')
    plane(OBS['upper_dark_strip'],-.081,-.068,BLACK,'Deep opening | dark upper transom')
    for n,row in enumerate(LETTERS):
        is_four = n < 4
        shapes=[]
        for contours in row['polygons']:
            shell=[xz(pt) for pt in contours['outer']]
            holes=[[xz(pt) for pt in ring]for ring in contours['holes']]
            poly=Polygon(shell,holes)
            # Separate quantized point contacts before extrusion, retaining the counters as physical holes.
            poly=poly.buffer(-width*.00006,quad_segs=1,join_style='mitre').buffer(width*.00002,quad_segs=1,join_style='mitre')
            poly=poly.simplify(width*(.0024 if low else .00016),preserve_topology=True)
            if not poly.is_empty and poly.is_valid:shapes.append(poly)
        lettering=unary_union(shapes)
        if is_four:
            extrude(lettering,.003,.0065,BRONZE,f'Warehouse name | letter {n+1}')
        else:
            # The black sides are visible from the oblique exposure. The lighter metal faces are grouped separately.
            extrude(lettering,-.009,.018,BLACK,f'Upper wordmark | dark sides {n-3}')
            extrude(lettering,.018,.0212,GOLD,f'Upper wordmark | brass face {n-3}')
