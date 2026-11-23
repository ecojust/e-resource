"""Re-read the same four small ground areas in two dated Wayback ortho mosaics.

Supply a private directory of original tile downloads named by SHA-256. The
manifest records public source URLs and checksums. Optional --fetch downloads
missing data; the output is numerical and contains no source photograph.
"""
import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from tempfile import NamedTemporaryFile
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image, ImageDraw


def tile_image(tile, cache, fetch):
    path = cache / tile["sha256"]
    if not path.exists() and fetch:
        request = Request(tile["url"], headers={"User-Agent": "GIS field verification/1.0"})
        with urlopen(request, timeout=20) as response:
            data = response.read()
        if sha256(data).hexdigest() != tile["sha256"]:
            raise ValueError(f"Source tile changed at {tile['url']}")
        with NamedTemporaryFile(dir=cache, delete=False) as temporary:
            temporary.write(data)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary.name, path)
    data = path.read_bytes()
    if sha256(data).hexdigest() != tile["sha256"]:
        raise ValueError(f"Private cache does not match {path.name}")
    return Image.open(BytesIO(data)).convert("RGB")


def read_period(period, areas, origin, size, cache, fetch):
    mosaic = Image.new("RGB", tuple(size))
    for tile in period["tiles"]:
        x, y, level = tile["xyz"]
        if level != 19:
            raise ValueError("The same zoom level is required for both periods")
        mosaic.paste(tile_image(tile, cache, fetch), (x * 256 - origin[0], y * 256 - origin[1]))
    rgb = np.asarray(mosaic, dtype=np.int16)
    result = {}
    for key, points in areas.items():
        mask = Image.new("1", mosaic.size)
        ImageDraw.Draw(mask).polygon([tuple(point) for point in points], fill=1)
        sample = rgb[np.asarray(mask, dtype=bool)]
        red = (sample[:, 0] - sample[:, 1] > 13) & (sample[:, 0] - sample[:, 2] > 22)
        result[key] = {"sample_pixels": len(sample), "median_rgb": np.median(sample, axis=0).tolist(),
                       "warm_pixel_fraction": round(float(red.mean()), 5)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    manifest_path = Path(__file__).with_name("2013-2019-roof-periods.json")
    source = json.loads(manifest_path.read_bytes())
    args.cache.mkdir(exist_ok=True, parents=True)
    checks = {period["acquisition"]: read_period(period, source["sample_polygons_px"], source["global_pixel_origin"],
              source["size"], args.cache, args.fetch) for period in source["periods"]}
    report = {"manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(), "periods": checks,
              "scope": "Same-position image-colour comparison. It cannot establish roof survival, demolition, phase of work or dormer identity."}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
