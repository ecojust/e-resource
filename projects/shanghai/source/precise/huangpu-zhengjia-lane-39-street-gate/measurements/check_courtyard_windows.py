"""Intersect decoded GLB triangles at the eight measured end-house window openings."""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"source"),str(HERE.parents[1]/"xuhui-pathe-records-office/measurements/city-contact")]
from glb_triangles import SerialScene
from courtyard_photo_plane import EYE,on_end
from courtyard_windows import openings,leaf_placement,PICKS,WOOD,SLAT,GLASS,FRAME,GRILLE,BLIND,STONE,EDGE,BOARD

UP=np.array([0.,0.,1.])
FRONT=np.array([0.,1.,0.])


def contacts(low):
    def front(tag,x,y,z,material,gap=.020,tol=.002):
        return tag,np.array([x,y,z]),FRONT,material,gap,tol
    for row in openings():
        k=row["key"]
        l,r,bot,top=[row[n] for n in ("left","right","bottom","top")]
        for f in (.12,.51,.9):
            yield front(k+" sill",l+f*(r-l),-.096,bot-.025,STONE,.2)
        if row["observed"][0]=="grille":
            for uv in PICKS["ground_grille_x"]:
                x=on_end(*uv,.025)[0]
                yield front(k+" grille upright",x,.025,bot+(top-bot)*.42,GRILLE)
            for uv in PICKS["ground_grille_rails"]:
                z=on_end(*uv,.018)[2]
                yield front(k+" horizontal tie",(l+r)*.5,.014,z,GRILLE)
            for blade in range(row["slat_count"]):
                pitch=(top-bot-.05)/row["slat_count"]
                z=bot+.025+(blade+.5)*pitch
                yield front(k+" blind "+str(blade+1),l+(r-l)*.61,.099-.0025/math.cos(math.radians(23)),z,BLIND,.012)
        elif row["observed"][0]=="board":
            for j in range(8):
                x=l+.016+(j+.5)*(r-l-.032)/8
                yield front(k+" board "+str(j+1),x,.050,(bot+top)*.5,BOARD,.16)
        else:
            for i,condition in enumerate(row["observed"]):
                h,d,n,width,angle=leaf_placement(row,i)
                h=h.copy();h[2]=0
                z0,z1=bot+.029,top-.029
                first,last=z0+.072,z1-.054
                pitch=(last-first)/row["slat_count"]
                tag=f"{k} leaf {i+1} "
                for s in (.018,width-.018):
                    yield tag+"stile",h+d*s+UP*(z0+.38*(z1-z0))-n*.015,n,WOOD,.010,.0015
                for s in (.030,width-.030):
                    y=-.015 if low else -.018
                    yield tag+"stile moulding",h+d*s+UP*(z0+.57*(z1-z0))+n*y,n,WOOD,.008,.0015
                for j in range(row["slat_count"]):
                    broken=k=="upper-right" and i==1 and j==7
                    z=first+(j+.5)*pitch+(pitch*.22 if broken else 0.)
                    tilt=math.radians(6 if broken else 34)
                    p=h+d*(.56*width)+UP*z-n*(.004/math.cos(tilt))
                    yield tag+"blade "+str(j+1),p,n,SLAT,.012,.0018
                if condition=="open":
                    x=l+(i+.5)*(r-l)/2
                    for f in (.2,.5,.83):
                        p=np.array([x,.127,bot+f*(top-bot)])
                        direction=p-EYE;direction/=np.linalg.norm(direction)
                        yield tag+"street view glass",p,direction,GLASS,float(np.linalg.norm(p-EYE)),.004
                    for f in (1/3,2/3):
                        yield front(tag+"crossbar",x,.108,bot+f*(top-bot),FRAME,.25)
        if k in PICKS["rooflet_corners"]:
            e=PICKS["rooflet_corners"][k]
            l,r=(on_end(*e[a])[0] for a in ("back_left","back_right"))
            back=sum(on_end(*e[a])[2] for a in ("back_left","back_right"))/2
            proj=.36 if k.startswith("middle") else .405
            front_z=sum(on_end(*e[a],-proj)[2] for a in ("lip_left","lip_right"))/2
            z=min(back-.035,max(back-.125,front_z))-.014
            for f in (.04,.55,.96):
                yield front(k+" canopy lip",l+f*(r-l),-proj-.013,z,EDGE,.05)


def examine(model,level,dest,transform=None):
    scene=SerialScene(model)
    affine=np.eye(4) if transform is None else np.array(json.loads(transform.read_text()),dtype=float)
    if affine.shape!=(4,4):
        raise ValueError("Expected a 4 by 4 local-to-building matrix")
    checks=[]
    for tag,pt,direction,material,gap,tol in contacts(level=="lod"):
        p=(affine@np.r_[pt,1.])[:3]
        d=affine[:3,:3]@direction
        scale=np.linalg.norm(d);d/=scale
        hit=scene.ray(p-d*gap*scale,d,(gap+.025)*scale)
        err=None if hit is None else float(np.linalg.norm(np.asarray(hit["point_enu_m"])-p))
        checks.append({"feature":tag,"expected_xyz_m":p.round(6).tolist(),"expected_material":material,
                       "actual_material":None if hit is None else hit["material"],"error_m":err,
                       "passed":bool(hit is not None and hit["material"]==material and err<tol*scale)})
    report={**scene.asset,"triangles":len(scene.tri),"level":level,"local_to_building":affine.tolist(),
            "rays":len(checks),"passed":all(c["passed"] for c in checks),"checks":checks}
    dest.write_text(json.dumps(report,indent=2)+"\n")
    print(model.name,sum(c["passed"] for c in checks),"/",len(checks),len(scene.tri))
    return report["passed"]


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("model",type=Path)
    a.add_argument("level",choices=("full","lod"))
    a.add_argument("report",type=Path)
    a.add_argument("--transform",type=Path)
    args=a.parse_args()
    raise SystemExit(0 if examine(args.model,args.level,args.report,args.transform) else 1)
