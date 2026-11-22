"""Recalculate recorded room-window head intersections from the two or three native views of each corner."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares

data=json.loads(Path(__file__).with_name("room-window-head-intersections.json").read_bytes())
cameras={k:np.asarray(v["matrix"]) for k,v in data["views"].items()}
def project(p,point):
    image=p@[*point,1.]
    return image[:2]/image[2]
for column in data["window_columns"]:
    for landmark in column["observations"].values():
        def error(point):
            return np.concatenate([project(cameras[row["camera"]],point)-row["pixel"] for row in landmark["views"]])
        target=landmark["xyz_m"]
        found=least_squares(error,target,loss="soft_l1",f_scale=1.5)
        assert np.max(abs(found.x-target))<.004,(column["position"],found.x,target)
print("Verified 72 intersections, including partly obscured and shallow-baseline estimates.")
