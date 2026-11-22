"""Check the earliest material encountered by street-normal rays in a decoded GLB."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
from upper_bookshop_windows import BEAD,FAN,GLASS,PAINT,openings,transform,window_parts


def load_triangles(path):
    data=path.read_bytes()
    magic,version,size,n,kind=struct.unpack_from("<4sIIII",data)
    if (magic,version,size,kind)!=(b"glTF",2,len(data),0x4E4F534A):
        raise ValueError("Invalid binary glTF")
    doc=json.loads(data[20:20+n]); offset=n+28
    def array(index):
        a=doc["accessors"][index];v=doc["bufferViews"][a["bufferView"]]
        dtype=np.dtype({5121:"u1",5123:"<u2",5125:"<u4",5126:"<f4"}[a["componentType"]]);cols={"SCALAR":1,"VEC3":3}[a["type"]]
        return np.ndarray((a["count"],cols),dtype=dtype,buffer=data,
                          offset=offset+v.get("byteOffset",0)+a.get("byteOffset",0),
                          strides=(v.get("byteStride",cols*dtype.itemsize),dtype.itemsize))
    triangles=[];materials=[]
    for idx in doc["scenes"][doc.get("scene",0)]["nodes"]:
        node=doc["nodes"][idx]
        if any(k in node for k in ("matrix","rotation","translation","scale","children")):
            raise ValueError("Expected the normal world-coordinate export")
        for p in doc["meshes"][node["mesh"]]["primitives"]:
            native=array(p["attributes"]["POSITION"])[array(p["indices"]).reshape(-1,3)]
            xyz=native[:,:,[0,2,1]].astype(float);xyz[:,:,1]*=-1
            triangles.append(xyz);materials.extend([p["material"]]*len(xyz))
    return np.concatenate(triangles),np.asarray(materials),doc,hashlib.sha256(data).hexdigest()


def shots(r):
    xa,xb,za,zb,tr,rail,y,leaves=window_parts(r)
    mid=(xa+xb)/2
    yield "jamb",(r["left"]+xa)/2,(za+zb)/2,PAINT,y
    yield "meeting rail",mid,tr,PAINT,y
    yield "undivided transom centre",mid,(tr+rail/2+zb)/2,FAN,y+.046
    for side,a,b,z0,z1,h,angle in leaves:
        place,_=transform(h,y+.010,angle)
        x,depth,z=place((a+b)/2,y+.010+.035,(z0+z1)/2)
        yield side+" lower pane",x,z,GLASS,depth
        margin=min(.047,(b-a)*.11)
        x,depth,z=place(a+margin*.45,y+.010,.5*(z0+z1))
        yield side+" leaf stile",x,z,PAINT,depth
        if angle:
            # Street ray through the strip of air beyond the physical free edge.
            free=b if side=="left" else a
            tip=place(free,y+.010,.5*(z0+z1))[0]
            yield side+" clear swing",(free+tip)/2,.5*(z0+z1),None,y+.11


def check(path):
    tris,mats,doc,digest=load_triangles(path)
    names=[m["name"] for m in doc["materials"]]
    x,z=tris[:,:,0],tris[:,:,2]
    span=(x.min(1),x.max(1),z.min(1),z.max(1))
    rows=[];fail=[]
    for r in openings():
        for feature,sx,sz,material,depth in shots(r):
            ids=np.flatnonzero((span[0]<=sx)&(span[1]>=sx)&(span[2]<=sz)&(span[3]>=sz))
            t=tris[ids];a=t[:,0,:];u=t[:,1,:]-a;v=t[:,2,:]-a
            det=u[:,0]*v[:,2]-u[:,2]*v[:,0]
            valid=abs(det)>1e-12;den=np.where(valid,det,1)
            dx,dz=sx-a[:,0],sz-a[:,2]
            p=(dx*v[:,2]-dz*v[:,0])/den;q=(u[:,0]*dz-u[:,2]*dx)/den
            valid&=(p>=-1e-7)&(q>=-1e-7)&(p+q<=1+1e-7)
            ys=np.where(valid,a[:,1]+p*u[:,1]+q*v[:,1],np.inf)
            nearest=int(ys.argmin()) if valid.any() else None
            hit=None if nearest is None else names[mats[ids[nearest]]]
            hit_y=None if nearest is None else float(ys[nearest])
            ok=(hit_y is None or hit_y>=depth) if material is None else (material==hit and abs(hit_y-depth)<.006)
            row={"window":r["label"],"feature":feature,"ray_xz":[round(float(sx),4),round(float(sz),4)],
                 "expected_material":material,"expected_y":round(float(depth),4),"first_material":hit,"first_y":None if hit_y is None else round(hit_y,4),"passed":bool(ok)}
            rows.append(row)
            if not ok:fail.append(row)
    return {"asset_sha256":digest,"bytes":path.stat().st_size,"physical_triangles":len(tris),"windows":len(openings()),
            "rays":len(rows),"passed":not fail,"failure_count":len(fail),"checks":rows}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("model",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args(); result=check(args.model)
    args.output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print(args.model.name,result['physical_triangles'],result['rays'],result['failure_count'])
    for r in [s for s in result['checks'] if not s['passed']][:6]:print(r)
    raise SystemExit(int(not result['passed']))
