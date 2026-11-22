"""Check oriented position/UV triples and embedded PNGs in the three dated mesh pairs."""
import argparse
import hashlib
import json
import mmap
import struct
from pathlib import Path

import numpy as np


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Model:
    def __init__(self, path):
        self.sha256 = file_sha(path)
        with path.open("rb") as stream:
            self.data = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
        magic, version, size, json_bytes, chunk = struct.unpack_from("<4sIIII", self.data)
        assert (magic, version, size, chunk) == (b"glTF", 2, len(self.data), 0x4E4F534A)
        self.doc = json.loads(self.data[20:20 + json_bytes])
        size, kind = struct.unpack_from("<II", self.data, 20 + json_bytes)
        self.bin = 28 + json_bytes
        assert kind == 0x004E4942 and self.bin + size == len(self.data)

    def accessor(self, index):
        a = self.doc["accessors"][index]
        v = self.doc["bufferViews"][a["bufferView"]]
        assert not a.get("sparse") and not a.get("normalized") and v["buffer"] == 0
        counts = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}
        types = {5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
        count, dtype = counts[a["type"]], np.dtype(types[a["componentType"]])
        offset = self.bin + v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.ndarray((a["count"], count), dtype, self.data, offset,
                          strides=(v.get("byteStride", count*dtype.itemsize), dtype.itemsize))

    def image(self, material, source):
        info = material["pbrMetallicRoughness"].get("baseColorTexture")
        if info is None:
            return None
        assert info.get("texCoord", 0) == 0
        tex = self.doc["textures"][info["index"]]
        im = self.doc["images"][tex["source"]]
        v = self.doc["bufferViews"][im["bufferView"]]
        assert v["buffer"] == 0 and im["mimeType"] == "image/png" and "uri" not in im
        start = self.bin + v.get("byteOffset", 0)
        image = self.data[start:start + v["byteLength"]]
        assert image[:8] == b"\x89PNG\r\n\x1a\n"
        name = im["name"]
        assert Path(name).name == name
        digest = hashlib.sha256(image).hexdigest()
        assert digest == file_sha(source/name)
        return {"file": name, "bytes": len(image), "sha256": digest}

    def textures(self, source):
        result = {}
        for mat in self.doc["materials"]:
            im = self.image(mat, source)
            if im:
                result[mat["name"]] = im
        assert len(result) == len(self.doc["images"])
        return result

    def surfaces(self, source):
        by_material = {}
        primitive_count = {}
        nonzero = {}
        texture = self.textures(source)
        nodes = self.doc["nodes"]
        assert len(nodes) == 1 and nodes[0]["mesh"] == 0
        assert not ({"matrix", "translation", "rotation", "scale"} & nodes[0].keys())
        for prim in self.doc["meshes"][0]["primitives"]:
            assert prim.get("mode", 4) == 4
            name = self.doc["materials"][prim["material"]]["name"]
            attrs = prim["attributes"]
            assert ("TEXCOORD_0" in attrs) == (name in texture)
            positions = self.accessor(attrs["POSITION"])
            indices = self.accessor(prim["indices"]).reshape(-1, 3)
            coords = positions
            if name in texture:
                uv = self.accessor(attrs["TEXCOORD_0"])
                coords = np.concatenate([positions, uv], axis=1)
                sampled = uv[indices].astype(np.float64)
                a, b = sampled[:, 1] - sampled[:, 0], sampled[:, 2] - sampled[:, 0]
                nonzero[name] = nonzero.get(name, 0) + int(np.count_nonzero(a[:, 0]*b[:, 1] != a[:, 1]*b[:, 0]))
            assert np.isfinite(coords).all() and coords.dtype == np.dtype("<f4")
            faces = coords[indices]
            faces[faces == 0] = 0  # Equivalent IEEE signed zero has the same geometric value.
            stride = 3 * coords.shape[1] * 4
            key_type = np.dtype("S" + str(stride))
            def cycled(k):
                return np.ascontiguousarray(np.roll(faces, -k, axis=1)).reshape(len(faces), -1).view(key_type).reshape(-1)
            best = cycled(0)
            for k in (1, 2):
                r = cycled(k)
                np.copyto(best, r, where=r < best)
            by_material.setdefault(name, []).append(best)
            primitive_count[name] = primitive_count.get(name, 0) + len(faces)
        result = {}
        for name, blocks in sorted(by_material.items()):
            ordered = np.concatenate(blocks)
            ordered.sort()
            row = {"triangles": primitive_count[name], "oriented_corner_sha256": hashlib.sha256(ordered).hexdigest()}
            if name in texture:
                row.update(texture=texture[name], textured_corners=3*len(ordered),
                           nondegenerate_texture_triangles=nonzero[name])
            result[name] = row
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exports", type=Path)
    parser.add_argument("packaged", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent.parent/"source"
    manifest_file = args.packaged/"manifest.json"
    manifest = json.loads(manifest_file.read_bytes())
    results = {}
    for role in ("full", "lod", "historic"):
        data = manifest["assets"][role]
        a = Model(args.exports/(role+"-source.glb"))
        b = Model(args.packaged/("decoded-"+role+".glb"))
        web = Model(args.packaged/data["file"])
        period = "2018" if role == "historic" else "2022"
        assert all(m.doc["extras"]["period"] == period for m in (a,b,web))
        original = a.surfaces(source)
        decoded = b.surfaces(source)
        assert original == decoded and sum(r["triangles"] for r in original.values()) == data["triangles"]
        assert web.sha256 == data["sha256"]
        if role=="full":
            assert a.sha256 == manifest["assets"]["raw"]["sha256"]
        textures = web.textures(source)
        assert textures == a.textures(source) == b.textures(source)
        names = {x["file"] for x in textures.values()}
        expected = {"hengchang-terracotta.png"}
        if period == "2022":
            expected.add("grey-running-bond.png")
        assert names == expected
        results[role] = dict(period=period, author_sha256=a.sha256, web_sha256=web.sha256,
                             decoded_sha256=b.sha256, triangles=data["triangles"], material_count=len(original),
                             textured_corners=sum(r.get("textured_corners",0) for r in original.values()),
                             textures=textures, materials=original)
        for m in (a,b,web):
            m.data.close()
    audit = dict(passed=True, id=manifest["id"], manifest_sha256=file_sha(manifest_file),
                 method="Each triangle retains its winding and its float32 vertex positions. Textured corners include the paired UV. Only cyclic rotations and triangle order are normalized. Duplicate triangles are counted. Embedded PNG bytes in the author, web and decoded files match the original image file.",
                 roles=results)
    args.out.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n")


if __name__ == "__main__":
    main()
