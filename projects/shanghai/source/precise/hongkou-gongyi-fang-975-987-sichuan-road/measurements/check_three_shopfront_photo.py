"""Cast rays through independently registered pixels of the repaired street facade."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "xuhui-pathe-records-office/measurements/city-contact"))
from glb_triangles import load_triangles


def sample_points():
    data = json.loads((HERE/"three-building-front-shop-and-door-dimensions.json").read_bytes())
    rows = []
    def add(component, pixel, feature, acceptable):
        rows.append((component,pixel,feature,acceptable))
    for i, shop in enumerate(data["shop_glazing"], 1):
        l,r,head,foot=shop["uv_head_foot_left_right"]
        bar=shop["transom_bar_center_v"]
        join=shop["fixed_to_door_mullion_u"]
        meeting=shop["leaf_meeting_u"]
        sign=1 if shop["door_side"]=="右" else -1
        label=f"shop {i}"
        add(label,[(join+(l if sign==1 else r))/2,468],"fixed glass",["shop glazing"])
        add(label,[(join+meeting)/2,468],"door glass",["shop glazing"])
        add(label,[join,470],"full height mullion",["slender shopfront metal"])
        add(label,[meeting,470],"door meeting",["slender shopfront metal"])
        add(label,[meeting,(bar+head)/2],"clear fanlight over door meeting",["shop glazing"])
        add(label,[(join+meeting)/2,bar],"fanlight bar",["slender shopfront metal"])
        add(label,[l+17,head-11],"fascia",["grey shop fascia"])
    for floor, subjects in data["balcony_doors"].items():
        for i,door in enumerate(subjects):
            l,r,head,foot=door["uv_head_foot_left_right"]
            center=(l+r)/2
            bar=door["transom_bar_center_v"]
            label=f"{floor} bay {door['complete_bay_from_left']} door {door['door_within_bay']}"
            # Read the closed right-hand leaf for every door. On the lower storey the
            # left leaf of the second complete bay's right-hand door stands open.
            add(label,[l+(r-l)*.65,bar+10],"right leaf glass",["reflected balcony glass"])
            add(label,[center,bar+10],"meeting stile",["red brown timber"])
            add(label,[l+(r-l)*.65,head+5],"overlight glass",["reflected balcony glass"])
            add(label,[l+(r-l)*.75,head+5],"overlight narrow bar",["red brown timber"])
            add(label,[r+3,bar+7],"pale stone jamb",["pale stone dressings","grey-beige washed aggregate"])
            if i%2==0:
                add(label,[r+19,bar+7],"brick between two doors",["cleaned running-bond brick"])
    return rows


def check(path):
    tri,groups,mats,meta=load_triangles(path)
    matrix=json.loads((HERE/"repaired-front-pixel-camera.json").read_bytes())
    P=np.array(matrix["P"]);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
    raw=tri.reshape(-1,3)@P[:,:3].T+P[:,3]
    assert raw[:,2].min()>0
    xy=(raw[:,:2]/raw[:,2:3]).reshape(-1,3,2)
    lo=xy.min(axis=1); hi=xy.max(axis=1)
    a=tri[:,0]; ab=tri[:,1]-a; ac=tri[:,2]-a
    def first(uv):
        ix=np.flatnonzero(np.all(lo<=uv,axis=1)&np.all(hi>=uv,axis=1))
        if not len(ix):return None
        d=inv@[*uv,1];d/=np.linalg.norm(d)
        h=np.cross(d,ac[ix]);det=np.einsum("ij,ij->i",ab[ix],h);live=abs(det)>1e-10
        denom=np.where(live,det,1);diff=eye-a[ix];q=np.cross(diff,ab[ix])
        u=np.einsum("ij,ij->i",diff,h)/denom;v=(q@d)/denom
        t=np.einsum("ij,ij->i",ac[ix],q)/denom
        ok=np.flatnonzero(live&(t>0)&(u>=0)&(v>=0)&(u+v<=1))
        return mats[groups[ix[ok[np.argmin(t[ok])]]]] if len(ok) else None
    evidence=[]
    for label,p,feature,surfaces in sample_points():
        uv=np.array(p);direct=first(uv);radius=None
        def matches(material):return material is not None and any(material.endswith("| "+s) for s in surfaces)
        if matches(direct):radius=0
        else:
            for r in (1,2,3):
                if any(matches(first(uv+r*np.array([np.cos(t),np.sin(t)]))) for t in np.arange(8)*np.pi/4):
                    radius=r;break
        evidence.append({"opening":label,"feature":feature,"uv":p,"expected":surfaces,"first":direct,"nearest_radius_px":radius})
    return {"asset_sha256":meta["sha256"],"triangles":len(tri),"projection_sha256":hashlib.sha256((HERE/"repaired-front-pixel-camera.json").read_bytes()).hexdigest(),"source_image_sha256":matrix["image"],"count":len(evidence),"direct":sum(r["nearest_radius_px"]==0 for r in evidence),"within_three_pixels":sum(r["nearest_radius_px"] is not None for r in evidence),"points":evidence}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh",type=Path);parser.add_argument("output",type=Path)
    args=parser.parse_args();report=check(args.mesh);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(args.mesh.name, report["direct"],report["within_three_pixels"],report["count"])
