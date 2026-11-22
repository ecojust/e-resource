"""Rectified curtain and reflection samples from the actual window panes photographed in 2014."""

from pathlib import Path
import hashlib
from PIL import Image

SOURCE = Path(__file__).resolve().parent
PHOTO_SHA = "a0b5665c7a5a24a2208ceb247137dbe8a74ea89a0496aaac9f649b52cdf69553"
# Pixel-sided samples from inside sashes. The upper and lower edges are deliberately
# inside the real frame. They are independent swatches, not a facade photograph.
PANES = {
    "Ground blue curtain": ((390, 674, 399, 699), (391, 705, 399, 734)),
    "Ground deep reflection": ((427, 672, 435, 700), (427, 707, 436, 733)),
    "Middle pale curtain": ((412, 435, 422, 455), (413, 462, 422, 479)),
    "Middle blue reflection": ((445, 437, 452, 456), (445, 464, 452, 478)),
    "Attic blue reflection": ((409, 235, 418, 243), (422, 247, 427, 252)),
}


def create(photo):
    photo = Path(photo)
    assert hashlib.sha256(photo.read_bytes()).hexdigest() == PHOTO_SHA
    with Image.open(photo) as original:
        assert original.size == (1350, 900)
        atlas = Image.new("RGB", (320, 64))
        for index, spans in enumerate(PANES.values()):
            for j, span in enumerate(spans):
                patch = (
                    original.crop(span).convert("RGB").resize((64, 32), Image.Resampling.BICUBIC)
                )
                atlas.paste(patch, (64 * index, 32 * j))
        atlas.save(SOURCE / "curtain-samples.png", optimize=True)
    return hashlib.sha256((SOURCE / "curtain-samples.png").read_bytes()).hexdigest()


if __name__ == "__main__":
    import sys

    print(create(sys.argv[1]))
