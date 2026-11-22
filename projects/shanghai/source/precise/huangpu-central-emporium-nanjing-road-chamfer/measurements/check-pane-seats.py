"""Sample the eight glass rebates from the street and obliquely on both sides."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np


def sample_rebates(source):
    sys.path.insert(0, str(source))
    from photo_plane import position
    from corner_fanlight import read
    samples = []
    for member in read("2022-fanlight-members.json")["members"][1:]:
        points = np.array([position(*p, .088)[[0, 2]] for p in member["centreline"]])
        name = member["member"]
        times = np.linspace(.12, .88, 10) if name == "inner arch" else np.linspace(.16, .90, 8)
        for station, t in enumerate(times):
            i = int(t * (len(points) - 1))
            dx, dz = points[i + 2] - points[i - 2]
            normal = np.array([-dz, dx]) / np.hypot(dx, dz)
            offsets = [-.039, -.026, -.016, -.007, 0., .007, .016, .026, .039]
            if name == "spring rail":
                if normal[1] < 0:
                    normal *= -1
                offsets = [.010, .017, .024, .033, .043]
            for offset in offsets:
                samples.append((name, station, offset, points[i] + offset * normal))
    return samples


def review(project, source, mesh):
    samples = sample_rebates(source)
    from corner_fanlight import GLASS, STEEL
    tools = runpy.run_path(project / "data/audit/postal-office-v1/independent-glb-review-helpers.py")
    triangles, ids, names, identity = tools["load_triangles"](mesh)
    appearance = tools["material_appearance"](mesh)["materials"]
    double = np.array([appearance[m]["doubleSided"] for m in names])[ids]
    normals = np.cross(triangles[:,1] - triangles[:,0], triangles[:,2] - triangles[:,0])
    views = {}
    front_y = .088
    for label, d in [("square", [0.,1.,0.]), ("from left", [.36,1.,.12]), ("from right", [-.36,1.,-.12])]:
        direction = np.asarray(d) / np.linalg.norm(d)
        xy = triangles[:,:,[0,2]] + (front_y - triangles[:,:,1:2]) * (direction[[0,2]]/direction[1])
        lo, hi = xy.min(axis=1)-1e-6, xy.max(axis=1)+1e-6
        front = double | ((normals @ direction) < -1e-12)
        misses, materials = [], {}
        for name, station, offset, (x,z) in samples:
            idx = np.flatnonzero(front & (lo[:,0]<x) & (lo[:,1]<z) & (hi[:,0]>x) & (hi[:,1]>z))
            material, depth = None, None
            if len(idx):
                start = np.array([x,front_y,z]) - direction*2.
                i, distance, loc = tools["first_hit"](triangles[idx], start, direction)
                if np.isfinite(distance):
                    material, depth = names[ids[idx[i]]], loc[1]
            materials[str(material)] = materials.get(str(material),0) + 1
            good = material in {GLASS, STEEL} and depth < front_y+.09
            if name == "spring rail" and material is not None and "limestone" in material.lower():
                good = True
            if not good:
                misses.append(dict(member=name, station=station, offset_m=offset, hit=material, depth_m=depth))
        views[label] = dict(samples=len(samples), passed=len(samples)-len(misses), materials=materials, misses=misses)
    return {"mesh":identity, "views":views}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source","project","mesh","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args = parser.parse_args()
    result = review(args.project,args.source,args.mesh)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print([(k,v["passed"],v["samples"]) for k,v in result["views"].items()])
    if any(v["misses"] for v in result["views"].values()):
        raise SystemExit(1)
