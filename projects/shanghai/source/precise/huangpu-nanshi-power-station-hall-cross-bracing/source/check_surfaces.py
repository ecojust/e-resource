from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-nanshi-power-station-hall-cross-bracing'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene, role):
    import runpy, math
    g=runpy.run_path(str(SOURCE/'hall_braces.py'));s=g['SURVEY'];rows=[]
    def check(name,x,z,y,expected):
        hit=scene.ray([x,-1,z],[0,1,0],2.2)
        rows.append(dict(feature=name,local_xz_m=[x,z],expected_depth=y,actual=hit,passed=bool(hit and hit['material']==expected and abs(hit['distance_m']-1-y)<.002)))
    for i,(name,points)in enumerate(s['visible_braces_crop_px'].items()):
        a,b=map(g['xz'],points)
        for t in [.12,.17,.22,.27,.32,.37,.67,.72,.77,.82]:
            x,z=(a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t)
            # Project the sample onto the other photographed diagonal in this storey.
            # A ray through its measured width first hits its outer face or its rolled lip.
            depth = [.04,-.045,.04,-.045][i]
            if i in (0,2):
                front_points = list(s['visible_braces_crop_px'].values())[i+1]
                start, end = map(g['xz'],front_points)
                dx, dz = end[0]-start[0], end[1]-start[1]
                length = math.hypot(dx,dz)
                along = ((x-start[0])*dx+(z-start[1])*dz)/length
                distance = abs((x-start[0])*dz-(z-start[1])*dx)/length
                half_width = [.142,.123][i//2]
                if 0 <= along <= length and distance < half_width:
                    depth = -.045
                    if role != 'lod' and abs(distance-(half_width-.007)) < .006:
                        depth -= .006
            check(name,x,z,depth,'steel brace')
    for name,quad in s['pier_stripes_crop_px'].items():
        # Each painted band is coplanar on its own column face.
        center=[sum(p[j] for p in quad)/4 for j in (0,1)]
        for p in quad:
            x,z=g['xz']([p[j]*.21+center[j]*.79 for j in (0,1)])
            check(name,x,z,-.165,'dark pier stripe')
    for name,pts in [('mid-storey',[(122,347),(353,300)]),('lower',[(126,610),(354,615)])]:
        z=sum(g['xz'](p)[1] for p in pts)/2
        for x in [-1.7,-1.36,-1.12,-.80,-.42,.0,.36,.72,1.12,1.48]:
            check(name+' upper flange',x,z+.132,-.075,'steel flange')
            check(name+' lower flange',x,z-.142,-.075,'steel flange')
    return dict(samples=rows,passed=all(p['passed'] for p in rows))

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
