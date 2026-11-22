"""Sample the actual exported street windows, projecting drum, fluted tiers and balcony rails."""
from pathlib import Path
from io import BytesIO
from tempfile import TemporaryDirectory
import hashlib,json,math,gzip,subprocess,sys
import numpy as np
import trimesh
ID='huangpu-gibb-livingston-corner'
ang=lambda d:np.array([math.cos(math.radians(d)),math.sin(math.radians(d))])
R=2.10

def probes():
    points=[]
    def add(name,point,normal,z,low,high):
        points.append((name,point.tolist(),normal.tolist(),z,low,high))
    edges=np.linspace(-162,62,6);depth=R*math.cos(math.radians((edges[1]-edges[0])/2))
    for a,c in zip(edges,edges[1:]):
        n=ang((a+c)/2);t=np.array([-n[1],n[0]]);xy=n*depth+t*.26
        for z in (1.82,5.20,9.30,12.91):add('recessed light in rounded bay',xy,n,z,-.338,-.305)
        add('lower awning inclines over street',xy,n,2.76,.27,.37)
        add('first cornice of round bay',n*R,n,3.53,.166,.195)
        add('upper balcony handrail',n*R,n,8.01,.148,.193)
        add('surviving cap above drum windows',n*R,n,14.00,.073,.122)
    for a in edges:
        n=ang(a)
        for z in (5.20,9.20):add('engaged red brick shaft',n*R,n,z,.126,.178)
    a0=ang(-162)*R;a1=ang(62)*R
    for kind,start,direction,n,axes in [
            ('south',a0+[-4.10,0],np.array([1,0]),np.array([0,-1]),[-2.66,0,2.69]),
            ('east',a1+[0,3.95],np.array([0,1]),np.array([1,0]),[-2.50,0,2.51])]:
        for i,u in enumerate(axes):
            xy=start+direction*(u+.28)
            for z in (1.73,5.03,9.22):add(kind+' street light or entrance glazing',xy,n,z,-.338,-.305)
            for z in (3.52,7.28,11.39):add(kind+' projecting street cornice',xy,n,z,.305,.41)
    return points

def probe_glb(blob):
    mesh=trimesh.load(BytesIO(blob),file_type='glb',force='mesh',process=False)
    tri=mesh.triangles[:,:,[0,2,1]]*[1,-1,1];results=[]
    assert abs(float(tri[:,:,2].max())-14.07)<.015, 'The documented low drum roof is the highest modeled feature'
    for name,xy,normal,z,low,high in probes():
        n=np.array(normal);xy=np.array(xy)
        t=np.array([-n[1],n[0]])
        vertex=np.stack([(tri[:,:,:2]-xy)@t,tri[:,:,2]-z],axis=2)
        a,b,c=vertex.transpose(1,0,2);v0=b-a;v1=c-a
        den=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0];valid=np.abs(den)>1e-8
        u=np.zeros(len(den));v=u.copy();u[valid]=(-a[valid,0]*v1[valid,1]+a[valid,1]*v1[valid,0])/den[valid]
        v[valid]=(-v0[valid,0]*a[valid,1]+v0[valid,1]*a[valid,0])/den[valid]
        hit=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)
        depths=(tri[:,:,:2]-xy)@n
        d=(depths[hit,0]+u[hit]*(depths[hit,1]-depths[hit,0])+v[hit]*(depths[hit,2]-depths[hit,0])).max(initial=-1000)
        results.append(dict(name=name,point_xy=xy.tolist(),outward=n.tolist(),height=z,minimum=low,maximum=high,first=float(d),passed=bool(low<=d<=high)))
    return results

def main():
    if len(sys.argv)>1:
        for f in sys.argv[1:]:
            out=probe_glb(gzip.decompress(Path(f).read_bytes()));bad=[(v['name'],v['height'],round(v['first'],4))for v in out if not v['passed']];print(f,len(out),'failures',bad)
        return
    audit=Path(__file__).resolve().parent;project=audit.parents[2];assets=project/'assets/models/candidates'/ID
    manifest=json.loads((assets/'manifest.json').read_bytes())
    checker=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    codec=project/'vendor/meshopt_decoder.module.js'
    results={}
    with TemporaryDirectory() as tmp:
        for role in ['raw','full','lod']:
            rec=manifest['assets'][role];f=assets/rec['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==rec['sha256']
            plain=f
            if role!='raw':
                plain=Path(tmp)/(role+'.glb')
                subprocess.run(['node',checker,f,plain,codec],check=True)
            hits=probe_glb(plain.read_bytes());bad=[v for v in hits if not v['passed']];assert not bad,(role,bad)
            results[role]={'sha256':rec['sha256'],'triangles':rec['triangles'],'samples':hits}
    (audit/'surface-checks.json').write_text(json.dumps({'id':ID,'total_checks':sum(len(r['samples'])for r in results.values()),'variants':results},indent=2)+'\n')
if __name__=='__main__':main()
