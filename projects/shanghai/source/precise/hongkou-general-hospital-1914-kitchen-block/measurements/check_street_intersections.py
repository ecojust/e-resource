"""Recompute horizontal intersections and local facade coordinates from measured pixels."""

import json
import math
from pathlib import Path


def fit_point(point, data):
    lon, lat = data["reference_wgs84"]
    lon_scale = data["longitude_metres_per_degree_at_equator"] * math.cos(math.radians(lat))
    lat_scale = data["latitude_metres_per_degree"]
    lines = []
    for ray in point["rays"]:
        camera = data["cameras"][ray["station_view"]]
        width, height = camera["width"], camera["height"]
        focal = width / (2 * math.tan(math.radians(camera["horizontal_fov_degrees"]) / 2))
        u, v = ray["pixel_xy"]
        pitch = math.radians(camera["pitch_up_degrees"])
        forward = math.cos(pitch) - (height / 2 - v) * math.sin(pitch) / focal
        bearing = math.radians(camera["heading_true_degrees"]) + math.atan2((u - width / 2) / focal, forward)
        east, north = math.cos(bearing), -math.sin(bearing)
        station_lon, station_lat = camera["wgs84_estimate"]
        offset = east * (station_lon - lon) * lon_scale + north * (station_lat - lat) * lat_scale
        lines.append((east, north, offset))
    aa = sum(a*a for a, _, _ in lines)
    bb = sum(b*b for _, b, _ in lines)
    ab = sum(a*b for a, b, _ in lines)
    ac = sum(a*c for a, _, c in lines)
    bc = sum(b*c for _, b, c in lines)
    det = aa*bb - ab*ab
    if det <= 1e-9:
        raise ValueError("Sight lines do not determine an intersection")
    x, y = (bb*ac - ab*bc)/det, (aa*bc - ab*ac)/det
    residuals = [a*x + b*y - c for a, b, c in lines]
    assert math.dist((lon + x/lon_scale, lat + y/lat_scale), point["wgs84_estimate"]) < 1e-8
    assert max(abs(a-b) for a, b in zip(residuals, point["signed_cross_track_errors_m"])) < 0.001
    return x, y


def main():
    data = json.loads(Path(__file__).with_name("street-and-courtyard-intersections.json").read_text())
    results = [fit_point(point, data) for point in data["points"]]
    (x0, y0), (x1, y1) = results[:2]
    length = math.dist(results[0], results[1])
    ex, ey = (x1-x0)/length, (y1-y0)/length
    assert abs(length - data["north_face_length_m"]) < 0.001
    assert abs(math.degrees(math.atan2(ex, ey))%360 - data["north_face_westward_bearing_true"]) < 0.001
    for point, (x, y) in zip(data["points"], results):
        dx, dy = x-x0, y-y0
        local = (dx*ex + dy*ey, -dx*ey + dy*ex)
        assert math.dist(local, point["local_axes_m"]) < 0.001
        print(f"{point['feature']}: X={local[0]:.3f} m, Y={local[1]:.3f} m")


if __name__ == "__main__":
    main()
