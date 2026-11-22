"""Check each surveyed window contour against the pinhole and both actual mesh exports."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
from shapely.geometry import Point,Polygon
here=Path(__file__).absolute()
w=here.parent.parent
source=next(folder for folder in (w/'source',w/'work') if (folder/'cypress_brick_windows.py').is_file())
possible=[*here.parents,Path.cwd(),Path.cwd()/'projects/shanghai',Path.cwd()/'e-resource/projects/shanghai']
if os.environ.get('SHANGHAI_PROJECT_ROOT'):
    possible.insert(0,Path(os.environ['SHANGHAI_PROJECT_ROOT']))
project=next(folder for folder in possible if (folder/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(source))
sys.path.insert(0,str(project/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from cypress_brick_windows import add_brick_front,PALETTE,on_wall,survey,BRICKS,GLASS,JOINT,SASH,SILL
m,windows=survey()
class Capture(Builder):
    def add(self,vertices,faces,material,label):
        assert material in self.palette
        v=np.asarray(vertices,float);rows=[]
        for f in faces:
            for j in range(1,len(f)-1):rows.append([f[0],f[j],f[j+1]])
        t=v[np.asarray(rows,int)]
        keep=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)>1e-10
        self.parts.append((material,label,t[keep]))

def closest(tri,mats,eye,target):
    ray=target-eye
    e1,e2=tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
    h=np.cross(np.broadcast_to(ray,e2.shape),e2);det=np.einsum('ij,ij->i',h,e1);inv=np.divide(1,det,where=abs(det)>1e-10,out=np.zeros(len(det)))
    delta=eye-tri[:,0];u=inv*np.einsum('ij,ij->i',delta,h);q=np.cross(delta,e1)
    v=inv*(q@ray);t=inv*np.einsum('ij,ij->i',e2,q)
    ids=np.flatnonzero((abs(det)>1e-10)&(u>=0)&(v>=0)&(u+v<=1)&(t>0))
    if not len(ids):return None
    return str(mats[ids[np.argmin(t[ids])]])
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
eye=np.array(json.loads((w/'measurements/lawn-camera.json').read_bytes())['eye_xyz'])
results={}
for lod in (False,True):
    b=Capture(PALETTE);add_brick_front(b,lod)
    tri=np.concatenate([t for _,_,t in b.parts]);mats=np.concatenate([np.full(len(t),mat,object) for mat,_,t in b.parts])
    assert np.isfinite(tri).all()
    samples={}
    for name,pixel,approved in [('left head half',(475,263),GLASS),('left second light',(484.3,264),GLASS),('right top left',(501.4,258.8),GLASS),('right lower right',(511.3,274.4),GLASS),('lawn left',(482.3,342),GLASS),('lawn middle',(490.5,345.7),GLASS),('lawn right',(503.2,345),GLASS),('wall between windows',(493,271),(*BRICKS,JOINT)),('wall below upper windows',(485,301),(*BRICKS,JOINT))]:
        x,z=on_wall([pixel])[0];hit=closest(tri,mats,eye,np.array([x,0,z]))
        samples[name]=hit
        assert hit in approved,(name,pixel,hit)
    for material,label,t in b.parts:
        if material==SILL:
            signed=np.sum(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])))/6
            assert signed>0,(label,signed)
    for rec in windows:
        p=on_wall(rec['corners']);xyz=np.c_[p[:,0],np.zeros(len(p)),p[:,1],np.ones(len(p))];uv=xyz@m.T
        assert np.max(abs(uv[:,:2]/uv[:,2,None]-rec['corners']))<1e-7
    results['lod' if lod else 'full']=dict(triangles=len(tri),material_count=len(set(mats)),samples=samples)
out=w/'measurements/central-wall-verification.json'
out.write_text(json.dumps(dict(helper_sha256=sha(source/'cypress_brick_windows.py'),camera_sha256=sha(w/'measurements/lawn-camera.json'),openings_sha256=sha(w/'measurements/second-storey-openings.json'),results=results,ground_opening_foot='estimated at the line screened by planting',bond='nominal running bond, with photographed bed lines; vertical joints cannot be counted from the photograph'),ensure_ascii=False,indent=2)+'\n')
print(sha(out),results)
