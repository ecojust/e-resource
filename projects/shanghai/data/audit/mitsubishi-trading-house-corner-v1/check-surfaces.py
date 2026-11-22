"""Sample the actual exported street windows, single flat portal, curved spandrels, three window axes, drum and roof rails."""
from pathlib import Path
from io import BytesIO
from tempfile import TemporaryDirectory
import hashlib,json,math,gzip,subprocess,sys
import numpy as np
import trimesh
ID='huangpu-mitsubishi-trading-house-round-corner'
R=2.62

def probes():
    samples=[]
    def at(label,radius,angle,z,low,high):
        n=np.array([math.sin(angle),-math.cos(angle)])
        samples.append((label,(n*radius).tolist(),n.tolist(),z,low,high))
    for angle in (-.87,0,.87):
        for offset in (-.26,.23):
            for z in (6.24,7.65,10.73,11.61,14.83,15.95):
                at('glass behind a real cut in the curved wall',R,angle+offset/R,z,-.275,-.235)
            for z in (18.74,19.17,19.72):
                at('glazing set into the upper drum',2.41,angle+offset/2.41,z,-.275,-.235)
        for z in (6.22,11.56,15.18):
            at('dark central mullion',R,angle,z,-.126,-.098)
        at('moulded springing arch above the sash',R,angle+.045,12.843,.108,.136)
        at('recessed circular spandrel decoration',R,angle+.34/R,9.53,.102,.123)
        at('round window sill on the lower tier',R,angle+.15,5.595,.086,.12)
        for z,low,high in [(8.33,.080,.106),(13.69,.151,.186),(17.62,.295,.326)]:
            at('projecting curved belt course',R,angle+.14,z,low,high)
        at('circular roof cap',2.41,angle,20.72,.21,.24)
    for x in (-.86,-.32,.32,.86):
        for z in (1.1,1.78,2.30):
            samples.append(('paired wood leaves',[x,-1.44],[0,-1],z,-.35,-.332))
    for x in (-1.72,1.72):
        samples.append(('flat stone face beside the portal',[x,-1.44],[0,-1],2.22,-.01,.012))
    samples.append(('projecting central keystone',[.04,-1.44],[0,-1],4.32,.312,.327))
    for j in (-7,-4,0,4,7):
        at('open roof railing upright',2.40,math.tau*j/28,21.17,.012,.027)
    return samples

def probe_glb(blob):
    mesh=trimesh.load(BytesIO(blob),file_type='glb',force='mesh',process=False)
    tri=mesh.triangles[:,:,[0,2,1]]*[1,-1,1];results=[]
    assert abs(float(tri[:,:,2].max())-21.52)<.01, 'The railing above the drum is the highest modeled feature'
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
            out=probe_glb(Path(f).read_bytes());bad=[(v['name'],v['height'],round(v['first'],4))for v in out if not v['passed']];print(f,len(out),'failures',bad);assert not bad
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
