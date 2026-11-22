"""Read the material-indexed UVs and exact photograph-derived PNG from all export variants."""

from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = PROJECT / "source/precise/jingan-central-reserve-bank-changshu-front/source"
NAMES = (
    "Ground brown curtain",
    "Pale drape",
    "Reflected winter branches",
    "Upper grey curtain",
    "Upper brown curtain",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def examine(path, atlas):
    blob = path.read_bytes()
    length, tag = struct.unpack_from("<II", blob, 12)
    assert tag == 0x4E4F534A
    doc = json.loads(blob[20 : 20 + length])
    buf = memoryview(blob)[28 + length :]
    assert len(doc["images"]) == 1
    im = doc["images"][0]
    v = doc["bufferViews"][im["bufferView"]]
    start = v.get("byteOffset", 0)
    assert im["mimeType"] == "image/png" and digest(buf[start : start + v["byteLength"]]) == atlas
    rows = {}

    def vals(ai):
        ac = doc["accessors"][ai]
        view = doc["bufferViews"][ac["bufferView"]]
        types = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
        dt = np.dtype(types[ac["componentType"]])
        c = {"VEC2": 2, "SCALAR": 1}[ac["type"]]
        vec = np.ndarray(
            (ac["count"], c),
            dt,
            buf,
            view.get("byteOffset", 0) + ac.get("byteOffset", 0),
            (view.get("byteStride", c * dt.itemsize), dt.itemsize),
        )
        return vec.astype(float) / np.iinfo(dt).max if ac.get("normalized") else vec

    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            mat = doc["materials"][prim["material"]]
            name = mat["name"]
            tex = mat["pbrMetallicRoughness"].get("baseColorTexture")
            if name not in NAMES:
                assert tex is None
                continue
            assert tex and doc["textures"][tex["index"]]["source"] == 0
            ids = vals(prim["indices"]).ravel().astype(int)
            uv = vals(prim["attributes"]["TEXCOORD_0"])[ids]
            i = NAMES.index(name)
            x = [(64 * i + 0.5) / 320, (64 * i + 63.5) / 320]
            assert all(np.min(np.abs(uv[:, 0] - v)) < 0.0001 for v in x)
            assert np.all((uv[:, 0] >= x[0] - 0.0001) & (uv[:, 0] <= x[1] + 0.0001)) and np.all(
                (uv[:, 1] > 0.006) & (uv[:, 1] < 0.994)
            )
            rec = rows.setdefault(name, dict(triangles=0))
            rec["triangles"] += len(ids) // 3
            rec["horizontal_interval"] = x
    assert set(rows) == set(NAMES) and sum(v["triangles"] for v in rows.values()) == 140
    return dict(sha256=digest(blob), glazing=rows, embedded_image_sha256=atlas)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    atlas = digest((SOURCE / "window-samples.png").read_bytes())
    out = {
        k: examine(args.directory / v, atlas)
        for k, v in [("raw", "raw.glb"), ("full", "decoded-full.glb"), ("lod", "decoded-lod.glb")]
    }
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(atlas)
