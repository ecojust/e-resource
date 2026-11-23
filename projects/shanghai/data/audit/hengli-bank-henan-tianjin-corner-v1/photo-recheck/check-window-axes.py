"""Check two surveyed street elevations against the model's photographed window bays."""
from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import subprocess
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


def window_axes(image_bytes, first, last, top, slope):
    image = subprocess.check_output(["magick", "-", "-thumbnail", "780x575", "png:-"], input=image_bytes)
    grayscale = np.asarray(Image.open(BytesIO(image)).convert("L"), dtype=float)
    columns = np.arange(first, last + 1)
    rows = np.rint(top + (columns - first) * slope).astype(int)
    luminance = grayscale[rows[:, None] + np.arange(-7, 8), columns[:, None]].mean(axis=1)
    peaks, _ = find_peaks(-gaussian_filter1d(luminance, 2.1), distance=16, prominence=14)
    return {"image_size": list(reversed(grayscale.shape)), "window_centers_x_px": columns[peaks].tolist(),
            "window_centers_y_px": rows[peaks].tolist(), "count": len(peaks)}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    model = "huangpu-hengli-bank-henan-tianjin-corner"
    source = args.project / "source/precise" / model
    audit = args.project / "data/audit/hengli-bank-henan-tianjin-corner-v1"
    references = json.loads((source / "reference-review.json").read_bytes())
    photos = [item for record in references["sources"] for item in record.get("images", [])]
    guides = {"tianjin-27": (96, 541, 222, -.078, 18), "tianjin-32": (104, 250, 208, -.27, 6)}
    axes = {}
    for photo in photos:
        key = photo["key"]
        if key not in guides:
            continue
        with urlopen(Request(photo["url"], headers={"User-Agent": "Mozilla/5.0"}), timeout=40) as response:
            pixels = response.read()
        assert sha256(pixels).hexdigest() == photo["sha256"]
        *line, count = guides[key]
        axes[key] = {**window_axes(pixels, *line), "source_sha256": photo["sha256"], "url": photo["url"],
                     "sample_line_x_start_x_end_y_start_slope": line}
        assert axes[key]["count"] == count
    with TemporaryDirectory() as scratch:
        actual = Path(scratch) / "surfaces.json"
        manifest = args.project / "assets/models/candidates" / model / "manifest.json"
        subprocess.run(["python", source / "source/check_surfaces.py", "--manifest", manifest, "--out", actual], check=True)
        data = actual.read_bytes()
        assert data == (audit / "surface-checks.json").read_bytes()
    roles = json.loads(data)["results"]
    report = {"model": model, "measured_window_rows": axes, "surface_report_sha256": sha256(data).hexdigest(),
              "surface_probes": {role: values["count"] for role, values in roles.items()},
              "brick_uv_checks": {role: values["brick_uv"]["count"] for role, values in roles.items()}}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
