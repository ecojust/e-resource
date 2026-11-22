from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='pudong-qingxi-teahouse-courtyard-window-screens'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def ray(x,z,material,dmin,dmax,feature):
        o=[x,-1,z];hit=scene.ray(o,[0,1,0],3)
        samples.append(dict(feature=feature,origin=o,material_choices=material,gap_interval_m=[dmin,dmax],hit=hit,
                            passed=bool(hit and hit['material'] in material and dmin-.0005<=hit['distance_m']<=dmax+.0005)))
    glass=['amber glass','honey glass','reflected amber','smoked glass','slate glass','bluish glass']
    for cx in [-.555,0,.555]:
        for z in [.047,.451,.845]:
            for dx in [-.11,.11]:ray(cx+dx,z,glass,1.033,1.036,'paired narrow transom panes')
        for z in [.165,.327,.562,.724]:
            for dx in [-.157,.161]:ray(cx+dx,z,glass,1.033,1.036,'short panes either side of the uninterrupted centre light')
            ray(cx,z,glass,1.033,1.036,'tall central glass light')
        for z in [.248,.650]:
            for dx in [-.161,.159]:ray(cx+dx,z,['varnished wood'],1.006,1.006,'lateral short tie')
            ray(cx,z,glass,1.033,1.036,'the lateral tie stops at the edge of the centre light')
        for z in [.097,.401,.502,.798]:ray(cx,z,['varnished wood'],.998,.998,'full width horizontal rail')
        for z in [.18,.31,.59,.72]:
            for dx in [-.1015,.097]:ray(cx+dx,z,['varnished wood'],1.004,1.004,'two long muntins around tall glass')
        for dx in [-.242,.241]:ray(cx+dx,.348,['shadowed wood'],.986,.986,'sash stile')
    for x in [-.2775,.2775]:
        for z in [.17,.4,.65,.81]:ray(x,z,['mullion sides'],1.003,1.003,'recessed timber between leaves')
    return dict(samples=samples,passed=all(v['passed'] for v in samples))

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
