"""Cameras in metres and per-plate UV positions in the rectified 2015 atlas."""

MAIN = "01 Street face"
CAMERAS = {
    "01 Street face": ((-0.85, -13.5, 3.35), (0, 0.18, 3.18), 6.53),
    "02 Springers and iron fan": ((-0.4, -8, 5.08), (0, 0.12, 4.97), 5.7),
    "03 Brick pier and address": ((-0.05, -5.5, 2.59), (-2.19, 0.04, 2.68), 2.25),
    "04 Heritage plaque and hinge": ((3.5, -5.6, 2.42), (2.12, 0.03, 2.51), 2.13),
    "05 Pierced moving leaves": ((1.0, -7, 1.72), (-0.15, 0.43, 1.78), 4.9),
    "06 Courtyard and hinge depth": ((5.75, 5.28, 7.49), (0, 0.5, 2.96), 7.1),
}
MATERIALS = ("Bronze activity centre plaque", "Bronze 522 address plaque", "Pale heritage plaque")
UV_NAME = "2015 street plaques"


def uv(material, vertex):
    index = MATERIALS.index(material)
    left = (128 * index + 0.5) / 384
    right = (128 * index + 127.5) / 384
    return [(left, 0.005), (right, 0.005), (right, 0.995), (left, 0.995)][vertex % 4]
