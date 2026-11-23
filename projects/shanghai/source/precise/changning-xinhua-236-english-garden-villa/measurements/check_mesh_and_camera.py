"""Check the two published GLBs, closed source parts, garden-face rays and source-photo projection."""
import argparse,hashlib,io,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image

here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'source'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def signed_part(p):
    vertices=np.asarray(p['vertices']);_,remap=np.unique(np.round(vertices,6),axis=0,return_inverse=True)
    faces=remap[np.asarray(p['triangles'])]
    e=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    n=np.unique(e,axis=0,return_counts=True)[1]
    a,b,c=vertices[np.asarray(p['triangles'])].transpose(1,0,2)
    volume=float(np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6)
    assert np.all(n==2) and volume>1e-9,(p['label'],volume,n.min(),n.max())
    return volume

def mesh(p, with_texture=False):
    data=p.read_bytes();js,chunk=struct.unpack_from('<II',data,12);assert chunk==0x4e4f534a
    doc=json.loads(data[20:20+js]);binary=data[28+js:]
    def arr(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        count=a['count'];dim={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']],count=count*dim,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(count,dim)
    mats=doc['materials'];tri=[];labels=[];texcoords=0;triangle_uv=[]
    for sub in doc['meshes'][0]['primitives']:
        attr=sub['attributes'];pos=arr(attr['POSITION'])[:,[0,2,1]].astype(float);pos[:,1]*=-1
        ids=arr(sub['indices']).reshape(-1,3);tri.extend(pos[ids]);mi=sub['material'];labels.extend([mi]*len(ids))
        if 'TEXCOORD_0'in attr:
            uv=arr(attr['TEXCOORD_0']);assert np.isfinite(uv).all() and np.max(uv)-np.min(uv)>1
            texcoords+=len(ids)*3
            if with_texture:triangle_uv.append(uv[ids])
        elif with_texture:
            triangle_uv.append(np.zeros((len(ids),3,2)))
    png={}
    for i,im in enumerate(doc['images']):
        v=doc['bufferViews'][im['bufferView']];blob=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
        assert digest(here.parent/'source'/im['name'])==hashlib.sha256(blob).hexdigest()
        png[i]=np.asarray(Image.open(io.BytesIO(blob)).convert('RGB'))
    assert len(png)==2 and all(v.get('wrapS',10497)==v.get('wrapT',10497)==10497 for v in doc['samplers'])
    base=(np.asarray(tri),np.asarray(labels),mats,texcoords)
    if with_texture:
        return *base,np.concatenate(triangle_uv),{i:png[doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']] for i,m in enumerate(mats) if 'baseColorTexture' in m['pbrMetallicRoughness']}
    return base

def ray(tri,origin,direction):
    e,f=tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
    cross=np.cross(direction,f);den=np.einsum('ij,ij->i',e,cross);ok=abs(den)>1e-8
    inv=np.divide(1,den,out=np.zeros_like(den),where=ok)
    delta=np.asarray(origin)-tri[:,0];u=np.einsum('ij,ij->i',delta,cross)*inv
    q=np.cross(delta,e);v=q@direction*inv;t=np.einsum('ij,ij->i',f,q)*inv
    t[~(ok&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1.0000001)&(t>1e-6))]=np.inf
    ix=np.argmin(t);return int(ix) if np.isfinite(t[ix]) else None

def render(path,source,destination):
    tri,labels,mats,_,tex,images=mesh(path,True)
    rotation=np.array(source['world_to_camera_rotation']);eye=np.array(source['eye']);principal=np.array(source['principal_point']);f=source['focal_px']
    actual=(tri-eye)@rotation.T;points=principal+f*actual[:,:,:2]/actual[:,:,2:]
    width,height=(2*principal).astype(int);canvas=np.full((height,width,3),[225,228,226],np.uint8);depth=np.zeros((height,width))
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
    for i,(p,cam) in enumerate(zip(points,actual)):
        if cam[:,2].min()<=0:continue
        x0,y0=np.maximum(0,np.floor(p.min(axis=0)).astype(int));x1,y1=np.minimum([width-1,height-1],np.ceil(p.max(axis=0)).astype(int))
        if x1<x0 or y1<y0:continue
        x,y=p.T;den=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if abs(den)<1e-8:continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        a=((y[1]-y[2])*(xx-x[2])+(x[2]-x[1])*(yy-y[2]))/den
        b=((y[2]-y[0])*(xx-x[2])+(x[0]-x[2])*(yy-y[2]))/den;c=1-a-b
        bary=np.stack((a,b,c),axis=-1);weighted=bary/cam[:,2];inv_z=weighted.sum(-1)
        crop=np.s_[y0:y1+1,x0:x1+1];show=(bary.min(-1)>=0)&(inv_z>depth[crop])
        mat=labels[i];light=.65+.35*max(0,normals[i]@[-.38,-.50,.77])
        color=np.asarray(mats[mat]['pbrMetallicRoughness']['baseColorFactor'][:3])*255
        if mat in images:
            uv=(weighted[show]@tex[i])/inv_z[show,None];im=images[mat];h,w=im.shape[:2];color=im[np.floor(uv[:,1]*h).astype(int)%h,np.floor(uv[:,0]*w).astype(int)%w]*color/255
        canvas[crop][show]=np.clip(color*light,0,255).astype('uint8');depth[crop][show]=inv_z[show]
    Image.fromarray(canvas).save(destination,quality=89)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('near',type=Path);p.add_argument('far',type=Path);p.add_argument('cameras',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);from build_model import build
    stations=json.loads(a.cameras.read_text())
    samples={'leaf-off-2014':{'Salmon flat machine tile':[[131,180],[135,194],[261,229],[255,255],[562,243]],'Blackened timber frame':[[169,406],[211,418]],'Weathered chimney brick':[[456,90],[447,111],[466,159],[472,334]],'Recessed blue green glass':[[301,332],[330,309],[318,218],[218,210],[631,341]]},
             'leaf-on-2014':{'Salmon flat machine tile':[[217,103],[322,156],[335,174]],'Weathered chimney brick':[[498,305],[495,334]],'Recessed blue green glass':[[374,231],[386,245],[381,137],[286,128]]},
             'planning-p12-128':{'Salmon flat machine tile':[[68,92],[78,101],[122,111]],'Weathered chimney brick':[[242,159],[246,151]],'Recessed blue green glass':[[155,155],[106,95],[90,146]]}}
    out={}
    for path,lod in [(a.near,False),(a.far,True)]:
        key='lod' if lod else 'full';parts=build(lod).parts;vol=[signed_part(x) for x in parts];tri,ids,mats,uv=mesh(path);shots=[]
        for station,groups in samples.items():
            s=stations[station];r=np.array(s['world_to_camera_rotation']);fx=s['focal_px'];cx,cy=s['principal_point']
            for expected,pix in groups.items():
                for px,py in pix:
                    direction=r.T@[(px-cx)/fx,(py-cy)/fx,1];idx=ray(tri,s['eye'],direction);got=None if idx is None else mats[ids[idx]]['name']
                    shots.append(dict(station=station,pixel=[px,py],intended=expected,actual=got,matched=got==expected))
        out[key]=dict(sha256=digest(path),closed_positive_components=len(parts),minimum_volume_m3=min(vol),triangles=len(tri),uv_corners=uv,rays=shots,matches=sum(x['matched'] for x in shots))
        print(key,len(parts),len(tri),out[key]['matches'],len(shots))
    (a.out/'mesh-photo-check.json').write_text(json.dumps(out,indent=2)+'\n')
    for n,s in stations.items():render(a.near,s,a.out/(n+'-model.jpg'))
