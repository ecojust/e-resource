"""Trace photographed points from the published camera through the whole decoded model."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"source"),str(HERE.parents[1]/"xuhui-pathe-records-office/measurements/city-contact")]
from glb_triangles import SerialScene
from garden_quoin_drain import PALE,HIGHLIGHT,GREY,PIPE,HOPPER,RIM,NECK

STONE={PALE,HIGHLIGHT,GREY}
DRAIN={PIPE,HOPPER,RIM,NECK}


def probes(data):
    for c in data["courses"]:
        n=c["course_from_top"]
        uf,vf=c["front_edge_px"]
        for offset,mode in ((-3,"stone"),(3,"outside-stone")):
            yield f"{n:02} front tail {mode}", [uf+offset,vf], mode
        # The return immediately below the soffit is in strong shadow. At the
        # bottom the garden planting hides the returns. Both absences are recorded.
        if 3 <= n <= 26:
            u,v=c["return_edge_px"]
            for offset,mode in ((3,"stone"),(-3,"outside-stone")):
                yield f"{n:02} return tail {mode}",[u+offset,v],mode
    for uv,mode in [
            ((314,105),"neck"),((309,115),"neck"),((304,122),"neck"),((300,128),"neck"),
            ((296,138),"hopper"),((296,144),"hopper"),((293,149),"hopper"),
            ((294.5,173),"pipe"),((294.5,191),"pipe"),((297.5,279),"pipe"),
            ((298.5,371),"pipe"),((299,427),"pipe"),((299,575),"pipe"),
            ((299,614),"pipe"),((299,666),"pipe"),((299,696),"pipe"),
            ((282,185),"outside-drain"),((306,265),"outside-drain"),
            ((285,363),"outside-drain"),((308,500),"outside-drain"),((308,671),"outside-drain")]:
        yield f"observed {mode} at {uv[0]},{uv[1]}",uv,mode


def inspect(path):
    data=json.loads((HERE/"garden-quoin-drain.json").read_text())
    cam=json.loads((HERE/"garden-corner-camera.json").read_text())
    mat=np.asarray(cam["main_corner_projection"])
    eye=np.asarray(cam["camera_position"])
    scene=SerialScene(path)
    hits=[]
    for label,uv,kind in probes(data):
        direction=np.linalg.solve(mat[:,:3],[*uv,1.])
        first=scene.ray(eye,direction,40)
        observed=first["material"] if first else None
        passed={
            "stone":observed in STONE,"outside-stone":observed not in STONE,
            "hopper":observed in {HOPPER,RIM}, "neck":observed in {NECK,RIM},
            "pipe":observed in {PIPE,RIM}, "outside-drain":observed not in DRAIN
        }[kind]
        hits.append({"point":label,"original_px":uv,"class":kind,"first_material":observed,
                     "first_xyz_m":None if first is None else [round(v,4)for v in first["point_enu_m"]],
                     "passed":passed})
    return {**scene.asset,"triangles":len(scene.tri),"rays":len(hits),"camera_xyz_m":eye.tolist(),
            "method":"Unfiltered nearest triangle hit on a ray from the fitted camera through each original photograph pixel.",
            "passed":all(row["passed"]for row in hits),"checks":hits}


if __name__=="__main__":
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("mesh",type=Path)
    arg.add_argument("output",type=Path)
    a=arg.parse_args()
    result=inspect(a.mesh)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+"\n")
    bad=[r for r in result["checks"]if not r["passed"]]
    print(result["rays"]-len(bad),"/",result["rays"],[(r["point"],r["first_material"])for r in bad])
    raise SystemExit(int(not result["passed"]))
