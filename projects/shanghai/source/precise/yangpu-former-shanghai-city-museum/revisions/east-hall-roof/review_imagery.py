"""Recreate the measured comparison crops from the 36 hash-bound zoom-19 tiles."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw

parser = ArgumentParser()
parser.add_argument("--evidence", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True, help="Private analysis directory for locally generated crops")
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
evidence = json.loads(args.evidence.read_text())
source = evidence["tile_source"]
lng, lat = source["center_wgs84"]
length = 256 * 2 ** 19
global_x = (lng + 180) / 360 * length
global_y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) * length / 2
metres_per_pixel = 2 * math.pi * 6371008.8 * math.cos(math.radians(lat)) / length
releases = sorted({tile["release"] for tile in source["tiles"]})


def fetch(tile):
    local = args.out / ("tile-" + tile["sha256"] + ".jpg")
    if local.exists():
        data = local.read_bytes()
    else:
        request = Request(tile["url"], headers={"User-Agent": "ShanghaiMuseumRoofReview/1.0"})
        with urlopen(request, timeout=45) as response:
            data = response.read()
    if sha256(data).hexdigest() != tile["sha256"] or len(data) != tile["bytes"]:
        raise ValueError("Changed imagery tile: " + tile["url"])
    local.write_bytes(data)
    image = Image.open(BytesIO(data)).convert("RGB")
    if image.size != (256, 256):
        raise ValueError("Unexpected tile dimensions")
    return tile, image


with ThreadPoolExecutor(max_workers=4) as pool:
    checked = list(pool.map(fetch, source["tiles"]))
for release in releases:
    tiles = [(tile, image) for tile, image in checked if tile["release"] == release]
    assert len(tiles) == 9
    x0 = min(t["x"] for t, _ in tiles)
    y0 = min(t["y"] for t, _ in tiles)
    mosaic = Image.new("RGB", (768, 768))
    for tile, image in tiles:
        mosaic.paste(image, ((tile["x"] - x0) * 256, (tile["y"] - y0) * 256))
    scale = .064 / metres_per_pixel
    offset_x = global_x - x0 * 256 - 13 / metres_per_pixel
    offset_y = global_y - y0 * 256 - 19 / metres_per_pixel
    original = mosaic.transform((680, 440), Image.Transform.AFFINE, (scale, 0, offset_x, 0, scale, offset_y), Image.Resampling.BICUBIC)
    crop = original.resize((430, 278), Image.Resampling.LANCZOS)
    crop.save(args.out / ("comparison-" + release + ".png"))
    measurement = next((m for m in evidence["selected_measurements"] if m["imagery_release"] == release), None)
    if measurement:
        sample = measurement["selected_pixels_in_comparison_crop"]
        draw = ImageDraw.Draw(crop)
        draw.rectangle(sample["cover_rectangle"], outline="#d4db40", width=1)
        draw.line([(20, sample["north_parapet_y"]), (sample["east_parapet_x"], sample["north_parapet_y"]), (sample["east_parapet_x"], sample["south_parapet_y"]), (28, sample["south_parapet_y"])], fill="#83ccff", width=1)
        crop.save(args.out / ("measured-" + release + ".png"))
print(f"Verified {len(checked)} source images and reconstructed {len(releases)} releases.")
