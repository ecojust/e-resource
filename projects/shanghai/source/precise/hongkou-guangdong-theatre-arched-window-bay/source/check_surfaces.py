from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-guangdong-theatre-arched-window-bay'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import cos,pi,sin
    items=[]
    def probe(name,x,z,materials,depth,tolerance=.012):
        pos=[x,-1.,z];direction=[0,1,0];hit=scene.ray(pos,direction,1.6)
        passed=hit is not None and hit['material'] in materials and abs(hit['distance_m']-(depth+1))<tolerance
        items.append(dict(check=name,origin=pos,direction=direction,expected=materials,expected_front=depth,hit=hit,passed=bool(passed)))
    for i in range(24):
        t=pi*(i+.5)/24
        for r,mat,y in ((.702,'stone highlight',-.065),(.487,'cast stone',-.045),(.434,'steel',.037)):
            probe('Continuous moulding over upper light',r*cos(t),6.82+(r+.02)*sin(t),[mat],y)
    for sign in (-1,1):
        for z in (.20,.55,1.54,2.76,3.93,4.94,6.26):
            probe('Continuous outer course at jamb',sign*.70,z,['stone highlight'],-.065)
            probe('Inner pale return beside the sash',sign*.493,z,['cast stone'],-.045)
        for z,mat in ((.78,'lower reflection'),(1.30,'lower reflection'),(3.38,'slate reflection'),(4.0,'slate reflection'),(6.0,'slate reflection'),(6.49,'slate reflection')):
            probe('Recessed casement glass',sign*.27,z,[mat],.146)
        for z in (2.03,2.52,4.89,5.44):probe('Pale fields of the spandrels',sign*.338,z,['panel field'],.023)
        for z in (6.99,7.045):probe('Glazed fanlight behind the arch',sign*.212,z,['shadow glass'],.146)
    for z in (.8,1.28,3.47,4.02,6.01,6.42):probe('Forward steel meeting stile',0,z,['steel'],.039)
    for z in (.36,3.03,5.73):probe('Projecting pale sill',.25,z,['cast stone'],-.081)
    for x in (-1.84,-1.17,-.32,.63,1.45):
        for z,mat,y in ((8.756,'cast stone',-.075),(8.85,'stone highlight',-.15),(9.21,'coping',-.205),(9.277,'coping edge',-.245)):
            probe('Four physical steps of the horizontal cornice',x,z,[mat],y)
    return {'passed':all(row['passed'] for row in items),'samples':items}


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
