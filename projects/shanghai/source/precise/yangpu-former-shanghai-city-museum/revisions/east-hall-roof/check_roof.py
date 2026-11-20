"""Ray-test gridded roof heights, surrounding flat roof and the two unfilled courts."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "source"))
from verify_serialized import load

parser = argparse.ArgumentParser()
parser.add_argument("--decoded", type=Path, required=True)
parser.add_argument("--source", type=Path)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
triangles, materials, digests = load(args.decoded, args.source)
# The central rectangle, eastern wing, and two courts all fall in this range.
triangles = np.asarray(triangles, dtype=float)
a = triangles[:, 0]
edge1 = triangles[:, 1] - a
edge2 = triangles[:, 2] - a

def hit_from_above(x, y):
    direction = np.array([0., 0., -1.])
    h = np.cross(direction, edge2)
    det = np.einsum("ij,ij->i", edge1, h)
    valid = abs(det) > 1e-10
    scale = np.zeros(len(det))
    scale[valid] = 1 / det[valid]
    offset = np.array([x, y, 30.]) - a
    u = np.einsum("ij,ij->i", offset, h) * scale
    q = np.cross(offset, edge1)
    v = np.einsum("j,ij->i", direction, q) * scale
    t = np.einsum("ij,ij->i", edge2, q) * scale
    indices = np.flatnonzero(valid & (u >= -1e-8) & (v >= -1e-8) & (u+v <= 1+1e-8) & (t > 1e-6))
    if not len(indices):
        return None
    nearest = indices[t[indices].argmin()]
    return {"surface": str(materials[nearest]), "height_m": float(30-t[nearest])}

probes = []
def probe(label, x, y, surface=None, height=0.):
    hit = hit_from_above(x, y)
    passed = hit is None if surface is None else hit is not None and hit["surface"] == surface and abs(hit["height_m"]-height) < .0001
    probes.append({"name":label, "xy_enu_m":[x,y], "expected":surface, "expected_height_m":height if surface else None, "hit":hit, "passed":passed})

for col,x in enumerate([-.5, 3., 6.5], 1):
    for row,y in enumerate([-2.45, .2], 1):
        probe(f"panel {col}/{row}", x, y, "cover panel", 10.36)
for label,x,y in [("west edge",-2.3,-1.8),("east edge",8.3,-.3),("south edge",4.,-3.65),("north edge",3.,1.45),("first transverse divider",1.27,-2.),("second transverse divider",4.73,.15),("central longitudinal divider",3.,-1.1)]:
    probe(label,x,y,"cover frame",10.42)
for x,y in [(-3.,-1.1),(9.,-1.1),(3.,-4.5),(3.,2.2),(20.,-4.),(18.,5.)]:
    probe("existing main eastern roof",x,y,"roof concrete",10.12)
for x,y in [(18.,16.),(12.,12.),(18.,-15.),(12.,-19.)]:
    probe("open court",x,y)
assert len(probes)==23 and all(row['passed'] for row in probes), [r for r in probes if not r["passed"]]
source=args.source or args.decoded
report={"asset":source.name,"asset_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"triangles":len(triangles),"tests":probes,"completed":True}
args.out.write_text(json.dumps(report,indent=2)+"\n")
print(args.out, len(probes))
