"""Check actual first surfaces in the shutter GLBs, or in a decoded assembled building."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"source"))
sys.path.insert(0,str(HERE.parents[1]/"xuhui-pathe-records-office"/"measurements"/"city-contact"))
from glb_triangles import SerialScene
from west_gable_shutters import side_openings, axes, TIMBER, BACK, BLADES, DARK, GLASS, STONE


def samples():
    for r in side_openings():
        z0,z1=r["bottom"]+.03,r["top"]-.03
        low,high=z0+.065,z0+.701*(z1-z0)
        for inland in (False,True):
            n,d,v=axes(r,inland)
            hinge=np.array([-.023,r["back_y"]-.020 if inland else r["front_y"]+.020,0.])
            width=(r["back_y"]-r["front_y"])/2-.024
            tag=r["key"]+(" inland" if inland else " street")
            clipped=bool(r["inward_leaf_angle_deg"] and inland)
            wood=BACK if clipped else TIMBER; blade=BACK if clipped else BLADES
            for part,a,b,c,mat in [
                ("hinge stile",.017,z0+.39*(z1-z0),-.018,wood),
                ("meeting stile",width-.018,z0+.55*(z1-z0),-.018,wood),
                ("bottom rail",width*.58,z0+.028,-.018,wood),
                ("solid top panel",width*.48,z0+.84*(z1-z0),-.006,wood),
                ("divider",width*.62,high+.019,-.018,wood)]:
                # Test the outward face of the rotated hinge stile. Its reverse faces the
                # wall: at the back window a reversed ray would start inside the plaster.
                ray_dir=n
                if part=="hinge stile" and n[0]<0:
                    c=.017
                    ray_dir=-n
                yield tag+" "+part,hinge+d*a+v*b+n*c,ray_dir,mat,.035
            # The inclined blade face meets the normal ray slightly before its centre.
            for j in range(r["blade_count"]):
                c=hinge+d*(width*.54)+v*(low+(j+.5)*(high-low)/r["blade_count"])
                yield tag+" blade "+str(j+1),c-n*(.004/np.cos(np.deg2rad(32))),n,blade,.025
        for pos in (.16,.52,.86):
            y=r["front_y"]+(r["back_y"]-r["front_y"])*pos
            z=r["bottom"]-.037
            yield r["key"]+" projecting sill",np.array([-r["sill_projection"]+.002,y,z]),np.array([1.,0.,0.]),STONE,.45
        if r["inward_leaf_angle_deg"]:
            a,b=r["front_y"],r["back_y"]
            for v in (.33,.82):
                yield r["key"]+" exposed recessed glass",np.array([.193,a+(b-a)*.72,r["bottom"]+v*(r["top"]-r["bottom"])]),np.array([1.,0.,0.]),GLASS,.7


def verify(model,dest):
    scene=SerialScene(model);rays=[]
    for name,p,d,material,gap in samples():
        o=p-d*gap;hit=scene.ray(o,d,gap+.012)
        delta=None if hit is None else float(np.linalg.norm(np.array(hit["point_enu_m"])-p))
        correct=hit is not None and hit["material"]==material and delta<.007
        rays.append(dict(feature=name,expected_material=material,expected_xyz=p.round(6).tolist(),first_hit=None if hit is None else hit["material"],distance_error_m=delta,passed=correct))
    report={**scene.asset,"triangles":len(scene.tri),"rays":len(rays),"passed":all(r["passed"] for r in rays),"checks":rays}
    dest.write_text(json.dumps(report,indent=2)+"\n")
    print(model.name,len(scene.tri),sum(r["passed"] for r in rays),len(rays))
    return report["passed"]

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("model",type=Path);a.add_argument("report",type=Path)
    q=a.parse_args();raise SystemExit(0 if verify(q.model,q.report) else 1)
