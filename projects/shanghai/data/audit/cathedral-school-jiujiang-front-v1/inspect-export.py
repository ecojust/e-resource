"""CPU inspection of decoded GLB positions, UVs and PNGs for 219 Jiujiang Road.

Usage: python -B inspect-export.py decoded-full.glb output_directory
An optional --views JSON file contains [{name, eye, target, width_m}, ...].
The camera is in author coordinates (+Y towards the street, Z upwards).
"""
import argparse
import ctypes
import hashlib
import io
import json
import math
import os
import runpy
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def sha(data):
    return hashlib.sha256(data).hexdigest()


def helpers():
    local = Path(__file__).resolve()
    for city in [*local.parents, Path(os.environ.get("SHANGHAI_PROJECT_ROOT", "/workspace/e-resource/projects/shanghai"))]:
        audit = city / "data/audit"
        reader = audit / "postal-office-v1/independent-glb-review-helpers.py"
        raster = audit / "weile-garden-gate-v1/default-source-visibility/raster.cpp"
        if reader.is_file() and raster.is_file():
            return reader, raster
    raise FileNotFoundError("Cannot find the shared geometry reader and raster.cpp")


def unit(v):
    return v / np.linalg.norm(v)


def default_views():
    return [
        ("north-street-front", [37.7, 51, 13], [37.7, 0, 11], None),
        ("pointed-entrance", [39, 13.5, 3.3], [37.7, 0, 2.95], 10.55),
        ("west-gable", [29, 16, 22], [26.9, .76, 20.0], 14.0),
        ("east-gable", [46, 16, 22], [48.6, .76, 20.0], 14.0),
        ("two-storey-stone-window", [38.5, 13, 11.2], [37.7, 0, 10.1], 9.2),
        ("west-shield-and-window-head", [27.05, 6.7, 18.45], [26.9, .76, 17.82], 3.1),
        ("four-lobed-window-spandrels", [38.25, 7.2, 10.1], [37.7, 0, 9.47], 4.5),
        ("east-ground-side-door", [51.0, 10.5, 2.1], [50.52, .76, 1.80], 7.15),
        ("brick-bond-and-stone", [46.3, 4.7, 12.35], [46.05, .71, 12.30], 2.05),
    ]


def load_textures(path, materials):
    raw = path.read_bytes()
    assert struct.unpack_from("<4sII", raw) == (b"glTF", 2, len(raw))
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(raw[20:20+size])
    n, chunk = struct.unpack_from("<II", raw, 20+size)
    assert chunk == 0x004E4942 and len(raw) == 28+size+n
    buf = memoryview(raw)[28+size:]
    textures, source = {}, {}
    factor = np.array([m.get("pbrMetallicRoughness",{}).get("baseColorFactor",[1.,1.,1.,1.])[:3] for m in doc["materials"]])

    def accessor(index):
        a = doc["accessors"][index]
        assert "sparse" not in a
        view = doc["bufferViews"][a["bufferView"]]
        dtype = np.dtype({5121:"u1",5123:"<u2",5125:"<u4",5126:"<f4"}[a["componentType"]])
        cols = {"SCALAR":1, "VEC2":2}[a["type"]]
        v = np.ndarray((a["count"],cols), dtype, buf, view.get("byteOffset",0)+a.get("byteOffset",0),
                       (view.get("byteStride",cols*dtype.itemsize),dtype.itemsize))
        if a.get("normalized",False):
            assert np.issubdtype(dtype,np.unsignedinteger)
            v = v.astype(float)/np.iinfo(dtype).max
        return v

    for i,m in enumerate(doc["materials"]):
        spec = m.get("pbrMetallicRoughness",{}).get("baseColorTexture")
        if spec is None:
            continue
        assert spec.get("texCoord",0) == 0 and not spec.get("extensions")
        t = doc["textures"][spec["index"]]
        pic = doc["images"][t["source"]]
        assert pic["mimeType"]=="image/png" and "bufferView" in pic
        view = doc["bufferViews"][pic["bufferView"]]
        start = view.get("byteOffset",0)
        encoded = bytes(buf[start:start+view["byteLength"]])
        assert encoded.startswith(b"\x89PNG\r\n\x1a\n")
        with Image.open(io.BytesIO(encoded)) as image:
            assert image.format == "PNG"
            if "A" in image.getbands():
                assert image.getchannel("A").getextrema() == (255,255)
            tex = np.array(image.convert("RGB"))
        sampler = doc.get("samplers",[])[t["sampler"]] if "sampler" in t else {}
        textures[i]=(tex,sampler)
        source[i]={"name":m.get("name",str(i)),"image_index":t["source"],"embedded_bytes":len(encoded),
                   "embedded_sha256":sha(encoded),"texture_dimensions":[tex.shape[1],tex.shape[0]],
                   "sampler":sampler,"uv_vertex_triangles":0}

    uv = np.full((len(materials),3,2),np.nan,dtype=np.float32)
    cursor=0
    def walk(idx):
        nonlocal cursor
        node=doc["nodes"][idx]
        if "mesh" in node:
            for prim in doc["meshes"][node["mesh"]]["primitives"]:
                m=prim["material"]
                order=(accessor(prim["indices"]).reshape(-1) if "indices" in prim else
                       np.arange(doc["accessors"][prim["attributes"]["POSITION"]]["count"]))
                faces=order.reshape(-1,3)
                end=cursor+len(faces)
                assert np.all(materials[cursor:end]==m)
                if m in textures:
                    attr=accessor(prim["attributes"]["TEXCOORD_0"])
                    uv[cursor:end]=attr[faces]
                    assert np.isfinite(uv[cursor:end]).all()
                    source[m]["uv_vertex_triangles"]+=len(faces)
                cursor=end
        for child in node.get("children",[]):walk(child)
    for root in doc["scenes"][doc.get("scene",0)]["nodes"]:walk(root)
    assert cursor==len(materials) and textures and all(v["uv_vertex_triangles"] for v in source.values())
    for m,info in source.items():
        a=uv[materials==m]
        info["indexed_texcoord_sha256"]=sha(a.astype("<f4").tobytes())
        info["uv_bounds"]=[a.min(axis=(0,1)).tolist(),a.max(axis=(0,1)).tolist()]
    return textures,source,uv,factor


def barycentric(tri, pts):
    a=tri[:,1]-tri[:,0]
    b=tri[:,2]-tri[:,0]
    d=pts-tri[:,0]
    dot=lambda v,w:np.einsum("ij,ij->i",v,w)
    aa,ab,bb,da,db=dot(a,a),dot(a,b),dot(b,b),dot(d,a),dot(d,b)
    det=aa*bb-ab*ab
    assert np.all(det>1e-18)
    r=(bb*da-ab*db)/det
    s=(aa*db-ab*da)/det
    return np.column_stack((1-r-s,r,s))


def texel_axis(i,n,mode):
    if mode==33071:return np.clip(i,0,n-1)
    if mode==10497:return np.mod(i,n)
    if mode==33648:
        t=np.mod(i,2*n)
        return np.where(t<n,t,2*n-1-t)
    raise ValueError(f"Unsupported wrap mode {mode}")


def srgb_to_linear(c):
    return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)


def linear_to_srgb(c):
    return np.where(c<=.0031308,12.92*c,1.055*np.maximum(c,0)**(1/2.4)-.055)


def sample(texture,sampler,uv):
    height,width=texture.shape[:2]
    p=uv*np.array([width,height])-.5
    mode_x,mode_y=sampler.get("wrapS",10497),sampler.get("wrapT",10497)
    nearest = sampler.get("magFilter",9729)==9728
    i=np.floor(p+(0.5 if nearest else 0)).astype(np.int64)
    x0=texel_axis(i[:,0],width,mode_x);y0=texel_axis(i[:,1],height,mode_y)
    if nearest:
        return srgb_to_linear(texture[y0,x0]/255.)
    x1=texel_axis(i[:,0]+1,width,mode_x);y1=texel_axis(i[:,1]+1,height,mode_y)
    f=p-i
    a,b=f[:,0,None],f[:,1,None]
    return ((1-a)*(1-b)*srgb_to_linear(texture[y0,x0]/255.)+
            a*(1-b)*srgb_to_linear(texture[y0,x1]/255.)+
            (1-a)*b*srgb_to_linear(texture[y1,x0]/255.)+
            a*b*srgb_to_linear(texture[y1,x1]/255.))


def render(mesh,out,views,width=900,height=580):
    reader,raster=helpers()
    tri,material,names,version=runpy.run_path(str(reader))["load_triangles"](mesh)
    textures,source,all_uv,pigment=load_textures(mesh,material)
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-15)
    irradiation=.68+.32*np.maximum(0,normals@unit(np.array([-.34,.57,.75])))
    bounds=[tri.min(axis=(0,1)).tolist(),tri.max(axis=(0,1)).tolist()]
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    with tempfile.TemporaryDirectory(prefix="school-facade-raster-")as tmp:
        so=Path(tmp)/"raster.so"
        subprocess.run(["c++","-O2","-fPIC","-shared",str(raster),"-o",str(so)],check=True)
        draw=ctypes.CDLL(str(so)).draw
        vp=ctypes.c_void_p
        draw.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,
                       ctypes.c_int,vp,vp,vp,vp,ctypes.c_int,vp,vp]
        draw.restype=None
        tags=np.arange(1,len(tri)+1,dtype=np.int32)
        clip=np.zeros(len(tri),np.int32)
        mask=np.zeros(4,dtype=np.float64)
        for name,eye,target,span in views:
            eye,target=np.array(eye,float),np.array(target,float)
            ray=unit(target-eye);right=unit(np.cross(ray,[0,0,1]));up=np.cross(right,ray)
            dist=np.linalg.norm(target-eye);rel=tri-eye
            projected=np.zeros((*tri.shape[:2],5),dtype=np.float64)
            projected[:,:,0]=rel@right;projected[:,:,1]=rel@up;projected[:,:,2]=rel@ray
            if span is None:
                assert np.all(projected[:,:,2]>.4)
                # Fit the actual export from this precise camera with a 5% margin.
                xy=projected[:,:,:2]*dist/projected[:,:,2,None]
                span=2.10*max(abs(xy[:,:,0]).max(),width/height*abs(xy[:,:,1]).max())
            f=width*dist/span
            hits=np.zeros((height,width),np.int32);depth=np.zeros((height,width),np.float32)
            draw(width,height,width/2,height/2,f,len(tri),projected.ctypes.data,tags.ctypes.data,
                 clip.ctypes.data,mask.ctypes.data,0,depth.ctypes.data,hits.ctypes.data)
            yy,xx=np.nonzero(hits);ids=hits[yy,xx]-1
            mats=material[ids]
            assert len(ids)>width*height*.015,f"Empty camera {name}"
            seen=np.bincount(mats,minlength=len(names))
            pixel=np.full((height,width,3),[238,235,226],np.uint8)
            proofs={}
            for m in np.flatnonzero(seen):
                sel=np.flatnonzero(mats==m)
                digest=hashlib.sha256();lo=np.full(3,255.);hi=np.zeros(3)
                for batch in range(0,len(sel),24000):
                    k=sel[batch:batch+24000];x,y=xx[k],yy[k];face=ids[k]
                    rgb=pigment[m]
                    if m in textures:
                        pts=eye+(ray+((x+.5-width/2)/f)[:,None]*right-((y+.5-height/2)/f)[:,None]*up)/depth[y,x,None]
                        weights=barycentric(tri[face],pts)
                        coords=np.einsum("ni,nij->nj",weights,all_uv[face])
                        tex=sample(*textures[m],coords)
                        colour=np.rint(255*linear_to_srgb(tex)).astype(np.uint8)
                        digest.update(colour.tobytes());lo=np.minimum(lo,colour.min(axis=0));hi=np.maximum(hi,colour.max(axis=0))
                        rgb=rgb*tex
                    pixel[y,x]=np.rint(255*np.clip(linear_to_srgb(rgb*irradiation[face,None]),0,1)).astype(np.uint8)
                if m in textures:
                    proofs[names[m]]={"pixels":int(seen[m]),"sampled_srgb_sha256":digest.hexdigest(),
                                      "sampled_srgb_range":[lo.astype(int).tolist(),hi.astype(int).tolist()]}
            path=out/(name+".jpg");Image.fromarray(pixel).save(path,quality=91)
            rows.append(dict(view=name,eye=eye.tolist(),target=target.tolist(),width_m_at_target=float(span),
                             pixels=len(ids),image=path.name,image_sha256=sha(path.read_bytes()),texture_samples=proofs,
                             material_pixels={names[m]:int(seen[m])for m in np.flatnonzero(seen)}))
    assert any(v["texture_samples"] for v in rows),"No textured surface was visible"
    report=dict(passed=True,model=version,mesh_faces=len(tri),bounds_x_y_z=bounds,reader_sha256=sha(reader.read_bytes()),
                raster_sha256=sha(raster.read_bytes()),inspection_script_sha256=sha(Path(__file__).read_bytes()),
                image_size=[width,height],embedded_textures=list(source.values()),views=rows)
    (out/"views.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    return report


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("decoded_glb",type=Path);cli.add_argument("output",type=Path)
    cli.add_argument("--views",type=Path);cli.add_argument("--dimensions",nargs=2,type=int,default=[900,580])
    args=cli.parse_args()
    views=default_views() if not args.views else [(s["name"],s["eye"],s["target"],s.get("width_m"))for s in json.loads(args.views.read_text())]
    result=render(args.decoded_glb,args.output,views,*args.dimensions)
    print(json.dumps(dict(views=len(result["views"]),faces=result["mesh_faces"],model=result["model"]["sha256"],
                          embedded_pngs=len(result["embedded_textures"]))))
