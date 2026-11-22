from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-jialu-garden-wall-floral-pediment'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    import numpy as np
    source=runpy.run_path(str(SOURCE/'garden_pediment.py'))
    data,tone=source['sample_data'](role=='lod');nz,nx=data.shape
    u=np.linspace(30,701,nx);v=np.linspace(19,418,nz);samples=[]
    for i in range(4,nx-3,7 if role=='lod' else 15):
        for j in range(4,nz-3,5 if role=='lod' else 10):
            x=(u[i]+u[i+1])/2;y=(v[j]+v[j+1])/2
            if not source['verge'](x)+6<y<source['sill'](x)-5:continue
            cx,_,cz=source['position'](x,y,0)
            hit=scene.ray([cx,-.5,cz],[0,1,0],.9)
            # The raster cells form two triangles. Their shared diagonal crosses the centre.
            expected=.499-float((data[j+1,i]+data[j,i+1])/2)
            expected_alt=.499-float((data[j,i]+data[j+1,i+1])/2)
            delta=None if not hit else min(abs(hit['distance_m']-x)for x in (expected,expected_alt))
            samples.append(dict(point_uv=[x,y],hit=hit,front_residual=delta,passed=hit is not None and hit['material'].startswith('cast-stone fleck tone') and delta<.002))
    return dict(samples=samples,passed=all(s['passed']for s in samples))
def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
