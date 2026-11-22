"""Upper-storey joinery on the Fuzhou Road face of the World Book Company.

X increases to the right in a frontal street view; Y points into the building.
openings() supplies the wall builder with actual individual masonry apertures.
"""
from functools import lru_cache
import json
import math
from pathlib import Path

MEASURES = Path(__file__).resolve().parents[1] / "measurements"
PAINT = "Bookshop charcoal-painted window frames"
BEAD = "Bookshop black glazing beads"
GLASS = "Bookshop cool lower glazing"
FAN = "Bookshop reflected sky in transom lights"


def finish(rgb, roughness, metallic):
    def linear(value):
        s = value / 255
        return s / 12.92 if s <= .04045 else ((s + .055) / 1.055) ** 2.4
    return {"color": [linear(c) for c in rgb], "roughness": roughness, "metallic": metallic}


PALETTE = {
    PAINT: finish((52, 53, 59), .57, .14),
    BEAD: finish((39, 42, 49), .53, .10),
    GLASS: finish((69, 87, 102), .23, .28),
    FAN: finish((83, 99, 111), .25, .23),
}


@lru_cache(maxsize=1)
def openings():
    """Fit repeated jamb, sill and lintel lines to 90 independently read apertures."""
    items = json.loads((MEASURES / "upper-window-apertures.json").read_bytes())["rows"]
    refined = json.loads((MEASURES / "three-view-aperture-alignments.json").read_bytes())
    rows = []
    for r in items:
        jamb = refined["horizontal"][f'{r["bay"]}/{r["within_bay"]}']
        course = refined["bay_courses"][f'{r["bay"]}/{r["row_from_roof"]}']
        left,right = jamb["left"],jamb["right"]
        bottom,top = course["bottom"],course["top"]
        if left >= right or bottom >= top:
            raise ValueError(f"Invalid front coordinates for {r['label']}")
        rows.append({**r, "left": float(left), "right": float(right),
                     "bottom": float(bottom), "top": float(top)})
    return tuple(rows)


@lru_cache(maxsize=1)
def fitted_sections():
    return json.loads((MEASURES / "bookshop-sash-fit.json").read_bytes())


def window_parts(r):
    """Return leaf dimensions in the closed plane and their observed swing."""
    fit = fitted_sections()
    sections = fit["sections"]
    l, h = r["left"], r["bottom"]
    width = r["right"] - l
    height = r["top"] - h
    mount = min(.042, .050 * width)
    x0, x1 = l + mount, l + width - mount
    frame_y = sections["local_frame_y_m"].get(r["label"].rsplit("-",1)[0],sections["front_frame_y_m"])
    z0 = h + mount
    z1 = h + height - mount
    transom_z = z0 + (z1 - z0) * sections["lower_height_fraction"]
    rail = min(.061, .04 * height)
    leaves = []
    count = r["lower_leaves"]
    for i in range(count):
        side = ("left", "right")[i] if count == 2 else "single"
        a = x0 + (x1-x0)*i/count + .002
        b = x0 + (x1-x0)*(i+1)/count - .002
        angle = fit["swing_degrees"].get(r["label"] + "/" + side, 0.)
        hinge = b if side == "right" else a
        leaves.append((side, a, b, z0 + .002, transom_z - rail/2 - .002,
                       hinge, math.radians(angle if side == "right" else -angle)))
    return x0,x1,z0,z1,transom_z,rail,frame_y,leaves


def rectangle_ring(builder, x0, x1, z0, z1, y, depth, margin, mapper, mat, name):
    outer = ((x0,z0),(x1,z0),(x1,z1),(x0,z1))
    inner = ((x0+margin,z0+margin),(x1-margin,z0+margin),
             (x1-margin,z1-margin),(x0+margin,z1-margin))
    if x1-x0 <= 2*margin or z1-z0 <= 2*margin:
        raise ValueError(f"Glazing rebate exceeds {name}")
    vertices = [mapper(x, d, z) for d in (y,y+depth) for x,z in outer+inner]
    faces = []
    for i in range(4):
        j = (i+1)%4
        faces.extend([(i,j,4+j,4+i), (8+i,12+i,12+j,8+j),
                      (i,8+i,8+j,j), (4+i,4+j,12+j,12+i)])
    builder.add(vertices, faces, mat, name)


def transform(hinge_x, hinge_y, angle):
    c, s = math.cos(angle), math.sin(angle)
    def place(x,y,z):
        dx,dy=x-hinge_x,y-hinge_y
        return (hinge_x+c*dx-s*dy, hinge_y+s*dx+c*dy, z)
    return place, ((c,s,0),(-s,c,0),(0,0,1))


def add_windows(builder, lod=False):
    """Build closed frames and the five side-hung leaf poses visible in the detail views."""
    for r in openings():
        key = r["label"]
        xa,xb,za,zb,transom,rail,y,leaves = window_parts(r)
        mount=xa-r["left"]
        no_rotation,basis=transform(xa,y,0.)
        rectangle_ring(builder,r["left"],r["right"],r["bottom"],r["top"],y,.082,
                       mount,no_rotation,PAINT,key+" fixed perimeter")
        builder.box(((xa+xb)/2,y+.034,transom),(xb-xa,.068,rail),PAINT,
                    label=key+" continuous transom rail")
        lower=transom+rail/2
        bead=min(.023,(xb-xa)*.045)
        rectangle_ring(builder,xa,xb,lower,zb,y+.015,.033,bead,no_rotation,BEAD,
                       key+" fixed upper light rebate")
        builder.box(((xa+xb)/2,y+.050,(lower+zb)/2),
                    (xb-xa-2*bead+.003,.008,zb-lower-2*bead+.003),FAN,
                    label=key+" single undivided top light")
        for side,a,b,z0,z1,hinge,angle in leaves:
            label=key+" "+side+" casement"
            hinge_y=y+.010
            place,axes=transform(hinge,hinge_y,angle)
            margin=min(.047,(b-a)*.11)
            rectangle_ring(builder,a,b,z0,z1,hinge_y,.047,margin,place,PAINT,label+" rails and stiles")
            if not lod:
                rectangle_ring(builder,a+margin,b-margin,z0+margin,z1-margin,hinge_y+.017,
                               .015,.010,place,BEAD,label+" glazing bead")
            bead_width=margin + (0. if lod else .010)
            centre=place((a+b)/2,hinge_y+.039,(z0+z1)/2)
            builder.box(centre,(b-a-2*bead_width+.003,.008,z1-z0-2*bead_width+.003),
                        GLASS,axes,label+" pane")
