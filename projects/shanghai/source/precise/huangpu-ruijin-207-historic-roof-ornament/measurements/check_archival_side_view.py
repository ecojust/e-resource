"""Measure the four roof ornament shadow bands in the independent archive view."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
import numpy as np

EXPECTED = "0e64591c5af1d512c7549152c7af8e28925d1ab3091c3a5cd7ba09338eb62e29"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("side_view", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assert hashlib.sha256(args.side_view.read_bytes()).hexdigest() == EXPECTED
    with Image.open(args.side_view) as image:
        assert image.size == (688, 439)
        luminance = np.asarray(image.convert("L"))
    profile = luminance[103:123, 516:521].mean(axis=1)
    rows = []
    for low, high, sky in [(105,107,104),(109,111,108),(114,116,113),(119,121,117)]:
        y = low + int(np.argmin(profile[low-103:high-102]))
        value = float(profile[y-103])
        lighter = float(profile[sky-103])
        assert lighter - value > 25
        rows.append(dict(dark_row=y,grey_level=value,preceding_light_row=sky,light_level=lighter))
    report = {
        "source_title": "Le Laboratoire Municipal avant de devenir Institut Pasteur entre 1934 et 1938",
        "source_page": "https://wiki.histoire-chine.fr/index.php?title=Il_%C3%A9tait_une_fois..._l%27Institut_Pasteur_de_Shanghai",
        "source_image": "https://wiki.histoire-chine.fr/images/5/5f/Le_Laboratoire_Municipal_avant_de_devenir_Institut_Pasteur_entre_1934_et_1938.jpg",
        "bytes": args.side_view.stat().st_size, "sha256": EXPECTED, "size":[688,439],
        "observation": "Four dark undersides occur on the projecting side of the two upright fins. The low-resolution scan permits band counts at about 1–2 pixels. No reproduction of the scan accompanies these measurements.",
        "mean_column_range_inclusive":[516,520],"native_pixels":rows,
        "comparison":{"original": "https://www.hpcbristol.net/visual/Ro-s018","photographer":"Malcolm Rosholt","catalogue_date":"circa 1938","four_underside_y_px":[149.9,157.8,165.8,173.8]},
        "chronology":"The French history captions this view between 1934 and 1938. Virtual Shanghai building 249 lists 1937. The Bristol catalogue dates the other photograph circa 1938. These dates do not establish a single year of completion."
    }
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
