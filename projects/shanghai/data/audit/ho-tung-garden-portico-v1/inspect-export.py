"""Inspect the decoded garden portico and its cast shadows with the project CPU z-buffer."""

import argparse, ctypes, hashlib, json, runpy, struct, subprocess, tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
READER = HERE.parent / "postal-office-v1/independent-glb-review-helpers.py"
RASTER = HERE.parent / "weile-garden-gate-v1/default-source-visibility/raster.cpp"


def unit(v):
    return v / np.linalg.norm(v)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(draw, tri, eye, target, span, width, height):
    eye = np.asarray(eye, float)
    axis = unit(np.asarray(target) - eye)
    right = unit(np.cross(axis, [0, 0, 1]))
    up = np.cross(right, axis)
    basis = np.array([right, up, axis]).T
    f = width * np.linalg.norm(target - eye) / span
    coords = np.zeros((*tri.shape[:2], 5), dtype=np.float64)
    coords[:, :, :3] = (tri - eye) @ basis
    hits = np.zeros((height, width), np.int32)
    depth = np.zeros_like(hits, dtype=np.float32)
    tags = np.arange(1, len(tri) + 1, dtype=np.int32)
    clip = np.zeros(len(tri), np.int32)
    mask = np.zeros(4, dtype=np.float64)
    draw(
        width,
        height,
        width / 2,
        height / 2,
        f,
        len(tri),
        coords.ctypes.data,
        tags.ctypes.data,
        clip.ctypes.data,
        mask.ctypes.data,
        0,
        depth.ctypes.data,
        hits.ctypes.data,
    )
    return hits, depth, basis, f


def main(mesh, out):
    tri, ids, names, asset = runpy.run_path(str(READER))["load_triangles"](mesh)
    with mesh.open("rb") as stream:
        stream.seek(12)
        size, kind = struct.unpack("<II", stream.read(8))
        assert kind == 0x4E4F534A
        doc = json.loads(stream.read(size))
    colors = np.array([m["pbrMetallicRoughness"]["baseColorFactor"][:3] for m in doc["materials"]])
    assert not doc.get("images") and not doc.get("textures")
    clear = names.index("Clear garden transom glass")
    alpha = doc["materials"][clear]["pbrMetallicRoughness"]["baseColorFactor"][3]
    assert doc["materials"][clear]["alphaMode"] == "BLEND" and abs(alpha - 0.25) < 1e-6
    opaque = np.flatnonzero(ids != clear)
    normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-12)
    cameras = json.loads((HERE / "inspection-cameras.json").read_bytes())
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    light = np.array([-18.0, -22.0, 24.0])
    focus = np.array([0.0, 1.5, 4.0])
    with tempfile.TemporaryDirectory() as temp:
        so = Path(temp) / "raster.so"
        subprocess.run(["c++", "-O2", "-fPIC", "-shared", RASTER, "-o", so], check=True)
        draw = ctypes.CDLL(str(so)).draw
        i, d, p = ctypes.c_int, ctypes.c_double, ctypes.c_void_p
        draw.argtypes = [i, i, d, d, d, i, p, p, p, p, i, p, p]
        draw.restype = None
        sc = 760
        _, shadow, light_basis, lf = project(draw, tri[opaque], light, focus, 17.2, sc, sc)
        for camera in cameras:
            eye = np.array(camera["eye"])
            target = np.array(camera["target"])
            w, h = 648 * 2, 568 * 2
            hits, depth, basis, f = project(draw, tri, eye, target, camera["width_m"], w, h)
            y, x = np.nonzero(hits)
            face = hits[y, x] - 1
            assert len(face) > 0.025 * w * h
            through = np.flatnonzero(ids[face] == clear)
            backing = None
            if len(through):
                second, _, _, _ = project(draw, tri[opaque], eye, target, camera["width_m"], w, h)
                backing = second[y[through], x[through]] - 1
            image = np.full((h, w, 3), [231, 232, 227], dtype=np.uint8)
            for start in range(0, len(x), 45000):
                s = slice(start, start + 45000)
                ix, iy = x[s], y[s]
                visible = face[s]
                rays = (
                    np.stack(
                        [(ix + 0.5 - w / 2) / f, (h / 2 - iy - 0.5) / f, np.ones(len(ix))], axis=1
                    )
                    @ basis.T
                )
                pos = eye + rays / depth[iy, ix, None]
                lv = (pos - light) @ light_basis
                lx = np.clip(np.floor(sc / 2 + lf * lv[:, 0] / lv[:, 2]).astype(int), 0, sc - 1)
                ly = np.clip(np.floor(sc / 2 - lf * lv[:, 1] / lv[:, 2]).astype(int), 0, sc - 1)
                reference = 1 / np.maximum(shadow[ly, lx], 1e-9)
                sun = lv[:, 2] <= reference + 0.046
                ndotl = np.maximum(0, normal[visible] @ unit(light - focus))
                linear = colors[ids[visible]] * (0.49 + 0.62 * ndotl * sun)[:, None]
                srgb = np.where(
                    linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055
                )
                image[iy, ix] = np.clip(np.rint(srgb * 255), 0, 255).astype(np.uint8)
            if len(through):
                # Composite the translucent fanlight over its first opaque surface or the studio.
                background = np.tile(np.array([231.0, 232.0, 227.0]) / 255, (len(through), 1))
                active = backing >= 0
                farther = opaque[backing[active]]
                linear = (
                    colors[ids[farther]]
                    * (0.49 + 0.62 * np.maximum(0, normal[farther] @ unit(light - focus)))[:, None]
                )
                background[active] = np.where(
                    linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055
                )
                tx, ty = x[through], y[through]
                image[ty, tx] = np.clip(
                    np.rint(image[ty, tx] * alpha + 255 * background * (1 - alpha)), 0, 255
                ).astype(np.uint8)
            path = out / (camera["name"] + ".jpg")
            Image.fromarray(image).resize((w // 2, h // 2), Image.Resampling.LANCZOS).save(
                path, quality=91
            )
            counts = np.bincount(ids[face], minlength=len(names))
            rows.append(
                dict(
                    **camera,
                    file=path.name,
                    image_sha256=sha(path),
                    visible_antialias_samples=len(face),
                    translucent_samples=len(through),
                    material_samples={k: int(v) for k, v in zip(names, counts) if v},
                )
            )
    (out / "views.json").write_text(
        json.dumps(
            dict(
                model=asset, triangles=len(tri), reader=sha(READER), raster=sha(RASTER), views=rows
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    main(args.decoded, args.out)
