from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-wuyi-100-garden-eaves-brackets'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def shoot(arm,s,r,z,mat,dist,label):
        ori=[s,-r,z] if arm=='front'else[r,s,z];hit=scene.ray(ori,[0,0,1],1.6)
        good=bool(hit and hit['material']==mat and abs(hit['distance_m']-dist)<.005)
        rows.append(dict(feature=label,origin=ori,material=mat,expected_distance=dist,hit=hit,passed=good))
    for arm,s in [('front',-1.56),('side',.62),('side',1.91)]:
        for offs in (-.078,.015,.07):
            for r in (.28,.335,.393):shoot(arm,s+offs,r,0,'concealed vent shade',.745,'three real rectangular recesses in the light soffit')
            for r in (.224,.461):shoot(arm,s+offs,r,0,'painted soffit',.70,'underside immediately on both sides of the opening')
        for ds in (-.165,.17):
            for r in (.29,.375):shoot(arm,s+ds,r,0,'painted soffit',.70,'solid soffit past each end of vent')
    # Independent checks of the visible curved lower edge of the four plaster braces.
    samples=[(.036,.160),(.069,.261),(.120,.394),(.190,.503),(.281,.586),(.397,.639)]
    for arm,s in [('front',-1.35),('front',-.105),('side',1.38),('side',2.18)]:
        for r,near in samples:
            ori=[s,-r,0]if arm=='front'else[r,s,0];hit=scene.ray(ori,[0,0,1],1.1)
            valid=bool(hit and hit['material']=='cream bracket' and abs(hit['distance_m']-near)<.052)
            rows.append(dict(feature='curve under each measured outrigger',origin=ori,expected_height_range=[near-.052,near+.052],hit=hit,passed=valid))
    for arm,s in [('front',-2.02),('front',-.66),('side',.22),('side',2.34)]:
        for z in (.773,.810,.839):
            ori=[s,-1,z]if arm=='front'else[1,s,z];direct=[0,1,0]if arm=='front'else[-1,0,0]
            hit=scene.ray(ori,direct,1.5);ok=bool(hit and hit['material']=='wine fascia' and abs(hit['distance_m']-.38)<.005)
            rows.append(dict(feature='exposed dark fascia below gutter',origin=ori,direction=direct,hit=hit,passed=ok))
    return dict(samples=rows,passed=all(r['passed']for r in rows))

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
