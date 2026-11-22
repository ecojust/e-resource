"""Rectify the three front-facing nameplates in Livelikerw's 2015 entrance photograph."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE_SHA256 = "683eab026bec0f1ed018b4a4a7b5c27a6c0ca85838f22f690ed1bbc8f0271ada"
TILES = {
    "Bronze activity centre plaque": [(29, 505), (28, 556), (103, 552), (103, 503)],
    "Bronze 522 address plaque": [(43, 566), (42, 592), (89, 589), (89, 563)],
    "Pale heritage plaque": [(586, 530), (589, 593), (666, 588), (664, 526)],
}


def original_point(x, y):
    # Coordinates on the 725-by-909 inspection crop, referenced to the full 4912-by-3264 frame.
    return (1800 + x * 1710 / 725, 1120 + y * 2144 / 909)


def build(original_bytes):
    assert sha256(original_bytes).hexdigest() == SOURCE_SHA256
    with Image.open(BytesIO(original_bytes)) as original:
        assert original.size == (4912, 3264)
        atlas = Image.new("RGB", (384, 96))
        for i, points in enumerate(TILES.values()):
            quad = tuple(c for point in points for c in original_point(*point))
            patch = original.convert("RGB").transform(
                (128, 96), Image.Transform.QUAD, quad, resample=Image.Resampling.BICUBIC
            )
            atlas.paste(patch, (i * 128, 0))
    atlas.save(HERE / "entrance-plaques.png", optimize=True)


if __name__ == "__main__":
    import sys

    build(Path(sys.argv[1]).read_bytes())
