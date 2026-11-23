"""Package the two levels of detail and compare decoded faces, corner UVs and image bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[1] / "source"
sys.path.insert(0, str(SOURCE))
from build_model import ID, META, PROJECT, retain_metadata
from package_architectural_model import check_pair, glb_stats

native_source = runpy.run_path(str(SOURCE / "build_blender_source.py"))
TEXTURES = native_source["TEXTURES"]
rights = native_source["rights"]
texture_extension = native_source["texture_extension"]
UV_READER = PROJECT / "source/precise/changning-hengchang-li-yuyuan-road-gatehouse/measurements/check_render_uv.py"
Model = runpy.run_path(str(UV_READER))["Model"]


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".writing")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def asset(path):
    with path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    return dict(file=path.name, bytes=path.stat().st_size, sha256=digest, **glb_stats(path))


def package(exports, out, audit, gltfpack):
    out.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)
    assets, closure, texture_reports, surfaces = {}, {}, {}, {}
    for role, suffix in (("full", "web"), ("lod", "lod")):
        src = exports / (role + "-source.glb")
        packed = out / (ID + "-" + suffix + ".glb")
        decoded = out / ("decoded-" + role + ".glb")
        close = json.loads((exports / (role + "-closure.json")).read_bytes())
        geometry = json.loads(src.with_suffix(".geometry.json").read_bytes())
        source_asset = asset(src)
        assert not close["failures"] and source_asset["sha256"] == geometry["sha256"]
        assert close["triangles"] == source_asset["triangles"] and close["parts"] == geometry["parts"]
        closure[role] = dict(source_sha256=source_asset["sha256"], **close)
        if role == "full":
            raw = out / (ID + "-raw.glb")
            shutil.copyfile(src, raw)
            assets["raw"] = asset(raw)
        subprocess.run([gltfpack, "-i", src, "-o", packed, "-cc", "-noq", "-vnf",
                        "-km", "-kn", "-ke"], check=True)
        retain_metadata(packed, src)
        surfaces[role] = check_pair(src, packed, decoded)
        assets[role] = asset(packed)
        assert source_asset["triangles"] == assets[role]["triangles"]
        assert rights(src) == rights(packed) == rights(decoded)
        author, web, result = (Model(p) for p in (src, packed, decoded))
        try:
            assert author.doc["extras"] == web.doc["extras"] == result.doc["extras"]
            assert author.doc["asset"]["copyright"] == web.doc["asset"]["copyright"]
            images = author.textures(SOURCE)
            assert set(images) == set(TEXTURES) and images == web.textures(SOURCE) == result.textures(SOURCE)
            for name in TEXTURES:
                assert all(texture_extension(m.doc, name) == "REPEAT" for m in (author, web, result))
            corners = author.surfaces(SOURCE)
            assert corners == result.surfaces(SOURCE), "Decoded position, material or UV differs"
            assert all(corners[name]["nondegenerate_texture_triangles"] > 0 for name in TEXTURES)
            texture_reports[role] = dict(
                triangles=source_asset["triangles"], author_sha256=source_asset["sha256"],
                web_sha256=web.sha256, decoded_sha256=result.sha256, textures=images,
                textured_corners=sum(row.get("textured_corners", 0) for row in corners.values()),
                materials=corners)
        finally:
            for model in (author, web, result):
                model.data.close()
        print(role, assets[role]["triangles"], assets[role]["bytes"], assets[role]["sha256"], flush=True)
    assert assets["raw"]["triangles"] == assets["full"]["triangles"] > assets["lod"]["triangles"]
    manifest = dict(**META, model_id=ID, assets=assets, all_dimensions_estimated=True,
                    third_party_models_embedded=False)
    write(audit / "editable-parts-closure.json", closure)
    write(audit / "oriented-surfaces.json", surfaces)
    write(audit / "render-uv.json", dict(passed=True, id=ID, roles=texture_reports))
    write(out / "manifest.json", manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exports", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("audit", type=Path)
    parser.add_argument("--gltfpack", default="gltfpack")
    args = parser.parse_args()
    package(args.exports, args.out, args.audit, args.gltfpack)
