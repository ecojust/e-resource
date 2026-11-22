"""Check front/return surfaces and clear gaps on the actual exported balcony mesh."""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "source"), str(HERE.parents[1] / "xuhui-pathe-records-office/measurements/city-contact")]
from glb_triangles import SerialScene
from jkk_balconies import DATA, BAND, SOFFIT, UPRIGHT, RAIL, FLAG, SHOE

FRONT = np.array([0.,1.,0.])
UP = np.array([0.,0.,1.])


def sample_lines(low):
    data = json.loads(DATA.read_text())
    for row in data["stack_geometry"]:
        left, right = row["x_west_east_m"]
        west, east = row["front_radius_west_east_m"]
        front = row["street_edge_y_m"]
        span = right - left
        for tier, base in enumerate(row["storey_slab_soffits_z_m"], 1):
            key = row["column"] + str(tier)
            for dz in (.06,.240,.412,.593,.772):
                for frac in (.20,.38,.61,.83):
                    yield key, "street band", [left+span*frac,front,base+dz], FRONT, BAND,.018
                for end, radius, center, angles in [("west",west,left+west,(200,224,251)),
                                                    ("east",east,right-east,(285,313,344))]:
                    for angle in angles if radius > 0 else ():
                        a = math.radians(angle)
                        radial = np.array([math.cos(a),math.sin(a),0.])
                        target = np.array([center,front+radius,base+dz]) + radius*radial
                        yield key, end+" curved return", target, -radial, BAND,.025
            for dz in (.157,.328,.50,.678):
                for frac in (.22,.36,.64,.81):
                    yield key, "clear horizontal opening", [left+span*frac,front+.18,base+dz], FRONT,None,.28
            xpost = row["front_upright_x_m"]
            yield key,"plaster upright", [xpost,front-.0015,base+.47],FRONT,UPRIGHT,.02
            for frac in (.19,.42,.78):
                x = left+span*frac
                yield key,"slab soffit", [x,front+.32,base], UP,SOFFIT,.05
                yield key,"upper deck", [x,front+.32,base+(.125 if low else .134)], -UP,SOFFIT if low else FLAG,.04
                yield key,"upper metal cap", [x,front+.04,base+.974],UP,RAIL,.048
            x = left + span*.30
            if not low:
                yield key,"individual steel socket", [x,front+.040-.0255,base+.839], FRONT,SHOE,.035


def inspect(mesh, low):
    scene = SerialScene(mesh)
    records = []
    for key, name, target, direction, expected, approach in sample_lines(low):
        p = np.asarray(target)
        d = np.asarray(direction)
        hit = scene.ray(p - d*approach, d, approach+.005)
        actual = hit["material"] if hit else None
        error = float(np.linalg.norm(np.asarray(hit["point_enu_m"])-p)) if hit else None
        # The top metal cap is round; a ray from below reaches its lower surface.
        tolerance = .025 if name == "upper metal cap" else .008
        ok = actual == expected and (error is None or error <= tolerance)
        records.append([key,name,np.round(p,4).tolist(),expected,actual,round(error,5) if error is not None else None,ok])
    return {**scene.asset,"mesh_level":"lod" if low else "full","triangles":len(scene.tri),
            "sample_columns":["balcony","feature","target_xyz_m","expected_material","first_hit_material","error_m","passed"],
            "samples":records,"traces":len(records),"by_feature":dict(Counter(r[1] for r in records)),
            "passed":all(row[-1] for row in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh",type=Path)
    parser.add_argument("level",choices=["full","lod"])
    parser.add_argument("output",type=Path)
    args = parser.parse_args()
    output = inspect(args.mesh, args.level == "lod")
    args.output.write_text(json.dumps(output,ensure_ascii=False,separators=(",",":"))+"\n")
    failed = [row[:2]+row[3:6] for row in output["samples"] if not row[-1]]
    print(output["traces"],"traces;",len(failed),"failed", failed[:6])
    raise SystemExit(int(not output["passed"]))
