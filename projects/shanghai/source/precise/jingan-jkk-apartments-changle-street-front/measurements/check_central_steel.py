"""Test visible glazing, open casements and recessed first surfaces against measured camera rays."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"xuhui-pathe-records-office/measurements/city-contact"))
from glb_triangles import SerialScene


def targets():
    data=json.loads((HERE/"central-steel-source-pixels.json").read_text())["frames"]
    result=[]
    def samples(camera,name,points,expect,tolerance=0):
        for i,uv in enumerate(points,1):
            result.append((camera,name+f" {i}",np.array(uv,dtype=float),expect,tolerance))
    # The dark openings are bounded in the original image by the jamb, open leaf and transom.
    for us in [(268,345),(418,496)]:
        samples("centre-middle-20","closed lower glazing",[(u,v) for u in us for v in [347,429,513,595]],"fixed")
    samples("centre-middle-20","middle east opening",[(u,v)for u in [573,634]for v in [345,427,517,597]],"interior")
    samples("centre-middle-20","closed side toplights",[(u,v)for u in [272,348,562,625]for v in [158,257]],"fixed")
    samples("centre-middle-20","tilting centre toplight",[(412,163),(482,150),(421,218),(487,210)],"fixed")
    samples("centre-lower-20","fixed lower centre",[(u,v)for u in [422,505]for v in [287,380,486,572]],"fixed")
    samples("centre-lower-20","lower open side apertures",[(u,v)for u in [253,325,575,639]for v in [280,376,492,565]],"interior")
    samples("centre-lower-20","lower toplights",[(u,v)for u in [261,336,422,498,567,649]for v in [84,175]],"fixed")
    samples("centre-upper-20","separate upper toplight",[(u,181)for u in [290,359,425,493,553,622]],"fixed",4)
    samples("centre-upper-20","upper fixed centre and east glazing",[(u,v)for u in [437,514,566,642]for v in [390,485,563]],"fixed",4)
    # Interpolate between the observed four corners of each projecting iron-and-glass wing.
    for camera,side in [("w20-mid","right"),("w20-low","right"),("e20-low","left")]:
        mark=data[camera]["marks"][side+"_leaf"]
        ht,hb,ft,fb=[np.array(mark[k],float)for k in ["hinge_top","hinge_bottom","free_top","free_bottom"]]
        pixels=[(1-v)*((1-u)*ht+u*ft)+v*((1-u)*hb+u*fb)
                for u in [.24,.76]for v in [.13,.38,.62,.86]]
        samples(camera,side+" open glass wing",pixels,"open",4)
    return result


def inspect(path):
    scene=SerialScene(path)
    matrices=json.loads((HERE/"jkk-street-camera-fit.json").read_text())["camera_matrices"]
    rows=[]
    for camera,name,uv,expect,tolerance in targets():
        m=np.array(matrices[camera]);eye=-np.linalg.solve(m[:,:3],m[:,3]);inv=np.linalg.inv(m[:,:3])
        offsets=[(0,0)]
        if tolerance:
            offsets += [(tolerance*x,tolerance*y)for x,y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]]
        direct=None;matched=None
        for dx,dy in offsets:
            ray=inv@np.r_[uv+[dx,dy],1.]
            hit=scene.ray(eye,ray,65)
            mat=hit["material"] if hit else None
            if dx==dy==0:direct=mat
            if mat and mat.startswith("JKK central | "):
                kind=("interior" if mat.endswith("inner shadow") else "open" if mat.endswith("glass in projecting leaf")
                      else "fixed" if "glass" in mat or "reflection" in mat else "frame")
                if kind==expect:
                    matched=[dx,dy];break
        rows.append({"camera":camera,"feature":name,"source_native_px":uv.round(2).tolist(),
                     "expected":expect,"first_material":direct,"matching_pixel_offset":matched})
    return {"asset":scene.asset,"total":len(rows),"direct":sum(r["matching_pixel_offset"]==[0,0] for r in rows),
            "passed":sum(r["matching_pixel_offset"] is not None for r in rows),"samples":rows}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model",type=Path);parser.add_argument("output",type=Path);args=parser.parse_args()
    r=inspect(args.model);args.output.write_text(json.dumps(r,indent=1,ensure_ascii=False)+"\n")
    print(r["direct"],r["passed"],r["total"])
    for s in r["samples"]:
        if s["matching_pixel_offset"] is None:print(s["camera"],s["feature"],s["source_native_px"],s["expected"],s["first_material"])
    sys.exit(int(r["passed"]!=r["total"]))
