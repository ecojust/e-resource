"""Reconstruct balcony survey points from three calibrated photographs.

Run with NumPy. Pass --photos DIRECTORY to also verify the three original
calibrated photographs named street-1-202101.jpg through street-3-202101.jpg.
"""

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
ORIGIN = np.array([121.4721, 31.21775])
METRES = 111198 * np.array([math.cos(math.radians(ORIGIN[1])), 1.0])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def station_ray(camera, pixel):
    pitch = math.radians(camera["pitch"])
    azimuth = math.radians(camera["az"])
    focal = camera["width"] / (2 * math.tan(math.radians(camera["hfov"] / 2)))
    x = (pixel[0] - camera["width"] / 2) / focal
    y = (camera["height"] / 2 - pixel[1]) / focal
    horizontal = math.cos(pitch) - y * math.sin(pitch)
    bearing = azimuth + math.atan2(x, horizontal)
    elevation = math.atan2(math.sin(pitch) + y * math.cos(pitch),
                           math.hypot(x, horizontal))
    normal = np.array([math.cos(bearing), -math.sin(bearing)])
    position = (np.array(camera["station"]["position"]) - ORIGIN) * METRES
    return normal, position, elevation, bearing


def intersection(cameras, pixels):
    rays = [station_ray(camera, pixel) for camera, pixel in zip(cameras, pixels)]
    normals = np.stack([normal for normal, *_ in rays])
    offsets = [normal @ position for normal, position, *_ in rays]
    xy = np.linalg.lstsq(normals, offsets, rcond=None)[0]
    observations = []
    for (normal, position, elevation, bearing), camera in zip(rays, cameras):
        distance = np.linalg.norm(xy - position)
        observations.append({
            "bearing_deg": round(math.degrees(bearing) % 360, 2),
            "horizontal_residual_m": round(float(normal @ (xy - position)), 2),
            "horizontal_distance_m": round(float(distance), 2),
            "height_m": round(math.tan(elevation) * distance + camera["station"]["height"], 2),
        })
    return ORIGIN + xy / METRES, observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photos", type=Path)
    args = parser.parse_args()
    survey = json.loads((ROOT / "three-station-dimensions.json").read_bytes())
    cameras = []
    for original, reference in sorted(survey["references"].items()):
        metadata = ROOT / f'baidu-{reference["station_id"]}.json'
        assert sha(metadata) == reference["metadata_sha256"], metadata
        camera = json.loads(metadata.read_bytes())
        assert camera["photo_sha256"] == reference["photo_sha256"]
        if args.photos:
            photo = args.photos / Path(original).with_suffix(".jpg")
            assert sha(photo) == camera["photo_sha256"], photo
        cameras.append(camera)
    assert len(cameras) == 3
    locations = {}
    for label, recorded in survey["point_measurements"].items():
        position, observations = intersection(cameras, recorded["points"])
        np.testing.assert_allclose(position, recorded["wgs84"], rtol=0, atol=1e-10)
        assert observations == recorded["rays"], label
        assert statistics.median(o["height_m"] for o in observations) == recorded["median_height_m"]
        locations[label] = position
    centre = locations["inscription midpoint"]
    along = (locations["front right base"] - locations["front left base"]) * METRES
    width = np.linalg.norm(along)
    x = along / width
    basis = np.stack([x, [-x[1], x[0]]])
    for label, location in locations.items():
        derived = basis @ ((location - centre) * METRES)
        np.testing.assert_allclose(derived, survey["point_measurements"][label]["model_xy_m"],
                                   rtol=0, atol=1e-8)
    heading = math.degrees(math.atan2(-x[1], x[0]))
    np.testing.assert_allclose([width, heading], [survey["front_width_m"], survey["model_heading_deg"]],
                               rtol=0, atol=1e-8)
    print(json.dumps({"control_points": len(locations), "stations": len(cameras),
                      "centre_wgs84": centre.tolist(), "front_width_m": width,
                      "model_heading_deg": heading}, indent=2))


if __name__ == "__main__":
    main()
