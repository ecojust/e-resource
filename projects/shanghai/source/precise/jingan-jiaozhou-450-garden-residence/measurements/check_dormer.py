"""First intersections on the garden-facing shed dormer, in the complete decoded GLB."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/"source"), str(HERE.parents[1]/"xuhui-pathe-records-office/measurements/city-contact")]
from dormer import EDGE, LOUVRE, PLASTER, RIM, SHADOW, TIMBER, TRIM
from glb_triangles import SerialScene


def check(mesh):
    scene = SerialScene(mesh)
    d = json.loads((HERE/"dormer-registration.json").read_text())
    hits = []

    def observe(label, origin, direction, distance, expected, **details):
        result = scene.ray(origin, direction, distance)
        material = result["material"] if result else None
        hits.append(dict(label=label, expected=sorted(expected), first_material=material,
                         passed=material in expected, **details))

    # The horizontal rays test a material and the dark interval above every
    # individual slat. The ray remains unfiltered through the complete scene.
    for sh in d["shutters"]:
        x = sum(sh["blade_span_x_m"])/2
        levels = d["blade_rows"][(sh["id"]-1)//3]["leading_edge_z_m"]
        for n, z in enumerate(levels, 1):
            for dz, kind, expected in [(.010, "blade", {LOUVRE}),(.054, "space", {SHADOW})]:
                origin = [x,d["front_shutter_plane_y_m"]-.34,z+dz]
                observe(f"leaf {sh['id']} / blade {n:02} / {kind}", origin, [0,1,0], .7,
                        expected, origin_xyz_m=[round(v,4) for v in origin])

    # Panel and stile locations were read in the rectified front photographs.
    # Reproject a centre for each onto each original source and send the ray
    # from the camera, including the photographed gaps between the paired sets.
    bands = [((46,121), {LOUVRE,SHADOW}),((89,132),{LOUVRE,SHADOW}),((126,128),{LOUVRE,SHADOW}),
             ((276,133),{LOUVRE,SHADOW}),((313,115),{LOUVRE,SHADOW}),((350,130),{LOUVRE,SHADOW}),
             ((178,101),{PLASTER}),((183,149),{PLASTER}),((220,104),{PLASTER}),((223,151),{PLASTER}),
             ((201,117),{TIMBER}),((152,119),{TIMBER}),((247,137),{TIMBER})]
    for image in ("13","8"):
        P = np.array(d["camera_models"][image])
        cam = -np.linalg.solve(P[:,:3],P[:,3])
        H = np.array(d["normalized_to_original"][image])
        for i,(xy,expected) in enumerate(bands):
            q = H@[*xy,1]
            uv = q[:2]/q[2]
            observe(f"source {image} / front control {i+1}",cam,np.linalg.solve(P[:,:3],[*uv,1]),
                    50,expected,original_px=uv.round(3).tolist())
    # Independent manually read original pixels on the dark external fittings
    # and cheek supplement the two source transformations above.
    cases = {
        "13":[((539,314),{RIM}),((533,416),{RIM}),((891,503),{RIM}),((496,391),{PLASTER}),
              ((695,360),{TIMBER,TRIM}),((602,322),{RIM,TIMBER}),((810,384),{TIMBER,TRIM})],
        "8":[((336,174),{RIM}),((334,234),{RIM}),((314,224),{PLASTER}),
             ((418,187),{TIMBER,TRIM}),((498,190),{RIM,TIMBER})]
    }
    for image,controls in cases.items():
        P = np.array(d["camera_models"][image])
        cam = -np.linalg.solve(P[:,:3],P[:,3])
        for uv,expected in controls:
            observe(f"source {image} / detail {uv[0]},{uv[1]}",cam,
                    np.linalg.solve(P[:,:3],[*uv,1]),50,expected,original_px=list(uv))
    return {**scene.asset,"method":"Nearest physical triangle, without material or node filtering.",
            "count":len(hits),"passed":all(v["passed"] for v in hits),"checks":hits}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh",type=Path)
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    result = check(args.mesh)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+"\n")
    bad = [v for v in result["checks"] if not v["passed"]]
    print(result["count"]-len(bad),"/",result["count"],[(v["label"],v["first_material"]) for v in bad][:30])
    raise SystemExit(int(bool(bad)))
