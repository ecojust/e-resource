"""Two name piers facing Nanchang Road, with recessed lettering and stepped stone caps."""

from pathlib import Path
from shapely import affinity
from shapely.geometry import box
from shapely.ops import unary_union
from sign_lettering import lettering_shapes

FONT = Path(__file__).resolve().parent / "lettering/Lane110StoneLetters.otf"
NAME = "上海別墅"
FIELD = "Blue-grey inset stone"
FRAME = "Light grey rubbed stone"
GRANITE = "Grey plinth stone"
CROWN = "Weathered capstone"
INK = "Dark infill in name strokes"


def slab(b, xmin, xmax, front, back, bottom, top, material, label):
    b.box(((xmin + xmax) / 2, (front + back) / 2, (bottom + top) / 2),
          (xmax - xmin, back - front, top - bottom), material, label=label)


def face(b, shape, front, back, material, label):
    b.prism(shape, -back, -front, lambda x, z, depth: (x, -depth, z), material, label)


def rect(x, z, width, height):
    return [(x - width / 2, z - height / 2), (x + width / 2, z - height / 2),
            (x + width / 2, z + height / 2), (x - width / 2, z + height / 2)]


def frame(b, outer, inner, y_outer, y_inner, material, label):
    """Four mitred continuous surfaces around a sunken rectangular inscription."""
    vertices = [(x, y_outer, z) for x, z in outer] + [(x, y_inner, z) for x, z in inner]
    sides = [(i, (i + 1) % 4, (i + 1) % 4 + 4, i + 4) for i in range(4)]
    b.add(vertices, sides, material, label)


def stone_tier(b, x, y, levels, material, label):
    """Successive rectangular plan sections describe the pedestal or pyramidal cap."""
    vertices = []
    faces = [(3, 2, 1, 0)]
    for i, (width, depth, z) in enumerate(levels):
        vertices.extend([(a, c, z) for a, c in rect(x, y, width, depth)])
        if i:
            k = 4 * (i - 1)
            for j in range(4):
                nxt = (j + 1) % 4
                faces.append((k + j, k + nxt, k + nxt + 4, k + j + 4))
    k = len(vertices) - 4
    faces.append((k, k + 1, k + 2, k + 3))
    b.add(vertices, faces, material, label)


def inscription(b, x, fw, field_bottom, field_top, y, side, lod):
    height = field_top - field_bottom
    # Image observations give separate max widths and heights for the four glyphs.
    positions = [(0.828, 0.66, 0.075), (0.614, 0.73, 0.087),
                 (0.390, 0.66, 0.086), (0.166, 0.70, 0.086)]
    letters = []
    for character, (level, width, size) in zip(NAME, positions):
        outline = lettering_shapes(character, width * fw, height * size, font=FONT)[0][1]
        tol = 0.00155 if lod else 0.00045
        outline = outline.simplify(tol, preserve_topology=True)
        letters.append(affinity.translate(outline, xoff=x, yoff=field_bottom + height * level))
    field = box(x - fw / 2, field_bottom, x + fw / 2, field_top)
    depth = 0.0035
    if lod:
        face(b, field, y, y + 0.025, FIELD, side + " inset field")
    else:
        face(b, field.difference(unary_union(letters)), y, y + depth, FIELD, side + " engraved field")
    for i, shape in enumerate(letters):
        front = y - 0.001 if lod else y + depth
        face(b, shape, front, front + 0.003, INK, side + " recessed character " + NAME[i])


def add_pier(b, x, d, side, lod):
    h, w, depth = d["height"], d["width"], d["depth"]
    y = depth / 2
    broad = w * 1.035
    z_plinth, z_shoulder = h * 0.160, h * 0.174
    stone_tier(b, x, y, [(broad, depth * 1.07, 0.0), (broad, depth * 1.07, z_plinth),
                          (w * 1.01, depth * 1.035, h * 0.167),
                          (w, depth, z_shoulder)], GRANITE, side + " battered plinth")
    cap_bottom = h * 0.948
    field_bottom, field_top = h * 0.197, h * 0.920
    centre = (field_bottom + field_top) / 2
    fw = w * 0.58
    fh = field_top - field_bottom
    field_y = max(0.037, w * 0.115)
    # The shaft is solid on both returns and on the reverse. The front is open at the field.
    slab(b, x - w / 2, x + w / 2, field_y + 0.014, depth, z_shoulder, cap_bottom,
         FRAME, side + " shaft and returns")
    outer = rect(x, (cap_bottom + z_shoulder) / 2, w, cap_bottom - z_shoulder)
    inner = rect(x, centre, fw, fh)
    ring = rect(x, centre, fw + w * 0.16, fh + h * 0.024)
    frame(b, outer, ring, 0.0, 0.0, FRAME, side + " flat outer border")
    frame(b, ring, inner, 0.0, field_y, CROWN, side + " bevel to inscription")
    # Four thin returns close the outer boundary between the face and the shaft.
    frame(b, outer, outer, field_y + 0.014, 0.0, FRAME, side + " shaft front returns")
    inscription(b, x, fw, field_bottom, field_top, field_y, side, lod)
    stone_tier(b, x, y, [(w, depth, cap_bottom), (w * 1.045, depth * 1.04, h * 0.952),
        (w * 1.045, depth * 1.04, h * 0.968), (w * 0.93, depth * 0.92, h * 0.975),
        (w * 0.88, depth * 0.87, h * 0.981), (w * 0.68, depth * 0.69, h * 0.988),
        (w * 0.51, depth * 0.51, h)], CROWN, side + " stepped cap")
