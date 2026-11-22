"""Reproduce the two relief contour files from Legolas1024's 2015 CC BY-SA photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_closing, median_filter
from shapely.geometry import box, mapping
from shapely.ops import unary_union

PHOTO_SHA = "860ff1dfde5cb64b1b85fa95afb2698eccadbf9c7dc1dc16c1d2450342553d19"
PHOTO_URL = "https://commons.wikimedia.org/wiki/File:Tonghanchun_pharmacy,_Renmin_Rd,_Shanghai.jpg"
# Pixel coordinates in the three-times-enlarged crop. The masks exclude balcony and window trim.
CHARACTER_REGIONS = {'童': [(77, 102), (114, 79), (96, 74), (95, 53), (128, 40), (120, 28), (199, 27), (207, 59),
       (181, 64), (188, 71), (222, 69), (228, 95), (200, 101), (203, 126), (183, 156), (179, 164),
       (190, 176), (211, 176), (217, 202), (186, 214), (112, 215), (111, 190), (122, 184),
       (117, 170), (121, 160), (105, 151), (103, 121), (72, 128)],
 '涵': [(82, 282), (111, 280), (124, 306), (118, 335), (101, 336), (95, 349), (107, 338),
       (124, 340), (116, 363), (112, 379), (128, 363), (135, 344), (150, 335), (146, 318),
       (126, 314), (129, 290), (178, 266), (197, 266), (201, 299), (178, 317), (187, 326),
       (182, 344), (194, 339), (204, 328), (212, 341), (205, 363), (220, 342), (233, 351),
       (221, 402), (230, 437), (213, 447), (197, 430), (167, 431), (139, 445), (130, 426),
       (134, 405), (125, 398), (102, 434), (80, 439), (77, 417), (90, 379), (99, 358), (98, 342),
       (83, 321), (80, 308)],
 '春': [(142, 490), (165, 486), (177, 503), (190, 495), (207, 497), (208, 524), (185, 538),
       (181, 549), (207, 547), (219, 557), (217, 578), (207, 581), (218, 594), (243, 614),
       (244, 632), (215, 637), (187, 625), (185, 662), (173, 673), (137, 661), (133, 649),
       (133, 623), (116, 649), (97, 649), (101, 627), (122, 600), (101, 601), (103, 579),
       (125, 562), (107, 574), (101, 556), (137, 539), (113, 543), (105, 520), (145, 505)],
 '堂': [(143, 711), (165, 706), (181, 718), (179, 748), (196, 725), (212, 723), (213, 747),
       (197, 759), (223, 758), (239, 767), (241, 793), (215, 798), (202, 786), (200, 802),
       (190, 824), (208, 827), (208, 848), (190, 856), (213, 854), (216, 886), (113, 892),
       (112, 866), (146, 852), (130, 849), (129, 830), (139, 825), (123, 812), (117, 823),
       (97, 826), (94, 803), (104, 777), (118, 767), (115, 753), (123, 734), (141, 738),
       (150, 751), (151, 737)]}

def outline(mask, min_area, tolerance):
    strips = []
    for row_number, row in enumerate(mask):
        transitions = np.flatnonzero(np.diff(np.r_[False, row, False]))
        for left, right in zip(transitions[::2], transitions[1::2]):
            strips.append(box(int(left), row_number, int(right), row_number + 1))
    merged = unary_union(strips)
    parts = merged.geoms if merged.geom_type == "MultiPolygon" else [merged]
    return unary_union([part.simplify(tolerance, preserve_topology=True)
                        for part in parts if part.area >= min_area])


def crop_rgb(photo, bounds):
    crop = photo.crop(bounds)
    return crop.resize((crop.width * 3, crop.height * 3), Image.Resampling.LANCZOS)


def characters(photo):
    bounds = [347, 481, 454, 785]
    crop = crop_rgb(photo, bounds)
    r, g, b = np.asarray(crop, dtype=float).transpose(2, 0, 1)
    gold = (r - b > 46) & (g - b > 22) & (r > 108) & (g > 72) & (r > g * 1.045)
    out = {}
    for letter, vertices in CHARACTER_REGIONS.items():
        region = Image.new("L", crop.size)
        ImageDraw.Draw(region).polygon(vertices, fill=255)
        mask = binary_closing(gold & (np.asarray(region) != 0), iterations=2)
        shape = outline(mask, 10, 1.0)
        out[letter] = {"pixel_geometry": mapping(shape), "bounds": list(shape.bounds)}
    return {
        "title": "童涵春堂 exterior gold lettering, after the 2015 photograph by Legolas1024",
        "source_original_sha256": PHOTO_SHA, "reference_crop_xyxy": bounds, "coordinate_scale": 3,
        "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "source_url": PHOTO_URL,
        "changes": "Cropped, enlarged, isolated individual strokes and converted to polygon outlines. Foreground wires repaired where adjacent stroke silhouettes establish the contour.",
        "characters": out,
    }


def medallion(photo):
    bounds = [343, 344, 438, 460]
    crop = np.asarray(crop_rgb(photo, bounds), dtype=float)
    y, x = np.indices(crop.shape[:2])
    r, g, b = crop.transpose(2, 0, 1)
    ellipse = ((x - 145) / 81) ** 2 + ((y - 136) / 65) ** 2 < 1
    mask = ellipse & (r - b > 36) & (g - b > 15) & (r > 90)
    badge = binary_closing(median_filter(mask, size=3))
    digits = {}
    for digit, left, top, right, bottom in [
        ("1", 83, 282, 111, 325), ("7", 115, 279, 149, 325),
        ("8", 151, 279, 185, 326), ("3", 191, 279, 225, 326),
    ]:
        region = (x >= left) & (x <= right) & (y >= top) & (y <= bottom)
        mask = region & (r - b > 47) & (g - b > 22) & (r > 109)
        digits[digit] = mapping(outline(binary_closing(mask), 8, .75))
    return {"source_sha256": PHOTO_SHA, "source_crop": bounds, "projection_scale": 3,
            "license": "CC BY-SA 4.0", "author": "Legolas1024",
            "medallion": mapping(outline(badge, 8, .75)), "numerals": digits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path, help="original 800 × 1200 JPEG")
    parser.add_argument("output", type=Path, help="directory for the two contour JSON files")
    args = parser.parse_args()
    if hashlib.sha256(args.original.read_bytes()).hexdigest() != PHOTO_SHA:
        parser.error("photograph SHA-256 differs from the signed 2015 original")
    with Image.open(args.original) as source:
        photo = source.convert("RGB")
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, payload, ascii_only in [
        ("street-name-relief.json", characters(photo), False),
        ("medallion-and-year.json", medallion(photo), True),
    ]:
        (args.output / filename).write_text(
            json.dumps(payload, ensure_ascii=ascii_only, separators=(",", ":")) + chr(10),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
