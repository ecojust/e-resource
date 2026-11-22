"""Read each shipped / independently decoded GLB, cast first hits and render the matte materials."""
from pathlib import Path
import argparse,ctypes,hashlib,json,math,os,struct,subprocess,sys,tempfile
import numpy as np
from PIL import Image
HERE=Path(__file__).absolute().parent
PROJECT=next((q for q in HERE.parents if(q/'tools/package_architectural_model.py').is_file()),None) or Path(os.environ['E_RESOURCE_SHANGHAI'])
CODE=PROJECT/'source/precise/hongkou-shanyin-229-canted-bay/source'
sys.path.insert(0,str(CODE));sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import Builder
from bay import add_bay,PALETTE,survey_layout

h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()

def glb(path):
    with path.open('rb')as f:
        magic,version,total=struct.unpack('<4sII',f.read(12));length,kind=struct.unpack('<II',f.read(8));doc=json.loads(f.read(length));length,kind=struct.unpack('<II',f.read(8));buf=f.read(length)
        assert magic==b'glTF' and total==path.stat().st_size and version==2
    def view(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];t={5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']]
        dim={'VEC3':3,'SCALAR':1}[a['type']]
        return np.frombuffer(buf,dtype=t,count=dim*a['count'],offset=a.get('byteOffset',0)+v.get('byteOffset',0)).reshape(a['count'],dim)
    tris=[];mats=[]
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            vert=view(prim['attributes']['POSITION']);tri=vert[view(prim['indices']).reshape(-1,3)];tri=tri[:,:,[0,2,1]].copy();tri[:,:,1]*=-1
            tris.append(tri);mats.extend([doc['materials'][prim['material']]['name']]*len(tri))
    return np.vstack(tris),np.array(mats)


def cast(tri,point,ray):
    e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];r=np.cross(ray,e2);det=(e1*r).sum(axis=1);mask=abs(det)>1.e-8;inv=np.divide(1,det,out=np.zeros_like(det),where=mask)
    v0=point-tri[:,0];u=inv*(v0*r).sum(axis=1);q=np.cross(v0,e1);v=inv*(q*ray).sum(axis=1);t=inv*(q*e2).sum(axis=1);valid=mask&(u>=0)&(v>=0)&(u+v<=1)&(t>0)
    ix=np.argmin(np.where(valid,t,np.inf))
    return (ix,float(t[ix])) if valid[ix] else (None,None)


def check(path,lod):
    b=Builder(PALETTE);add_bay(b,lod)
    for part in b.parts:
        vertices=np.array(part['vertices']);vs=vertices[part['triangles']];v=((vs[:,0]*np.cross(vs[:,1],vs[:,2])).sum()/6)
        if v<=1e-11:raise ValueError((part['label'],v))
    tri,mats=glb(path);actual=[]
    cases=[('transom glass',.34,.777,['smoke blue']),('transom mullion',.47,.775,['vermilion']),('right jamb',.739,.53,['vermilion','brick']),('apron crown',.45,.276,['red']),('left sill',.21,.312,['pale stone']),('bricks below sill',.41,.16,['brick']),('red bottom band',.412,.056,['facing','brick']),('upper fascia',.42,1.046,['facing','brick']),('upper copper-brown cornice',.35,1.091,['facing','brick']),('cap',.29,1.137,['iron']),('iron upper bar',.43,1.42,['iron']),('air above crown',.41,1.47,[])]
    dims=survey_layout();height=dims['height'];ang=math.radians(dims['turn_degrees'])
    for face in ['oblique','central']:
        w=height*dims['left_width_ratio' if face=='oblique' else 'center_width_ratio'];tx,ty=(math.cos(ang),-math.sin(ang))if face=='oblique' else(1.,0.);ox,oy=(-w*tx,-w*ty)if face=='oblique' else(0.,0.);normal=np.array([ty,-tx,0])
        for name,u,z,expected in cases:
            if name=='right jamb':u=.756 if face=='oblique'else .735
            if name=='transom mullion':u=.4665 if face=='oblique'else .473
            if name=='left sill':z=.317 if face=='oblique'else .302
            if name=='apron crown':z=.272 if face=='oblique'else .265
            pt=np.array([ox+tx*w*u,oy+ty*w*u,z*height])+normal*height*.55
            ix,t=cast(tri,pt,-normal);material=None if ix is None else str(mats[ix]);okay=not expected and ix is None or ix is not None and any(q in material for q in expected)
            actual.append(dict(face=face,feature=name,uv=[u,z],found=material,depth=t,passed=bool(okay)))
    out=dict(file=path.name,sha256=h(path),faces=len(tri),positive_closed_solids=len(b.parts),checks=actual)
    return out

def norm(v):
    return v/np.linalg.norm(v)

def render(path,output):
    tri,names=glb(path);normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-14)
    light=.72+.28*np.maximum(0,normals@norm(np.array([-.6,-.9,1.5])))
    lin=np.array([PALETTE[k]['color'][:3] for k in names])*light[:,None]
    rgb=np.clip(np.rint(255*np.where(lin<.0031308,12.92*lin,1.055*lin**(1/2.4)-.055)),0,255).astype(np.uint8)
    cams={'both-faces':([-.46,-1.,.12],[.09,.28,2.28],5.1),'red-window':([.03,-1.,.02],[.64,.0,1.86],2.24),'iron-rail':([-.4,-1.,.09],[.02,.27,4.11],3.07),'apron':([-.43,-1.,.21],[.06,.18,.91],2.95),'opening-leaf':([-.75,-1.,.1],[-.55,.48,1.85],1.85),'brick-arch':([-.42,-1.,.03],[.02,.20,2.88],2.98)}
    raster=PROJECT/'data/audit/weile-garden-gate-v1/default-source-visibility/raster.cpp';tags=np.arange(1,len(tri)+1,dtype=np.int32);clipped=np.zeros(len(tri),np.int32);mask=np.zeros(4,float);output.mkdir(exist_ok=True,parents=True);rows=[]
    with tempfile.TemporaryDirectory() as temp:
        so=Path(temp)/'surface.so';subprocess.run(['c++','-O2','-fPIC','-shared',raster,'-o',so],check=True)
        fd=os.memfd_create("bay-raster");os.write(fd,so.read_bytes());draw=ctypes.CDLL(f"/proc/self/fd/{fd}").draw;os.close(fd);vp=ctypes.c_void_p;draw.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_int,vp,vp,vp,vp,ctypes.c_int,vp,vp];draw.restype=None
        for name,(dirn,tgt,vspan) in cams.items():
            width,height=800,750
            ray=-norm(np.array(dirn));target=np.array(tgt);eye=target-18*ray;right=norm(np.cross(ray,[0.,0.,1.]));up=np.cross(right,ray);rel=tri-eye
            q=np.zeros((*tri.shape[:2],5),np.float64);q[:,:,0]=rel@right;q[:,:,1]=rel@up;q[:,:,2]=rel@ray
            hits=np.zeros((height,width),np.int32);depth=np.zeros((height,width),np.float32)
            draw(width,height,width/2,height/2,18*height/vspan,len(tri),q.ctypes.data,tags.ctypes.data,clipped.ctypes.data,mask.ctypes.data,0,depth.ctypes.data,hits.ctypes.data)
            touched=hits>0;idx=hits[touched]-1;assert len(idx)>15000
            pix=np.full((height,width,3),[228,226,215],dtype=np.uint8);pix[touched]=rgb[idx];f=output/(name+'.jpg');Image.fromarray(pix).save(f,quality=91)
            rows.append(dict(camera=name,eye=eye.tolist(),target=target.tolist(),height=vspan,pixels=int(touched.sum()),materials=sorted(set(names[idx])),image_sha256=h(f)))
    return rows

if __name__=='__main__':
    x=argparse.ArgumentParser(description=__doc__);x.add_argument('raw',type=Path);x.add_argument('full',type=Path);x.add_argument('low',type=Path);x.add_argument('output',type=Path);a=x.parse_args();a.output.mkdir(exist_ok=True,parents=True)
    report={}
    for key,path,low in [('raw',a.raw,False),('full',a.full,False),('lod',a.low,True)]:
        r=check(path,low);assert all(p['passed']for p in r['checks']),[p for p in r['checks']if not p['passed']]
        if key!='raw':r['views']=render(path,a.output/key)
        report[key]=r
    q=a.output/'three-role-inspection.json';q.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:len(v['checks'])for k,v in report.items()})
