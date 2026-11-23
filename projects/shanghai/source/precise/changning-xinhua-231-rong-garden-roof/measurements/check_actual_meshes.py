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
    assert len(doc['images'])==1 and doc['samplers'][0]['wrapS']==doc['samplers'][0]['wrapT']==10497
    view=doc['bufferViews'][doc['images'][0]['bufferView']]
    blob=binary[view['byteOffset']:view['byteOffset']+view['byteLength']]
    assert hashlib.sha256(blob).hexdigest()==digest(here.parent/'source/garden-roof-tiles.png')
    result=np.array(tri),np.array(labels),mats,texcoords
    if with_texture:
        return *result,np.concatenate(triangle_uv),np.asarray(Image.open(io.BytesIO(blob)).convert('RGB'))
    return result

def ray(tri,origin,direction):
    e,f=tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
    cross=np.cross(direction,f);den=np.einsum('ij,ij->i',e,cross);ok=abs(den)>1e-8
    inv=np.divide(1,den,out=np.zeros_like(den),where=ok)
    delta=np.asarray(origin)-tri[:,0];u=np.einsum('ij,ij->i',delta,cross)*inv
    q=np.cross(delta,e);v=q@direction*inv;t=np.einsum('ij,ij->i',f,q)*inv
    t[~(ok&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1.0000001)&(t>1e-6))]=np.inf
    ix=np.argmin(t);return int(ix) if np.isfinite(t[ix]) else None

def photo_projection():
    # These refer to the 550 x 345 source from People's Daily, not pixels from the 3D renderer.
    names=['garden gable apex','left roof lip','right roof lip','left lower rail','right lower rail','dormer left lip','dormer right lip','far roof rear peak','right east cross peak']
    xyz=np.array([[-5.80,-6.08,9.72],[-8.92,-6.08,6.46],[-2.68,-6.08,6.46],[-8.65,-5.93,3.42],[-2.95,-5.93,3.42],[-2.57,-3.34,8.11],[1.83,-3.34,8.11],[-8.7,5.92,10.38],[-2.35,6.13,10.18]])
    pix=np.array([[229,166],[218,180],[251,204],[222,200],[250,218],[264,183],[297,197],[285,112],[325,136]])
    def projection(p):
        az,el,scale,u,v=p
        ca,sa=np.cos(az),np.sin(az);ce,se=np.cos(el),np.sin(el)
        right=np.array([ca,sa,0.]);up=np.array([-sa*se,ca*se,ce])
        return np.column_stack((u+scale*(xyz@right),v-scale*(xyz@up)))
    fit=np.array([.8,.65,8.,300.,240.])
    def residual(p):
        return (projection(p)[:7]-pix[:7]).ravel()
    steps=np.diag([1e-6,1e-6,1e-5,1e-4,1e-4])
    for iteration in range(30):
        jacobian=np.column_stack([(residual(fit+d)-residual(fit-d))/(2*d[i]) for i,d in enumerate(steps)])
        correction,_,rank,_=np.linalg.lstsq(jacobian,-residual(fit),rcond=None)
        assert rank==5
        fit+=correction
        if np.linalg.norm(correction)<1e-8:break
    else:
        raise ArithmeticError('Camera fit did not converge')
    fitted=projection(fit);errors=np.linalg.norm(fitted-pix,axis=1)
    return dict(method='level aerial weak-perspective camera: seven garden-side controls set scale, azimuth and elevation; two rear roof points check the adopted roof placement. Roof locations were revised against the same photograph.',source_size=[550,345],camera_azimuth_elevation_scale_origin=fit.tolist(),rms_px=float(np.sqrt(np.mean(errors**2))),max_px=float(errors.max()),controls=[dict(name=name,model_xyz=coord.tolist(),observed_pixels=target.tolist(),projected_pixels=np.round(place,2).tolist(),residual_px=round(float(err),2)) for name,coord,target,place,err in zip(names,xyz,pix,fitted,errors)])
def check(p,lod):
    from build_model import build,roof_planes
    tri,ids,mats,uv=mesh(p);b=build(lod);vol=[signed_part(v) for v in b.parts]
    rays=[]
    for name,shape,(a,c,d) in roof_planes():
        for sx in np.linspace(.15,.85,5):
            for sy in np.linspace(.15,.85,4):
                x0,y0,x1,y1=shape.bounds;x=x0+(x1-x0)*sx;y=y0+(y1-y0)*sy
                from shapely.geometry import Point
                footprint=Point(x,y);heights=[(coeff.dot((x,y,1)),part)for part,plan,coeff in roof_planes()if plan.contains(footprint)]
                if not heights or max(heights)[1]!=name:continue
                ix=ray(tri,[x,y,18],np.array([0,0,-1]));material=mats[ids[ix]]['name'] if ix is not None else None
                assert material in ('mottled clay tiles','clay ridge and verge'),(name,x,y,material)
                rays.append(dict(part=name,xyz=[round(x,3),round(y,3),round(float(a*x+c*y+d),3)],first=material))
    for name,x,z,kind in [('left timber',-7.52,5.20,'dark timber'),('gable plaster',-7.90,4.82,'cool lime infill'),('gable glazing',-6.12,5.25,'shaded window'),('dormer opening',-.41,7.59,'shaded window'),('setback wall',.24,4.49,'cool lime infill')]:
        ix=ray(tri,[x,-18,z],np.array([0,1,0]));mat=mats[ids[ix]]['name'] if ix is not None else None;assert mat==kind,(name,mat,kind)
        rays.append(dict(part=name,x=x,z=z,first=mat))
    return dict(file=p.name,sha256=digest(p),closed_parts=len(vol),min_solid_volume_m3=min(vol),triangles=len(tri),materials=len(mats),textured_triangle_corners=uv,rays=rays)
if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('mesh_dir',type=Path);pa.add_argument('output',type=Path);args=pa.parse_args()
    report=dict(photo=photo_projection(),roles=[check(args.mesh_dir/(role+'-source.glb'),role=='lod')for role in ['full','lod']])
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(report['photo']['rms_px'],[(r['closed_parts'],r['triangles'],len(r['rays']))for r in report['roles']])
