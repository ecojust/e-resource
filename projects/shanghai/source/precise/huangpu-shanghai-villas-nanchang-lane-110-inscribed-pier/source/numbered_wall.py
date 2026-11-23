"""Adjoining wall of No. 112 and the lane-number plate on the opposite return."""

from shapely import affinity
from shapely.geometry import Polygon
from sign_lettering import lettering_shapes
from stone_piers import FONT, FRAME, GRANITE, face, slab

WALL = "Grey courtyard render"
COPING = "Lighter grey wall coping"
NUMERAL = "Charcoal address numerals"
TIMBER = ("Brown horizontal screen", "Weathered red-brown screen")
SUPPORT = "Dark screen support"
GREEN = "Green enamel lane number"
WHITE = "Ivory enamel print"


def address_marks(b, text, width, height, mapper, mat, label, lod):
    for i, (_, shape) in enumerate(lettering_shapes(text, width, height, font=FONT.with_name("NanchangAddresses.otf"))):
        # Both signs are much smaller than the names on the stone piers.
        poly = shape.simplify(0.0016 if lod else 0.0006, preserve_topology=True)
        b.prism(poly, 0.0, 0.0025, mapper, mat, label + " mark " + str(i + 1))


def make_wall(b, d, lod):
    west = -d["centre_distance"] / 2 - d["width"] / 2
    left = west - d["wall_width"]
    height = d["wall_height"]
    jamb = d["address_jamb_width"]
    front = d["wall_front_setback"]
    back = front + d["wall_depth"]
    slab(b, left, west + 0.012, front, back, 0, height - 0.105, WALL, "112 courtyard wall")
    slab(b, left + jamb, west, front - 0.045, back, 0, d["wall_plinth_top"],
         GRANITE, "112 wall plinth")
    slab(b, left + jamb, west, front - 0.024, back, d["wall_plinth_top"], d["wall_plinth_top"] + 0.025,
         COPING, "112 wall plinth ledge")
    for lower, upper, projection, mat in (
        (d["wall_band_bottom"], d["wall_band_bottom"] + 0.047, 0.034, COPING),
        (d["wall_band_bottom"] + 0.047, height - 0.12, 0.017, WALL),
        (height - 0.105, height - 0.038, 0.030, FRAME),
        (height - 0.038, height, 0.059, COPING),
    ):
        slab(b, left + jamb, west, front - projection, back + projection / 2,
             lower, upper, mat, "112 wall coping course")
    slab(b, left, left + jamb, front - 0.046, back + 0.025, 0.0, d["address_jamb_top"] - 0.04,
         FRAME, "112 numbered terminal jamb")
    slab(b, left - 0.012, left + jamb + 0.012, front - 0.065, back + 0.033,
         d["address_jamb_top"] - 0.04, d["address_jamb_top"], COPING, "112 terminal cap")
    number_x = left + jamb / 2
    # A small unlettered pointed escutcheon sits above the street number.
    shield = Polygon([(-0.095, 0.12), (0.095, 0.12), (0.091, -0.015),
                      (0.060, -0.059), (0, -0.122), (-0.060, -0.059), (-0.091, -0.015)])
    for size, y, mat in ((1.0, front - 0.073, GRANITE), (0.82, front - 0.080, FRAME)):
        outline = affinity.translate(affinity.scale(shield, size, size, origin=(0, 0)),
                                     xoff=number_x, yoff=d["address_jamb_top"] - 0.215)
        face(b, outline, y, front - 0.045, mat, "112 pointed stone escutcheon")
    address_marks(b, "112", 0.244, 0.152,
                  lambda u, z, k: (number_x + u + z * 0.19, front - 0.046 - k, d["address_jamb_top"] - 0.58 + z),
                  NUMERAL, "112 street number", lod)
    # In the 2020 street view the timber slats are set back behind the coping.
    # The neighbouring shop and the continuation beyond the 112 jamb are outside the model.
    bottom, top = d["screen_bottom"], d["screen_top"]
    slats = d["screen_slats"]
    pitch = (top - bottom) / slats
    for i in range(slats):
        z = bottom + i * pitch
        slab(b, left + 0.008, west + 0.02, front + 0.14, front + 0.172,
             z, z + pitch * 0.72, TIMBER[i % 2], "112 slat " + str(i + 1))
    for t in (0.035, 0.53, 0.96):
        x = left + t * (west - left)
        slab(b, x - 0.025, x + 0.025, front + 0.173, front + 0.215,
             height - 0.02, top - 0.018, SUPPORT, "112 screen uprights")


def lane_plate(b, d, lod):
    x = (d["centre_distance"] - d["width"]) / 2
    y = d["depth"] * 0.33
    z = d["height"] * 0.563
    # The green plate faces across the entrance, attached to the west return of the east pier.
    b.box((x - 0.011, y, z), (0.022, 0.366, 0.155), GREEN, label="110 lane-number plate")
    address_marks(b, "110弄", 0.295, 0.083,
                  lambda u, v, k: (x - 0.022 - k, y - u, z + v),
                  WHITE, "110 lane enamel", lod)
    b.box((x - 0.009, y, z - 0.244), (0.017, 0.332, 0.272),
          "Pale lane information plate", label="Lower lane information plate")
