"""Check first visible triangles and empty openings in the courtyard of an exported residence GLB."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "xuhui-pathe-records-office/measurements/city-contact"))
from glb_triangles import SerialScene


def inspect(path):
    mesh = SerialScene(path)
    placement = json.loads((HERE/"courtyard-boundary-placement.json").read_text())
    surveyed = json.loads((HERE/"courtyard-pier-and-ironwork.json").read_text())
    origin = np.array(placement["origin_in_building_xyz_m"])
    unit = np.r_[placement["unit_x_in_building_xy"], 0.]
    inward = np.array([-unit[1], unit[0], 0.])
    up = np.array([0., 0., 1.])
    sx, sz = placement["horizontal_section_scale"], placement["vertical_section_scale"]
    piers = placement["local_pier_centres_m"]
    iron = "black painted iron"
    casting = "weathered foliate casting"
    rubbed = "rubbed casting edges"
    checked = []
    def sample(label, x, y, z, direction, length, expect, max_y=None):
        point = origin + x*unit + y*sx*inward + z*sz*up
        hit = mesh.ray(point, direction, length)
        material = hit["material"].removeprefix("9 courtyard | ") if hit else None
        depth = np.dot(np.array(hit["point_enu_m"])-origin, inward)/sx if hit else None
        passed = material in expect and (max_y is None or depth is not None and depth < max_y)
        checked.append({"sample": label, "material": material, "expected": expect,
                        "street_normal_depth_m": None if depth is None else round(float(depth*sx), 5),
                        "passed": bool(passed)})
        return depth
    def front(label, x, z, expect, max_y=None):
        return sample(label, x, -.65, z, inward, .85*sx, expect, max_y)
    for i, center in enumerate(piers, 1):
        prefix = f"pier {i} "
        for label, z in [("long panel", 1.5), ("upper panel", 2.59)]:
            face = front(prefix+label+" plaster face", center+.272*sx, z, ["cream plaster"])
            cavity = front(prefix+label+" inset", center, z, ["recessed plaster"])
            passed = face is not None and cavity is not None and .022 < (cavity-face)*sx < .052
            checked.append({"sample": prefix+label+" recess depth", "passed": bool(passed),
                            "measured_m": None if cavity is None or face is None else round(float((cavity-face)*sx), 5)})
        front(prefix+"base", center, .3, ["grey rendered plinth"])
        sample(prefix+"top of head block", center, 0., 3.55, -up, .5*sz, ["grey coping"])
        front(prefix+"cap edge", center, 3.070, ["coping edge"])
    for i, (left, right) in enumerate(zip(piers, piers[1:]), 1):
        xs = left + (right-left)*np.array(surveyed["iron"]["measured_abscissae_m_on_winter_plane"])/4.83744
        assert len(xs) == surveyed["iron"]["observed_uprights_one_bay"] == 24
        bay = f"bay {i} "
        for n, x in enumerate(xs, 1):
            upright = bay+f"upright {n} "
            for z in (1.19, 2.13):
                front(upright+f"shaft {z}", x, z, [iron])
            front(upright+"blade ridge", x, 2.646, [rubbed])
            front(upright+"scroll lobe", x-.028*sx, 2.548, [casting, rubbed])
        for n, (a, b) in enumerate(zip(xs, xs[1:])):
            mid = (a+b)/2
            front(bay+f"air gap {n+1}", mid, 1.83, [None])
            front(bay+f"continuous upper rail {n+1}", mid, 2.394, [iron])
            if n % 2:
                continue
            radius = min(.071, (b-a)/sx*.44)
            z = 2.382-.016-radius
            flower = bay+f"roundel {n//2+1} "
            front(flower+"domed centre", mid, z, [rubbed], -.018)
            for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                front(flower+f"embossed petal {dx}/{dz}", mid+dx*.56*radius*sx,
                      z+dz*.56*radius, [rubbed], -.017)
            front(flower+"rim", mid+.84*radius*sx, z-.46*radius, [iron])
            for dx, dz in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                front(flower+f"open quadrant {dx}/{dz}", mid+dx*.48*radius*sx, z+dz*.48*radius, [None])
    return {"asset": mesh.asset, "total": len(checked), "passed": sum(c["passed"] for c in checked),
            "samples": checked}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inspect(args.model)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1)+"\n")
    print(result["passed"], "/", result["total"])
    for row in [r for r in result["samples"] if not r["passed"]][:6]:
        print(row)
    sys.exit(int(result["passed"] != result["total"]))
