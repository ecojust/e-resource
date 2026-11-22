"""The 慢 symbol in the 2015 photograph, traced as a raised enamel silhouette."""

import json
from pathlib import Path
from hashlib import sha256
from io import BytesIO

SOURCE = Path(__file__).resolve().parent


def trace(original):
    import numpy as np
    from contourpy import contour_generator
    from PIL import Image, ImageFilter
    from shapely.geometry import Polygon, mapping
    from plaque_samples import SOURCE_SHA256

    assert sha256(original).hexdigest() == SOURCE_SHA256
    # The lens sees this sideways. Ellipse centre and radii are in the study crop
    # at twice the original pixel scale. The y coordinate runs up on the sign.
    im = Image.open(BytesIO(original)).convert("RGB").crop((2030, 2390, 2190, 2660))
    img = np.asarray(
        im.resize((320, 540), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(0.45))
    ).astype(float)
    # Red-channel luminance separates the dark left vertical stroke from the
    # shaded ochre background. Chroma alone also picks up the brown fringe.
    score = img[:, :, 0]
    score[:168, :] = 150
    score[374:, :] = 150
    score[:, :133] = 150
    score[:, 202:] = 150
    field = contour_generator(
        x=(np.arange(320) - 162.5) / 55.5,
        y=(270.0 - np.arange(540)) / 193.0,
        z=score,
        fill_type="OuterOffset",
    )
    vertices, separators = field.filled(-1, 95.0)
    shapes = []
    for pts, starts in zip(vertices, separators):
        rings = [pts[p:q] for p, q in zip(starts, starts[1:])]
        poly = Polygon(rings[0], rings[1:]).simplify(0.007, preserve_topology=True)
        if poly.area > 0.0017:
            assert poly.is_valid
            shapes.append(mapping(poly))
    data = dict(
        photograph_sha256=SOURCE_SHA256,
        artist="Livelikerw",
        license="CC BY-SA 4.0",
        image="522 Jiaozhou Rd. Shanghai.JPG",
        silhouettes=shapes,
    )
    (SOURCE / "caution-strokes.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    )


def add_sign(b, lod):
    from shapely.geometry import Point, shape
    from shapely.affinity import scale, translate
    from gate_stone import IRON

    # Right-facing inner return of the left pier. Y runs away from the street.
    centre_y = 0.111
    centre_z = 0.631
    radius = 0.095
    plane = lambda y, z, d: (-0.500 + d, y, z)
    n = 14 if lod else 28
    circle = Point(centre_y, centre_z).buffer(radius, quad_segs=n)
    b.prism(circle, 0, 0.006, plane, IRON, "Left reveal / black circular sign rim")
    face = Point(centre_y, centre_z).buffer(radius * 0.83, quad_segs=n)
    b.prism(
        face, 0.006, 0.007, plane, "Ochre yellow sign enamel", "Left reveal / enamel caution disc"
    )
    for item in json.loads((SOURCE / "caution-strokes.json").read_bytes())["silhouettes"]:
        # Right is into the yard as seen looking directly at the inner face.
        glyph = translate(
            scale(shape(item), xfact=radius, yfact=radius * 0.991, origin=(0, 0)),
            xoff=centre_y,
            yoff=centre_z,
        )
        b.prism(glyph, 0.007, 0.0075, plane, IRON, "Left reveal / photographed slow character")


if __name__ == "__main__":
    import sys

    trace(Path(sys.argv[1]).read_bytes())
