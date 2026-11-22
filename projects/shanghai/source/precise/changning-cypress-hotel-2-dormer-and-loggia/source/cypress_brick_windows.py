"""Lawn-facing brickwork below the valley eave of Cypress Hotel villa 2.

The two upper opening polygons use the surveyed pixel corners. Depths and the
running bond are reconstruction dimensions. The photograph resolves the courses
at the ground floor more clearly than the joints between individual bricks.
"""
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

BRICKS = ("Cypress russet clay", "Cypress red clay", "Cypress orange clay")
JOINT = "Cypress warm bedding mortar"
SASH = "Cypress dark timber sash"
GLASS = ("Cypress shaded garden glass", "Cypress reflected garden glass")
SILL = "Cypress fired window sill"
LINTEL = "Cypress buff ground lintel"

def pigment(rgb, roughness, metallic=0.0):
    color = np.asarray(rgb, dtype=float) / 255.0
    return dict(color=np.where(color <= .04045, color / 12.92,
                               ((color + .055) / 1.055)**2.4).tolist(),
                roughness=roughness, metallic=metallic)

PALETTE = {
    BRICKS[0]: pigment((154, 83, 61), .90),
    BRICKS[1]: pigment((160, 86, 64), .91),
    BRICKS[2]: pigment((165, 92, 67), .88),
    JOINT: pigment((149, 103, 79), .94),
    SASH: pigment((69, 50, 41), .64),
    GLASS[0]: pigment((48, 53, 54), .39, .10),
    GLASS[1]: pigment((76, 82, 85), .37, .10),
    SILL: pigment((137, 76, 55), .88),
    LINTEL: pigment((181, 142, 105), .88),
}

@lru_cache(maxsize=1)
def survey():
    folder = Path(__file__).resolve().parents[1] / 'measurements'
    camera = json.loads((folder / 'lawn-camera.json').read_bytes())
    openings = json.loads((folder / 'second-storey-openings.json').read_bytes())
    assert camera['source_sha256'] == openings['source_sha256']
    return np.asarray(camera['pinhole_3x4']), openings['windows']

def on_wall(pixels):
    matrix, _ = survey()
    homography = matrix[:, [0, 2, 3]]
    pixels = np.asarray(pixels, dtype=float)
    homogeneous = np.linalg.solve(homography, np.c_[pixels, np.ones(len(pixels))].T).T
    return homogeneous[:, :2] / homogeneous[:, 2, None]

def plane(x, z, relief):
    return (x, -relief, z)

def polygon(points):
    return Polygon(on_wall(points))

def point_in_opening(quad, u, v):
    # Clockwise pixel survey starts at top left. v increases down the facade.
    a, b, c, d = quad
    return (1-v)*((1-u)*a + u*b) + v*((1-u)*d + u*c)

def panel(quad, left, top, right, bottom):
    return Polygon([point_in_opening(quad, u, v) for u,v in
                    ((left,top),(right,top),(right,bottom),(left,bottom))])

def window(builder, quad, label, columns, rails, light):
    opening = Polygon(quad)
    width = .5 * (np.linalg.norm(quad[1]-quad[0]) + np.linalg.norm(quad[2]-quad[3]))
    height = .5 * (np.linalg.norm(quad[3]-quad[0]) + np.linalg.norm(quad[2]-quad[1]))
    jamb, head = .043/width, .046/height
    bar_x, bar_z = .019/width, .015/height
    panes = []
    splits = [0., *rails, 1.]
    for j, (v0, v1) in enumerate(zip(splits, splits[1:])):
        for i in range(columns):
            p = panel(quad, i/columns + (jamb if i==0 else bar_x*.5),
                      v0+(head if j==0 else bar_z*.5),
                      (i+1)/columns - (jamb if i+1==columns else bar_x*.5),
                      v1-(head if j+1==len(splits)-1 else bar_z*.5))
            panes.append(p)
            m = GLASS[1 if light and i==0 else 0]
            builder.prism(p, -.142, -.134, plane, m, label+'/recessed panes')
    builder.prism(opening.difference(unary_union(panes)), -.146, -.095, plane, SASH, label+'/frame and bars')
    # Both sill ends extend into the brickwork. The top slopes away from the frame.
    left = point_in_opening(quad, -.06, 1.0)
    right = point_in_opening(quad, 1.06, 1.0)
    profile = [(-.087,.005),(.067,-.018),(.052,-.083),(-.085,-.074)]
    ends = [(float(pt[0]),-depth,float(pt[1]+offset)) for pt in (left,right) for depth,offset in profile]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    builder.add(ends, faces, SILL, label+'/sloping fired sill')

def coursed_face(builder, mask, lod):
    # 72-mm courses and a 235-mm stretcher suit the visible horizontal scale.
    # Vertices share the same front plane at both levels. The close view includes
    # the recessed beds and the returns of each face, the far view omits those returns.
    minx,minz,maxx,maxz = mask.bounds
    pitch, course, seam = .235, .072, .009
    batches = {}
    for row in range(math.floor(minz/course), math.ceil(maxz/course)):
        bottom = row*course + seam*.5
        top = bottom + course-seam
        origin = (.5 if row%2 else 0.)*pitch
        for col in range(math.floor((minx-origin)/pitch), math.ceil((maxx-origin)/pitch)):
            lo = origin+col*pitch+seam*.5
            face = box(lo,bottom,lo+pitch-seam,top)
            if not mask.contains(face):
                face = mask.intersection(face)
            if face.is_empty or face.area < 2e-6:
                continue
            value = (row * 37 + col * 71 + (row*col)%11)%13
            material = BRICKS[1 if value < 8 else 0 if value < 11 else 2]
            vertices, triangles = batches.setdefault((row//9,material), ([],[]))
            # A clipped face can split at a reveal. Triangulation is required for
            # concave fragments, which also occur where a corner crosses a brick.
            polygons = [face] if face.geom_type == 'Polygon' else [g for g in getattr(face,'geoms',()) if g.geom_type=='Polygon']
            for frag in polygons:
                frag=orient(frag,sign=1.)
                for piece in constrained_delaunay_triangles(frag).geoms:
                    pts=list(orient(piece,sign=1.).exterior.coords)[:3]
                    off=len(vertices);vertices.extend([(x,-.008,z) for x,z in pts]);triangles.append((off,off+1,off+2))
                    if not lod:
                        off=len(vertices);vertices.extend([(x,.003,z) for x,z in pts]);triangles.append((off+2,off+1,off))
                if not lod:
                    for ring in (frag.exterior,*frag.interiors):
                        for (x,z),(u,v) in zip(ring.coords, list(ring.coords)[1:]):
                            off=len(vertices);vertices.extend(((x,.003,z),(u,.003,v),(u,-.008,v),(x,-.008,z)))
                            triangles.extend(((off,off+1,off+2),(off,off+2,off+3)))
    for (band,material),(vertices,triangles) in sorted(batches.items()):
        builder.add(vertices,triangles,material,'Middle brick field/course band '+str(1+band-math.floor(minz/course)//9)+' '+material.split()[1])

def add_brick_front(builder, lod):
    _, openings = survey()
    # Outer left junction, under-eave wall head and right loggia edge. The base is
    # continued to the requested ground line beneath the photographic vegetation.
    field = polygon([(454,247),(542,240),(542,376),(454,376)])
    upper = [on_wall(r['corners']) for r in openings]
    # Three widths of lower glazing are visible at lawn level. The foot is screened by planting.
    lower = on_wall([(475.7,326.3),(507.0,325.4),(507.2,361.5),(476.0,362.9)])
    sections = [*upper, lower]
    holes = unary_union([Polygon(q) for q in sections])
    masonry = field.difference(holes)
    builder.prism(masonry,-.235,-.001,plane,JOINT,'Middle brick field/reveals and cut wall')
    coursed_face(builder,masonry,lod)
    window(builder,upper[0],'Middle brick field/left upstairs',2,(),True)
    window(builder,upper[1],'Middle brick field/right upstairs',2,(.31,.55,.79),False)
    window(builder,lower,'Middle brick field/lawn opening',3,(.19,),False)
    band=polygon([(473,321.9),(508.5,320.8),(509.5,324.3),(474.1,325.7)])
    builder.prism(band,-.012,.063,plane,LINTEL,'Middle brick field/light lintel at lawn opening')
