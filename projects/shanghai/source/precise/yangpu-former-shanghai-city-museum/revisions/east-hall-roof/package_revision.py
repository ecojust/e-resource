"""Package a same-ID revision under its own asset subdirectory and manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ID = "yangpu-former-shanghai-city-museum"
SUBDIR = Path("revisions/east-hall-roof")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--lod", required=True, type=Path)
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--gltfpack", required=True, type=Path)
    parser.add_argument("--asset-root", required=True, type=Path)
    args = parser.parse_args()
    original = args.asset_root / "manifest.json"
    inherited = json.loads(original.read_text())
    if inherited["id"] != ID or inherited["assets"]["raw"]["sha256"] != "1f2cd5ba517d0c4b9ec235894a87776af7014eebde1435cc169ced95065f327e":
        raise ValueError("This roof revision requires the frozen west-facade museum model")
    target = args.asset_root / SUBDIR
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        staged = Path(temp)
        subprocess.run([
            sys.executable, str(HERE.parents[1] / "source/package_assets.py"),
            "--raw", str(args.raw), "--lod", str(args.lod), "--native", str(args.native),
            "--gltfpack", str(args.gltfpack), "--out", str(staged),
        ], check=True)
        manifest = json.loads((staged / "manifest.json").read_text())
        for asset in manifest["assets"].values():
            name = asset["file"]
            if digest(staged / name) != asset["sha256"]:
                raise ValueError("Staged asset changed: " + name)
            (staged / name).replace(target / name)
            asset["file"] = (SUBDIR / name).as_posix()
        manifest.update({
            "revision": "east-hall-roof",
            "previous_manifest": "manifest.json",
            "previous_manifest_sha256": digest(original),
            "audit_directory": "data/audit/city-museum-east-hall-roof-v1/",
            "model_scope_zh": "旧市博物馆江湾馆舍的西主立面、两层南北翼、黄瓦重檐门楼与东中厅。东中厅平屋面上见于2019至2026年发布航片的浅矩形分格顶盖已建模，顶盖的高度、板材、用途与建造年代待核。两院内独立体各自保留。",
            "observed_east_hall_roof_cover": json.loads((HERE / "roof-parameters.json").read_text()),
            "rear_hall_rendered_as_simplified_estimated_low_volume": True,
            "rear_hall_scope": "Existing estimated outer walls and flat main roof, with an observed gridded roof cover. North and south elevations remain undocumented.",
        })
        manifest["city_integration"]["source_metadata_scope"] = "Main source 1860 and overlapping west tower 1931. The eastern roof cover lies inside the prior model envelope. Independent courtyard sources 510 and 1262 keep their existing geometry and map registration."
        saved = staged / "manifest-east-hall-roof.json"
        saved.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        saved.replace(args.asset_root / saved.name)


if __name__ == "__main__":
    main()
