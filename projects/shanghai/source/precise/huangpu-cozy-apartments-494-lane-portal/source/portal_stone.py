"""Stone jambs, bed joints, inset name panel and separate raised lettering above the lane gate."""

from pathlib import Path
from shapely.geometry import box
from shapely import affinity
from sign_lettering import lettering_shapes

SOURCE = Path(__file__).resolve().parent
FONT = SOURCE / "lettering/CozyGateInscription.otf"
CHARACTERS = "康綏公寓"
STONE = ("Buff-grey cut stone", "Cool grey alternate stone", "Pale stone with ochre cast")
JOINT = "Recessed stone bed joint"
FACE = "Grey-green inset inscription field"
EDGE = "Dressed stone coping"
LETTER = "Oxide red name characters"


def front(b, poly, outer, inner, mat, name):
    b.prism(poly, -inner, -outer, lambda x, z, d: (x, -d, z), mat, name)


def panel(b, x0, x1, z0, z1, outer, inner, mat, name):
    b.box(
        ((x0 + x1) / 2, (outer + inner) / 2, (z0 + z1) / 2),
        (x1 - x0, inner - outer, z1 - z0),
        mat,
        label=name,
    )


def dressed_block(b, x0, x1, z0, z1, face, back, mat, label, lod):
    if lod:
        panel(b, x0, x1, z0, z1, face, back, mat, label)
        return
    # A shallow bevel on the four face arrises catches light at masonry joints.
    bevel = 0.008
    points = ((x0, z0), (x1, z0), (x1, z1), (x0, z1))
    inset = (
        (x0 + bevel, z0 + bevel),
        (x1 - bevel, z0 + bevel),
        (x1 - bevel, z1 - bevel),
        (x0 + bevel, z1 - bevel),
    )
    verts = (
        [(x, face, z) for x, z in inset]
        + [(x, face + bevel, z) for x, z in points]
        + [(x, back, z) for x, z in points]
    )
    faces = [(0, 1, 2, 3), (11, 10, 9, 8)]
    for i in range(4):
        j = (i + 1) % 4
        faces.extend(((i, i + 4, j + 4, j), (i + 4, i + 8, j + 8, j + 4)))
    b.add(verts, faces, mat, label)


def add_portal(b, d, lod):
    width = d["stone_width"]
    south = d["stone_front_y"]
    jamb_y = south + 0.03
    head = d["opening_head"]
    cap = d["crown"]
    clear = d["clear_width"]
    opening_mid = d["opening_center_x"]
    left = opening_mid - clear / 2
    right = opening_mid + clear / 2
    west = d["stone_center_x"] - width / 2
    east = west + width
    sign_low, sign_high = d["board_low"], d["board_high"]
    field_half = d["board_width"] / 2
    field_mid = d["board_center_x"]
    for i, (x0, x1) in enumerate([(west, left), (right, east)]):
        label = ("West" if i == 0 else "East") + " portal jamb"
        panel(b, x0, x1, 0.012, head, jamb_y + 0.029, 0.27, JOINT, label + " bedding")
        courses = 10
        for k in range(courses):
            h = head / courses
            mat = STONE[(k * 7 + i) % 3]
            dressed_block(
                b,
                x0 + 0.006,
                x1 - 0.006,
                k * h + 0.006,
                (k + 1) * h - 0.006,
                jamb_y,
                0.30,
                mat,
                label + " front course",
                lod,
            )
            # The broad stone face turns into the passage reveal.
            a, c = (x1 - 0.075, x1) if i == 0 else (x0, x0 + 0.075)
            panel(
                b,
                a,
                c,
                k * h + 0.006,
                (k + 1) * h - 0.006,
                0.30,
                0.45,
                mat,
                label + " reveal course",
            )
        bevel = box(x0 - 0.015, head - 0.09, x1 + 0.015, head - 0.015)
        front(b, bevel, south - 0.023, 0.44, EDGE, label + " impost band")
    # Rectangular portal. The lintel spans the actual air gap and has a visible underside.
    panel(b, west, east, head, sign_low, south - 0.025, 0.47, EDGE, "Portal lintel and soffit")
    panel(
        b, west, east, sign_low, sign_high, south + 0.012, 0.35, JOINT, "Inscription backing wall"
    )
    panel(
        b,
        field_mid - field_half,
        field_mid + field_half,
        sign_low + 0.008,
        sign_high - 0.008,
        south - 0.008,
        south + 0.04,
        FACE,
        "Recessed grey inscription field",
    )
    for i, (x0, x1) in enumerate([(west, field_mid - field_half), (field_mid + field_half, east)]):
        for k in range(4):
            unit = (sign_high - sign_low) / 4
            panel(
                b,
                x0 + 0.004,
                x1 - 0.003,
                sign_low + k * unit + 0.006,
                sign_low + (k + 1) * unit - 0.006,
                south - 0.046,
                0.36,
                STONE[(k + 2 * i) % 3],
                "Side block framing the inscription",
            )
    panel(
        b,
        west - 0.025,
        east + 0.025,
        sign_high,
        cap - 0.047,
        south - 0.049,
        0.43,
        STONE[0],
        "Upper inscription rail",
    )
    for k in range(9):
        length = (width + 0.11) / 9
        x0 = west - 0.055 + k * length
        panel(
            b,
            x0 + 0.003,
            x0 + length - 0.003,
            cap - 0.048,
            cap,
            south - 0.082,
            0.47,
            STONE[(k + 1) % 3],
            "Individual capstone",
        )
    text_z = d["letter_mid_z"]
    letter_h = d["letter_height"]
    # Four roughly equally spaced glyphs. The photographed sign has generous
    # grey gaps, particularly on either side of 公.
    ink_width = 0.452
    pitch = (d["letter_width"] - ink_width) / 3
    for i, ch in enumerate(CHARACTERS):
        shape = lettering_shapes(ch, ink_width, letter_h, font=FONT)[0][1]
        tol = 0.0016 if lod else 0.00045
        x = d["letter_center_x"] + (i - 1.5) * pitch
        geom = affinity.translate(shape.simplify(tol, preserve_topology=True), xoff=x, yoff=text_z)
        front(b, geom, south - 0.034, south - 0.008, LETTER, f"Inscription relief {i + 1} {ch}")
