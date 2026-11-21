from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-kangping-1-hipped-tile-eaves'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def ray(label, origin, direction, maximum, materials, near, far):
        hit=scene.ray(origin,direction,maximum)
        passed=hit is None if not materials else bool(hit and hit['material'] in materials and near<=hit['distance_m']<=far)
        samples.append(dict(check=label,origin=origin,direction=direction,maximum_m=maximum,allowed_materials=materials,expected_range_m=[near,far],hit=hit,passed=passed))
    for side in (0,1):
        def xyz(across,up,height):
            return [across,up,height] if side==0 else [up,across,height]
        for i in range(2,16):
            for y in (.082, .16 if i==2 else .237):
                x=(i+.28)*.192;surface=1.08+.43*y+.020+.048
                ray('standing curved cover tile',xyz(x,y,3),[0,0,-1],3,['russet cover','weathered cover'],3-surface-.018,3-surface+.020)
                x=(i+.78)*.192;surface=1.08+.43*y
                ray('concave pan between covers',xyz(x,y,3),[0,0,-1],3,['red clay pan'],3-surface-.025,3-surface+.014)
        ray('hip cap overlaps the first field tile',xyz(.43776,.237,3),[0,0,-1],3,['red hip cap'],1.655,1.705)
        for x in (.72,1.4,2.2,2.83):
            ray('outside dark gutter',xyz(x,-1.,1.04),xyz(0,1,0),2,['shadowed gutter'],.95,1.02)
            ray('brown fascia below gutter',xyz(x,-1.,.971),xyz(0,1,0),2,['brown fascia'],1.015,1.05)
            ray('visible sand render below fascia',xyz(x,-1.,.84),xyz(0,1,0),2,['sand render'],1.29,1.31)
        ray('outside corner remains free',xyz(.95,-.19,2),[0,0,-1],2,[],0,0)
    for d in (.07,.16,.25,.34,.49,.62,.71,.84,.99,1.12,1.21):
        surface=1.08+.43*d+.07+.142
        ray('rounded hip cap above both roof slopes',[d,d,3],[0,0,-1],3,['red hip cap'],3-surface-.022,3-surface+.022)
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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
