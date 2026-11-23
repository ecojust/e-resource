"""Recast three registered photograph sets against the complete GLB, without filtering geometry."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

directory = Path(__file__).resolve().parent
project = directory.parents[3]
sys.path.insert(0,str(project / "source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact"))
from glb_triangles import SerialScene

parser=argparse.ArgumentParser()
parser.add_argument("glb",type=Path)
parser.add_argument("report",type=Path)
parser.add_argument("--transform",type=Path,help="4x4 No. 9 local-to-scene matrix as a JSON array")
args=parser.parse_args()
M=np.array(json.loads(args.transform.read_bytes()) if args.transform else np.eye(4))
survey=json.loads((directory / "nine-gable-window-survey.json").read_bytes())
scene=SerialScene(args.glb)
out=[]
for view,photo in survey["images"].items():
    P=np.array(photo["P"]) @ np.linalg.inv(M)
    inverse=np.linalg.inv(P[:,:3])
    eye=-inverse@P[:,3]
    scale=photo["camera_pixel_per_native_pixel"]
    def test(label,uv,expected,point_type):
        direction=inverse@np.r_[np.array(uv)*scale,1.]
        hit=scene.ray(eye,direction,120)
        out.append({"station":view,"label":label,"type":point_type,"upright_native_pixel":list(uv),
                    "expected_material_prefix":expected,"first_hit":hit,
                    "matched":bool(hit and any(hit["material"].startswith(k)for k in expected))})
    for row in photo["windows"]:
        q=np.array(row["frame_outline_or_visible_extent"])
        for name,(tx,ty) in {"left glass":(.24,.22),"right glass":(.76,.22)}.items():
            uv=(1-ty)*((1-tx)*q[0]+tx*q[1])+ty*((1-tx)*q[3]+tx*q[2])
            test(row["id"]+" "+name,uv,["9 glass"],"glass inside photographed jambs")
        for line in row.get("mouldings_and_crossrail",[]):
            index=line["id"]
            if index not in ["outer_white_cap_top","sill_top","heavy_transom"]:
                continue
            # Record original edge pixels unchanged. Their width is 1–3 pixels in 2023;
            # a first hit above/below a lip is retained with that original edge observation.
            uv=np.mean(line["ends"],axis=0)
            exp=["9 sash"] if index=="heavy_transom" else ["9 surround"]
            test(row["id"]+" "+index,uv,exp,"photographed edge, may hit adjoining surface")
    if view in ['winter2023-14','winter2023-18']:
        px=[456,426] if view=='winter2023-14' else [395,377]
        test("lower breast front",px,["Hongji 9 | pebbled stack"],"front face")
report={"glb_sha256":sha256(args.glb.read_bytes()).hexdigest(),"rays":len(out),
        "matches":sum(row["matched"] for row in out),"transform":M.tolist(),"first_hits":out}
args.report.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
print(report["matches"],report["rays"])
for row in out:
    if not row["matched"]:
        print(row["station"],row["label"],row["first_hit"]["material"] if row["first_hit"] else "clear")
