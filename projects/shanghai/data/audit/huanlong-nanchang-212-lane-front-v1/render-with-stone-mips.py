"""Document material-aware image sampling at the final camera's pixel footprint."""
import ctypes,hashlib,json,runpy,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from hashlib import sha256
SHARED=runpy.run_path(Path(__file__).absolute().parent.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py')
helpers,load_textures,unit,barycentric,sample,linear_to_srgb,sha=(SHARED[k]for k in ('helpers','load_textures','unit','barycentric','sample','linear_to_srgb','sha'))
def render(mesh,out,views,width=900,height=580):
    reader,raster=helpers()
    tri,material,names,version=runpy.run_path(str(reader))["load_triangles"](mesh)
    textures,source,all_uv,pigment=load_textures(mesh,material)
    pyramids={}
    for m,(tex,sampler) in textures.items():
        im=Image.fromarray(tex);levels=[tex]
        while min(im.size)>1:
            im=im.resize(tuple(max(1,i//2) for i in im.size),Image.Resampling.BOX)
            levels.append(np.asarray(im))
        pyramids[m]=levels
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-15)
    irradiation=.54+.32*np.maximum(0,normals@unit(np.array([-.78,-.63,1.15])))
    bounds=[tri.min(axis=(0,1)).tolist(),tri.max(axis=(0,1)).tolist()]
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    with tempfile.TemporaryDirectory(prefix="huangpu-theatre-raster-")as tmp:
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
                        # Neighbouring pixel rays intersect the same triangle plane.
                        # Their UV footprint selects the LINEAR_MIPMAP_LINEAR level.
                        eye_to=pts-eye;plane_distance=np.einsum("ij,ij->i",eye_to,normals[face])
                        gradients=[]
                        for shift in (right/f,-up/f):
                            vectors=eye_to+shift/depth[y,x,None]
                            div=np.einsum("ij,ij->i",vectors,normals[face])
                            adjacent=eye+vectors*(plane_distance/np.where(abs(div)>1e-14,div,1e-14))[:,None]
                            weights2=barycentric(tri[face],adjacent)
                            uv2=np.einsum("ni,nij->nj",weights2,all_uv[face])
                            gradients.append(np.linalg.norm((uv2-coords)*textures[m][0].shape[0],axis=1))
                        levels=pyramids[m]
                        lod=np.clip(np.log2(np.maximum(1,np.maximum(*gradients))),0,len(levels)-1)
                        level0=lod.astype(int);frac=lod-level0;tex=np.zeros((len(coords),3))
                        for level in np.unique(level0):
                            sel_level=(level0==level);base=coords[sel_level];blend=frac[sel_level,None]
                            tex[sel_level]=(1-blend)*sample(levels[level],textures[m][1],base)+blend*sample(levels[min(level+1,len(levels)-1)],textures[m][1],base)
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


