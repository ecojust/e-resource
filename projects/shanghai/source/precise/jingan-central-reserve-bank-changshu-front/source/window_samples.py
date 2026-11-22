"""Crop five small curtain and reflection samples from Antigng's photograph of 7 February 2018."""

import io, hashlib
from pathlib import Path
from PIL import Image

SHA256 = "563c08bbe694564df767b288f7528e41d8ff6b412e0a0c2d4bdf02808e0b7a5e"
# Coordinates are relative to the displayed 1050-pixel-wide complete frame.
SAMPLES = [
    (347.5, 450, 354.2, 474.0),
    (348.2, 280.5, 354.5, 292.8),
    (514.6, 270, 521.9, 280.2),
    (497.7, 124.5, 505.7, 140.0),
    (637.2, 126.5, 647.0, 145.2),
]


def create(data, destination):
    assert hashlib.sha256(data).hexdigest() == SHA256
    with Image.open(io.BytesIO(data)) as img:
        assert img.size == (5312, 2988)
        scale = img.width / 1050
        canvas = Image.new("RGB", (320, 64))
        for i, box in enumerate(SAMPLES):
            crop = img.crop(tuple(round(x * scale) for x in box)).convert("RGB")
            canvas.paste(crop.resize((64, 64), Image.Resampling.BICUBIC), (i * 64, 0))
        canvas.save(destination, optimize=True)


if __name__ == "__main__":
    import sys

    create(Path(sys.argv[1]).read_bytes(), Path(__file__).with_name("window-samples.png"))
