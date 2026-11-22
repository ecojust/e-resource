from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-soong-hongqiao-four-chimney-shafts'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from four_pots import POTS
    rows=[]
    def ray(label,x,z,mat,y,tolerance=.002):
        hit=scene.ray([x,-.80,z],[0,1,0],1.35)
        good=(hit is None) if mat is None else bool(hit and hit['material'] in mat and abs(hit['distance_m']-.80-y)<tolerance)
        rows.append(dict(label=label,origin=[x,-.8,z],direction=[0,1,0],expected_material=mat,expected_distance_m=.80+y if mat else None,observed=hit,passed=good))
    for x in (-.582,-.451,-.314,-.214,-.055,.089,.229,.396,.502,.578):
        for z in (.077,.346,.624,.902,1.16):
            ray('stippled lower shaft',x,z,['coarse render','darker roughcast','pale stone granule'],-.250,.005)
        ray('projecting shoulder underside',x,1.232,['smoked shoulder'],-.303)
        for z in (1.27,1.304,1.334):
            y=-.303+(z-1.251)*(.303-.238)/(.102)
            ray('sloped shoulder face',x,z,['exposed edge'],y)
    for i,c in enumerate(POTS):
        stem=(['warm clay shaft'] if i in (1,3)else['clay shaft'])+['charcoal weathering','brown weathering','umber clay','buff clay','dusty clay']
        for dx in (-.079,0,.075):
            for z in (1.39,1.57,1.82):ray('long flat stem face',c+dx,z,stem,-.217)
            ray('broad band',c+dx,2.053,['raised cap course'],-.247)
            ray('setback joint',c+dx,2.106,['smoked shoulder'],-.224)
            ray('tapered crown',c+dx,2.203,['upper cap'],-.247+(2.203-2.146)*.008/.101)
        for s in (-1,1):ray('cut corner of the stem',c+s*.128,1.69,stem,-.217+(.128-(.145-.053)))
        if i<3:
            for z in (1.48,1.755,2.049):ray('open seam between next two stems',c+.155,z,None,0)
    return dict(passed=all(v['passed']for v in rows),samples=rows)

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
