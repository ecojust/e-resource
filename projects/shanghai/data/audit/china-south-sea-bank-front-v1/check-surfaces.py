"""Check the recessed window panes, door thresholds and both orders of columns in source and packed geometry."""
from pathlib import Path
import gzip,json,sys,hashlib,subprocess
from tempfile import TemporaryDirectory
from io import BytesIO
import numpy as np,trimesh
ID='huangpu-china-south-sea-bank-front'
def probes():
    out=[]
    def at(kind,x,z,low,high):
        out.append((kind,x,z,low,high))
    for x in (-6.6,-2.2,2.2,6.6):
        for dx in (-.437,.437):
            for z in (1.04,2.37,3.55):
                at('smooth paired Tuscan shaft',x+dx,z,1.619,1.715)
            at('square Tuscan capital',x+dx,3.933,1.74,1.77)
        for z,minr in ((5.90,.61),(8.76,.56),(14.62,.46)):
            at('fluted Doric shaft',x,z,1+minr,1.69)
        at('Doric capital plate',x,15.442,1.785,1.794)
    for x in (-4.4,0,4.4):
        for z in (6.21,9.62,12.99):
            for dx in (-.79,.19,.76):
                at('recessed glass within original window',x+dx,z,-.323,-.315)
        for z in (7.799,11.276,14.589):at('projecting stone window head',x+.52,z,.212,.224)
        for z in (1.37,2.27):at('doorway glazing',x+.25,z,-.316,-.296)
        at('granite threshold',x+.24,.074,.205,.217)
    for door in (-4.4, 0):
        for leaf in (-.568, .568):
            center = door + leaf
            at('gilded openwork on upper door glass', center, 2.64, -.111, -.103)
            at('open glass beside gilded door outline', center+.25, 2.17, -.317, -.295)
            at('gilt swag on lower door panel', center, .651, -.119, -.111)
    for x in (-7.49,-6.59,-2.85,-.873,.67,2.87,6.53,7.46):
        at('upper cornice forward edge',x,16.52,2.212,2.229)
        at('granite cornice forward edge',x,5.255,2.252,2.269)
    return out

def sample(blob):
    mesh=trimesh.load(BytesIO(blob),file_type='glb',force='mesh',process=False)
    tri=mesh.triangles[:,:,[0,2,1]]*[1,-1,1]
    t=tri[:,:,[0,2]]
    a,b,c=t.transpose(1,0,2);ab=b-a;ac=c-a
    den=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0];valid=np.abs(den)>1e-9
    results=[]
    for title,x,z,low,high in probes():
        delta=np.array([x,z])-a
        u=np.zeros_like(den);v=np.zeros_like(den)
        u[valid]=(delta[valid,0]*ac[valid,1]-delta[valid,1]*ac[valid,0])/den[valid]
        v[valid]=(ab[valid,0]*delta[valid,1]-ab[valid,1]*delta[valid,0])/den[valid]
        hit=valid&(u>=-.000001)&(v>=-.000001)&((u+v)<=1.000001)
        d=-tri[:,:,1]
        first=(d[hit,0]+u[hit]*(d[hit,1]-d[hit,0])+v[hit]*(d[hit,2]-d[hit,0])).max(initial=-100)
        results.append(dict(observation=title,x=x,z=z,near_depth=float(first),allow=[low,high],passed=bool(low<=first<=high)))
    return results

if __name__=='__main__':
    if len(sys.argv)>1:
        for arg in sys.argv[1:]:
            res=sample(Path(arg).read_bytes())
            print(arg,len(res),[(r['observation'],r['x'],r['z'],round(r['near_depth'],3)) for r in res if not r['passed']])
    else:
        audit=Path(__file__).resolve().parent;project=audit.parents[2];assets=project/'assets/models/candidates'/ID
        manifest=json.loads((assets/'manifest.json').read_bytes());checker=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs';codec=project/'vendor/meshopt_decoder.module.js';results={}
        with TemporaryDirectory() as tmp:
            for role in ('raw','full','lod'):
                item=manifest['assets'][role];path=assets/item['file']
                assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
                if role!='raw':
                    decoded=Path(tmp)/(role+'.glb')
                    subprocess.run(['node',checker,path,decoded,codec],check=True)
                    path=decoded
                hits=sample(path.read_bytes());assert all(r['passed'] for r in hits),[r for r in hits if not r['passed']]
                results[role]=dict(sha256=item['sha256'],triangles=item['triangles'],samples=hits)
        (audit/'surface-checks.json').write_text(json.dumps(dict(id=ID,total_checks=sum(len(r['samples']) for r in results.values()),variants=results),indent=2)+'\n')
