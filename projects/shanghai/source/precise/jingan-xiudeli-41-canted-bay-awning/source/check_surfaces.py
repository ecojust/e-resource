from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-xiudeli-41-canted-bay-awning'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import hypot
    source=runpy.run_path(str(SOURCE/'canted_bay.py'));out=[]
    def cast(label,part,s,z,d,mat):
        origin=source['loc'](part,s,-.65,z);end=source['loc'](part,s,.35,z)
        direction=[end[i]-origin[i]for i in range(3)];hit=scene.ray(origin,direction,1.5)
        out.append(dict(feature=label,facet=part,longitudinal_m=s,z=z,hit=hit,expected_material=mat,passed=hit is not None and hit['material']==mat and abs(hit['distance_m']-(d+.65))<.006))
    for part,left,right,lights in [(0,.32,2.12,4),(1,.15,.77,1)]:
        width=(right-left-.072)/lights
        for i in range(lights):
            x0=left+.036+width*i
            for z in (.81,.97,1.35,1.64,1.87):
                row=0 if z<1.103 else 1
                for off in (.27,.72):
                    cast('red sash recessed glass',part,x0+off*width,z,.204,'shadow glass'if part or (i+row)%5==0 else 'sky glass')
                cast('box-section red upright',part,x0+.015,z,.151,'red timber')
            cast('deep horizontal transom',part,x0+width/2,1.136,.153,'red timber')
        for t in (.18,.34,.49,.66,.82):
            for z,d,mat in [(.622,-.108,'projecting grey sill'),(2.473,-.083,'upper belt shadow'),(2.558,-.127,'granite trim')]:
                cast('continuous angular belt',part,t*source['width'](part),z,d,mat)
    return dict(samples=out,passed=all(v['passed']for v in out))
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
