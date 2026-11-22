"""Relief of the south portal from the 16 August 2014 architectural archive photograph."""
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely import constrained_delaunay_triangles
from shapely.geometry import Point, Polygon

DATA = Path(__file__).resolve().parents[1] / "measurements/portal-carvings-2014.json"
STONE = "Carved grey portal stone"
LETTERS = "Raised pale stone date"
PALETTE = {
    STONE: {"color": [.255, .232, .215], "roughness": .91},
    LETTERS: {"color": [.355, .329, .301], "roughness": .88},
}


def closed_relief(builder, pixels, heights, faces, position, support, material, label):
    """Give an image-space relief its visible face, polygon returns and embedded back."""
    pixels = np.asarray(pixels, float)
    heights = np.broadcast_to(heights, len(pixels))
    front = np.array([position(*uv, support-h) for uv,h in zip(pixels, heights)])
    back = np.array([position(*uv, support+.0015) for uv in pixels])
    oriented, edges = [], set()
    for face in faces:
        face = tuple(face)
        a,b,c = pixels[list(face[:3])]
        # With the camera outside a facade, increasing image v points down.
        # Negative signed image area gives the face toward the camera.
        if (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]) > 0:
            face = face[::-1]
        oriented.append(face)
        for a,b in zip(face, face[1:]+face[:1]):
            if (b,a) in edges:
                edges.remove((b,a))
            else:
                edges.add((a,b))
    n = len(pixels)
    shell = oriented + [tuple(i+n for i in face[::-1]) for face in oriented]
    shell.extend((b,a,a+n,b+n) for a,b in sorted(edges))
    builder.add(np.vstack((front,back)), shell, material, label)


def stone_face(builder, polygon, origin, depth, bevel_px, position, support, material, label):
    core = polygon.buffer(-bevel_px, quad_segs=3)
    pieces = [polygon] if core.is_empty else [polygon.difference(core), core]
    vertices,faces,index = [],[],{}
    for shape in pieces:
        for tri in constrained_delaunay_triangles(shape).geoms:
            face = []
            for x,y in list(tri.exterior.coords)[:3]:
                key = (round(x,6), round(y,6))
                if key not in index:
                    index[key] = len(vertices)
                    vertices.append(key)
                face.append(index[key])
            if len(set(face)) == 3:
                faces.append(face)
    h = [depth*(.68+.32*min(1.,polygon.boundary.distance(Point(*p))/bevel_px)) for p in vertices]
    closed_relief(builder, np.array(vertices)+origin, h, faces, position, support, material, label)


def grid_faces(rows, columns):
    faces = []
    for i in range(rows-1):
        for j in range(columns-1):
            a = i*columns+j
            faces.append((a,a+1,a+columns+1,a+columns))
    return faces


def folded_strip(builder, name, controls, origin, position, support, lod):
    controls = np.array(controls,float)
    length = np.r_[0.,np.cumsum(np.linalg.norm(np.diff(controls[:,:2],axis=0),axis=1))]
    stations = np.linspace(0,length[-1],max(8,int(length[-1]/(2.4 if lod else 1.15))))
    curve = PchipInterpolator(length, controls, axis=0)(stations)
    tangent = np.gradient(curve[:,:2], axis=0)
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1,keepdims=True),.001)
    normal = np.column_stack((-tangent[:,1],tangent[:,0]))
    across = np.linspace(-1.,1.,5 if lod else 9)
    # At a tightly turned knot the interior of a ribbon is compressed. Limit
    # its transverse span locally so the photographed loop has no overlapping
    # faces at that turn. Its exterior remains a single attached stone strip.
    width = curve[:,2].copy()
    def det(a,b):
        return a[:,0]*b[:,1] - a[:,1]*b[:,0]
    for _ in range(24):
        left = curve[:,:2]-normal*width[:,None]
        right = curve[:,:2]+normal*width[:,None]
        bad = ((det(right[:-1]-left[:-1],right[1:]-left[:-1]) >= -1e-8) |
               (det(right[1:]-left[:-1],left[1:]-left[:-1]) >= -1e-8))
        if not np.any(bad):
            break
        i = np.flatnonzero(bad)
        width[np.unique(np.r_[i,i+1])] *= .72
    else:
        raise ValueError("Fold profile reverses at " + name)
    uv = curve[:,None,:2]+origin+normal[:,None,:]*width[:,None,None]*across[None,:,None]
    phase = stations / length[-1]
    # Ribbons thicken across the rounded fold and twist gently at the ends.
    turn = .20*np.sin(phase*np.pi*2)
    crown = np.sqrt(np.maximum(0.,1.-across**2))
    h = .011 + (.020+.009*np.sin(phase*np.pi))[:,None]*crown + .005*turn[:,None]*across
    if name == "Swag central binding":
        h += .041
    closed_relief(builder,uv.reshape(-1,2),h.ravel(),grid_faces(len(curve),len(across)),
                  position,support,STONE,name)


def fruit(builder, ellipse, origin, position, support, label, lod, profile=None):
    x,y,rx,ry = ellipse
    sectors, levels = (12,4) if lod else (24,7)
    angles = np.arange(sectors)*2*np.pi/sectors
    factors = np.ones(sectors) if profile is None else np.asarray(profile["perimeter_factors"])[::24//sectors]
    uv, heights, faces = [[x,y]], [.052 if profile is None else .069], []
    for ring in range(1,levels+1):
        radius = ring/levels
        for j,a in enumerate(angles):
            scale = radius*factors[j]
            uv.append([x+rx*scale*np.cos(a),y+ry*scale*np.sin(a)])
            h = np.sqrt(max(0.,1.-radius**2))
            heights.append((.014+.038*h) if profile is None else (.023+.046*h))
            i = 1+(ring-1)*sectors+j
            following = 1+(ring-1)*sectors+(j+1)%sectors
            faces.append((0,i,following) if ring==1 else (i-sectors,i,following,following-sectors))
    uv = np.asarray(uv)
    mark = None if profile is None else profile.get("visible_depression")
    if mark:
        radius = np.linalg.norm(uv-np.array(mark["source_centre_px"]),axis=1)/mark["radius_px"]
        heights = np.array(heights)-.016*np.exp(-1.8*radius**2)+.0018*np.exp(-((radius-1.05)/.3)**2)
    closed_relief(builder,uv+origin,heights,faces,position,support,STONE,label)


def cupped_leaf(builder, leaf, origin, position, support, lod):
    start,end = np.array(leaf["base"]),np.array(leaf["tip"])
    tangent = end-start
    normal = np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)
    t = np.linspace(0.,1.,6 if lod else 11)
    s = np.linspace(-1.,1.,5 if lod else 9)
    width = leaf["half_width"]*(.10+.90*np.sin(np.pi*t)**.78)
    centres = start + t[:,None]*tangent + .16*width[:,None]*normal
    uv = centres[:,None,:]+normal[None,None,:]*width[:,None,None]*s[None,:,None]+origin
    # A low midrib, recessed channel on either side and turned outer rim
    # give the photographed pendent drops their distinct changing section.
    profile = .36+.58*abs(s)**1.5+.62*np.exp(-(s/.18)**2)
    on_swag = "drop" not in leaf["name"].lower()
    h = (.024 if on_swag else .014)+np.sin(np.pi*t)[:,None]*.024*profile[None,:]
    closed_relief(builder,uv.reshape(-1,2),h.ravel(),grid_faces(len(t),len(s)),position,support,STONE,leaf["name"])


def add_portal_carvings(builder, lod, position, date_support_y, swag_support_y):
    """Use position(u, v, y) for the 800 × 1200 close photograph; +y is inward."""
    data = json.loads(DATA.read_bytes())
    date = data["date"]
    for glyph in date["digits"]:
        poly = Polygon(glyph["outline"],glyph["holes"])
        if not poly.is_valid:
            raise ValueError("Invalid date outline: "+glyph["digit"])
        offset = np.add(date["origin_px"],glyph["crop_origin_px"])
        stone_face(builder,poly,offset,.016,.38,position,date_support_y,LETTERS,"Cut stone numeral "+glyph["digit"])
    swag = data["festoon"]
    origin = np.array(swag["origin_px"],float)
    stone_face(builder,Polygon(swag["swag_body"]),origin,.028,1.55,position,swag_support_y,STONE,"Fruit garland backing")
    for fold in swag["folds"]:
        folded_strip(builder,fold["name"],fold["points"],origin,position,swag_support_y,lod)
    fruit_study = json.loads((DATA.parent/"portal-fruit-profiles.json").read_bytes())
    if fruit_study["photograph_sha256"] != data["source"]["sha256"]:
        raise ValueError("Fruit observations and carving photograph differ")
    for record,ell in zip(fruit_study["shapes"],swag["fruit_ellipses"],strict=True):
        i = record["number"]
        fruit(builder,ell,origin,position,swag_support_y,f"Swag carved fruit {i:02d}",lod,record)
    for leaf in swag["leaves"]:
        cupped_leaf(builder,leaf,origin,position,swag_support_y,lod)
    for i,ell in enumerate(swag["knots"],1):
        fruit(builder,ell,origin,position,swag_support_y,f"Tied ribbon knot {i}",lod)

