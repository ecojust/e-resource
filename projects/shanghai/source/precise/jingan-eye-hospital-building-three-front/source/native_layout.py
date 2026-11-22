"""Editable views and UV positions for each independently framed, four-vertex pane."""

MAIN = "01 Courtyard southwest bay"
CAMERAS = {
    MAIN: ((-8, -31, 8.8), (0, -0.15, 8.8), 20.7),
    "02 Number and lower sash": ((-4.7, -12, 3.2), (-0.58, -0.52, 3.20), 8.1),
    "03 Middle bow and jambs": ((3.4, -13, 7.45), (0, -0.73, 7.60), 7.5),
    "04 Balcony handrail and vases": ((-3.6, -12, 11.0), (0, -0.55, 11.3), 7.75),
    "05 Pediment and finial": ((-0.9, -16, 16.0), (0, 0.06, 15.49), 8.10),
    "06 Roof and courtyard return": ((6.2, -7.7, 23.0), (0, 0.53, 14.62), 9.1),
}
MATERIALS = (
    "Ground blue curtain",
    "Ground deep reflection",
    "Middle pale curtain",
    "Middle blue reflection",
    "Attic blue reflection",
)
UV_NAME = "2014 sash textile samples"


def uv(material, vertex):
    i = MATERIALS.index(material)
    left = (64 * i + 1.5) / 320
    right = (64 * i + 62.5) / 320
    return [(left, 0.023), (right, 0.023), (right, 0.977), (left, 0.977)][vertex % 4]
