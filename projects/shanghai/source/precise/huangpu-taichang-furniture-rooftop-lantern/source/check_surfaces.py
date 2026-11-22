from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-taichang-furniture-rooftop-lantern'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import sin,cos,pi,sqrt
    hits=[]
    def cast(feature,t,r,z,dist,mat=None,tol=.010):
        origin=[r*sin(t),-r*cos(t),z];direction=[-sin(t),cos(t),0]
        value=scene.ray(origin,direction,dist+.14 if mat else dist)
        hits.append(dict(feature=feature,origin=origin,direction=direction,expected=mat,expected_distance=dist,observed=value,passed=bool(value and value['material']==mat and abs(value['distance_m']-dist)<tol) if mat else value is None))
    for j in [-2,-1,0,1,2]:
        t=j*pi/4
        for z in [1.08,1.35,1.65,1.86]:
            face=.84+.08-(z-.878)*(.006/(1.98-.878));cast('street-facing upright',t,1.37,z,1.37-face,'pale pier')
        for z,r,material in [(.838,.953,'upper bed'),(2.08,.952,'relief bevel')]:
            cast('base or capital',t,1.37,z,1.37-r,material)
    for j in [-2,-1,0,1]:
        t=(j+.5)*pi/4
        for z in [.94,1.26,1.59,1.89]:cast('open space between piers',t,1.49,z,1.38)
    # A cast normal to an octagonal flat sees the apothem of each moulding.
    for j in range(8):
        t=(j+.5)*pi/4
        for z,r,mat in [(.626,1.007,'cornice lip'),(.737,.969,'plain base'),(2.224,.978,'shaded joint'),(2.31,1.052,'upper bed'),(2.392,1.044,'upper bed')]:
            cast('polygonal ledge',t,1.49,z,1.49-r*cos(pi/8),mat)
    for j in range(12):
        a=2*pi*j/12
        for z in [2.51,2.65,2.79]:
            rr=.925*sqrt(1-((z-2.422)/.545)**2)
            cast('domed shell',a,1.35,z,1.35-rr,'dark dome',.019)
    return dict(samples=hits,passed=all(v['passed']for v in hits))

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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
