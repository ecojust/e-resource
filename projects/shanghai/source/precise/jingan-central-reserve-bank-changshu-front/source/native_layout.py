"""Saved cameras, glazing material names and the UV atlas convention."""

MAIN = "01 Garden entrance front"
CAMERAS = {
    MAIN: ((-2.3, -38.5, 10.8), (0, 0.5, 10.4), 24.0),
    "02 Carved door and stone steps": ((-0.65, -16, 4.12), (0, 0.20, 3.69), 8.15),
    "03 Central splayed balcony": ((4.7, -13.7, 9.93), (0, -0.3, 7.13), 6.2),
    "04 Upper stone balusters": ((-4.3, -13.9, 15.14), (0, -0.12, 14.16), 6.0),
    "05 Two cornices and attic": ((10.3, -18.8, 21.4), (1.4, 1.1, 16.3), 14.7),
    "06 East return and side sashes": ((18.2, -12.2, 11.7), (7.32, 1.66, 9.1), 18.8),
}
MATERIALS = (
    "Ground brown curtain",
    "Pale drape",
    "Reflected winter branches",
    "Upper grey curtain",
    "Upper brown curtain",
)
UV_NAME = "2018 independent pane samples"


def uv(material, vertex):
    i = MATERIALS.index(material)
    left = (64 * i + 0.5) / 320
    right = (64 * i + 63.5) / 320
    return [(left, 0.992), (right, 0.992), (right, 0.008), (left, 0.008)][vertex % 4]
