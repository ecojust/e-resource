from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='pudong-chuansha-yiyuan-no88-stone-inscription'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene, role):
    from plaque import SCALE, TRACES, point
    result=[]
    def shoot(u,v,material,low,high,feature):
        x,_,z=point(u,v,0)
        hit=scene.ray((x,-1,z),(0,1,0),1.5)
        passed=bool(hit and hit['material']==material and low<=hit['distance_m']<=high)
        result.append(dict(feature=feature,origin=[x,-1,z],direction=[0,1,0],expected_material=material,depth_interval=[low,high],hit=hit,passed=passed))
    for glyph,strokes in TRACES.items():
        for k,(width,line) in enumerate(strokes):
            for i in sorted(set([1,len(line)//2])):
                a=line[i-1];c=line[i]
                shoot((a[0]+c[0])/2,(a[1]+c[1])/2,'worn stone lettering',.948,.9605,f'{glyph} stroke {k+1}')
    for inset,material,low,high in [(7,'outer limestone lip',.924,.929),(17,'stone bevel',.940,.950),(22,'inner stone bead',.935,.943),(30,'stone cove',.956,.964),(47,'buff limestone face',.958,.964)]:
        for t in [92,190,367,502]:
            for u,v in [(t,inset),(t,192-inset)]:
                if (u,v)==(92,145):
                    shoot(u,v,'worn stone lettering',.950,.958,'left descending brush at the lower field edge')
                    shoot(83,160,'stone cove',.958,.964,'horizontal cove below that brush')
                    shoot(68,139,'buff limestone face',.958,.964,'plain field left of the brush')
                else:shoot(u,v,material,low,high,'moulding or plain field')
        for v in [71,123]:
            for u in [inset,600-inset]:shoot(u,v,material,low,high,'vertical moulding')
    return dict(samples=result,passed=all(i['passed'] for i in result))

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
