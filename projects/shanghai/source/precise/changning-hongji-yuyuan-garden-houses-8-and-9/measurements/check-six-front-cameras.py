"""Reproject the six front-gable photographs at their native upright pixel sizes.

Run without arguments to use the published measurements. Repeat --photos with photo
directories to also check the six original file digests, dimensions and orientations.
Use --output to save the full residual table.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rms(distances):
    return float(np.sqrt(np.mean(np.square(distances))))


def original(tag, camera, directories):
    from PIL import Image

    path = next(folder / (tag + ".jpg") for folder in directories if (folder / (tag + ".jpg")).is_file())
    if sha(path) != camera["sha256"]:
        raise ValueError(f"The {tag} original file digest differs")
    with Image.open(path) as image:
        orientation = image.getexif().get(274, 1)
        size = image.size[::-1] if orientation in (5, 6, 7, 8) else image.size
    assert list(size) == camera["upright_pixels"]
    if tag == "commons-00":
        assert orientation == 3
    return {"sha256": camera["sha256"], "upright_pixels": size, "exif_orientation": orientation}


def check_camera(tag, camera, number, dimensions, directories):
    width, overhang, front, eave, rise = dimensions
    model = {
        "left eave outer tip": (-overhang, -front, eave),
        "ridge end": (width / 2, -front, eave + rise),
        "right eave outer tip": (width + overhang, -front, eave),
        "left wall foot": (0, 0, 0), "right wall foot": (width, 0, 0),
    }
    matrix = np.array(camera["world_to_upright_pixel_camera"], dtype=float)
    eye = np.linalg.solve(matrix[:, :3], -matrix[:, 3])
    assert np.allclose(eye, camera["estimated_eye_local_m"], rtol=0, atol=1.e-5)
    assert eye[1] < -front and abs(np.linalg.det(matrix[:, :3])) > 1.e-6
    image_size = np.array(camera["upright_pixels"])
    gable_errors, window_pairs, window_errors, rows = [], [], [], []
    for mark in camera["landmarks"]:
        name = mark["landmark"]
        xyz, uv = np.array(mark["xyz"]), np.array(mark["uv"])
        homogeneous = matrix @ np.r_[xyz, 1.]
        assert homogeneous[2] > 0 and np.all((uv >= 0) & (uv < image_size))
        projected = homogeneous[:2] / homogeneous[2]
        delta = projected - uv
        error = float(np.linalg.norm(delta))
        if name == "upper edge of window frame":
            assert 0 < xyz[0] < width and xyz[1] == 0 and 0 < xyz[2] < eave
            window_pairs.append((xyz, uv))
            window_errors.append(error)
        else:
            assert np.allclose(xyz, model[name], rtol=0, atol=1.e-6)
            gable_errors.append(error)
        rows.append({"landmark": name, "xyz_m": xyz.tolist(), "observed_px": uv.tolist(),
                     "projected_px": projected.tolist(), "residual_xy_px": delta.tolist(),
                     "distance_px": error})
    assert len(window_pairs) == (8 if number == "8" else 12)
    assert len(gable_errors) == (4 if tag == "winter2023-18" else 5)
    # The stored gable errors were rounded to 0.01 study pixels, at quarter size for Commons.
    tolerance = .021 if tag == "commons-00" else .0051
    assert np.allclose(gable_errors, camera["gable_residuals_native_px"], rtol=0, atol=tolerance)
    assert abs(rms(window_errors) - camera["window_rt_mean_square_root_native_px"]) < 1.e-6
    openings = []
    for (left, left_uv), (right, right_uv) in zip(window_pairs[::2], window_pairs[1::2]):
        clear_width = float(right[0] - left[0])
        assert 0 < clear_width < width and left_uv[0] < right_uv[0]
        openings.append({"width_m": clear_width, "width_over_facade_width": clear_width / width,
                         "measured_pixel_span": float(np.linalg.norm(right_uv - left_uv))})
    return {"source_sha256": camera["sha256"], "upright_pixels": image_size.tolist(),
            "source_file_check": original(tag, camera, directories) if directories else None,
            "eye_local_m": eye.tolist(), "points": rows, "opening_upper_edges": openings,
            "gable_rms_px": rms(gable_errors), "window_rms_px": rms(window_errors),
            "all_points_rms_px": rms(gable_errors + window_errors)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photos", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    survey_path = HERE / "six-front-cameras.json"
    survey = read(survey_path)
    layout_path = HERE.parent / "source/garden-layout.json"
    layout = read(layout_path)
    aerial_path = HERE / survey["independent_aerial_reference"]
    aerial = read(aerial_path)
    houses = {}
    axes = {}
    for number, house in survey["houses"].items():
        dim = house["dimensions_m"]
        assert np.allclose([layout[number][k] for k in survey["dimension_order"]], dim, rtol=0, atol=5.1e-5)
        frame = layout[number]["garden_transform"]
        assert frame == aerial["houses"][number]
        x, y = (np.array(frame[f"local_{axis}_unit_EN"]) for axis in ("X", "Y"))
        assert abs(np.linalg.det([x, y]) - 1.) < 1.e-5 and abs(x @ y) < 1.e-5
        axes[number] = {"outward": -y, "mid": np.array(frame["front_midpoint"]["garden_ENU_m"])}
        plan_width = frame["apparent_main_wall_width_m"]
        assert abs(dim[0] - plan_width) <= aerial["uncertainty"]["independent_width_m"]
        cameras = {tag: check_camera(tag, cam, number, dim, args.photos) for tag, cam in house["views"].items()}
        assert len(cameras) == 3
        houses[number] = {"face_width_m": dim[0], "aerial_width_m": plan_width,
                          "width_ratio_to_aerial": dim[0] / plan_width, "cameras": cameras}
    toward_nine = axes["9"]["mid"] - axes["8"]["mid"]
    assert axes["8"]["outward"] @ toward_nine > 0 and axes["9"]["outward"] @ toward_nine < 0
    assert axes["8"]["outward"] @ axes["9"]["outward"] < -.99
    result = {"survey_sha256": sha(survey_path), "layout_sha256": sha(layout_path),
              "independent_aerial_sha256": sha(aerial_path), "native_upright_pixels": True,
              "outward_normals_dot": float(axes["8"]["outward"] @ axes["9"]["outward"]),
              "houses": houses, "passed": True}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
