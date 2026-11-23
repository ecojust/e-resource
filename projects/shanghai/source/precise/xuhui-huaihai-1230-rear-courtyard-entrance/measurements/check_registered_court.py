"""Probe frozen photographic pixels against actual raw or independently decoded GLB triangles."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from register_court import Camera

HERE=Path(__file__).absolute().parent
HELPER=HERE.parents[1]/"xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py"
SerialScene=runpy.run_path(str(HELPER))["SerialScene"]
POINTS=HERE/"independent-court-pixels.json"


def matches(hit, role):
    if hit is None:
        return False
    material=hit["material"].lower()
    depth=hit["point_enu_m"][1]
    if role in ("gap","recess"):
        return depth>.12
    if role=="recessed-glass":
        return depth>.40 and "glass" in material
    if role=="balcony-glass":
        return "glass" in material and "balcony" in material
    if role=="plaque":
        return "street-number enamel" in material or ("green" in material and any(s in material for s in ("plaque","address","plate")))
    if role=="band":
        return "base and bands" in material
    if role=="cast":
        return "precast balcony" in material
    if role=="door":
        return depth>.5 and any(s in material for s in ("door","recess","dark entrance","dark-painted","umber","reveal","vestibule"))
    if role=="step":
        x,y,z=hit["point_enu_m"]
        return ("step" in material or "granite" in material or "precast balcony" in material) and abs(x)<1.5 and y<.25 and z<1.05
    tokens={"sash":("sash","frame","steel joinery"),"drip":("green painted balcony drip",),
            "brick":("brick","soldier"),"glass":("glass",)}
    return any(s in material for s in tokens[role])


def near_offsets(radius):
    points=[(x,y) for x in range(-radius,radius+1) for y in range(-radius,radius+1)
            if 0<x*x+y*y<=radius*radius]
    return sorted(points,key=lambda p:(p[0]*p[0]+p[1]*p[1],p))


def check(mesh):
    scene=SerialScene(mesh)
    records=[]
    for group in json.loads(POINTS.read_text())["views"]:
        camera=Camera(group["camera"])
        for row in group["controls"]:
            x,y=row["xy"]
            exact=scene.ray(camera.c,camera.ray((x,y)),90)
            good=matches(exact,row["role"])
            near=(0,0) if good else None
            if not good:
                for dx,dy in near_offsets(row["tol_native_px"]):
                    if matches(scene.ray(camera.c,camera.ray((x+dx,y+dy)),90),row["role"]):
                        near=(dx,dy)
                        break
            records.append({**row,"station":group["camera"],"exact_hit":exact,"matched_exactly":good,
                            "nearest_matching_offset_native_px":near})
    return {"asset":scene.asset,"controls_sha256":hashlib.sha256(POINTS.read_bytes()).hexdigest(),
            "camera_sha256":hashlib.sha256((HERE/"registered-rear.json").read_bytes()).hexdigest(),
            "count":len(records),"exact":sum(r["matched_exactly"] for r in records),
            "within_predeclared_tolerance":sum(r["nearest_matching_offset_native_px"] is not None for r in records),
            "rows":records}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("glb",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    report=check(a.glb)
    a.output.parent.mkdir(exist_ok=True,parents=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(f'{report["exact"]} exact, {report["within_predeclared_tolerance"]}/{report["count"]} within stated tolerances')
