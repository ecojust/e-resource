from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-fan-garden-no8-three-arched-windows'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from three_arches import CENTERS,eyebrow_top
    from math import sqrt
    rows=[]
    def ray(name,x,z,mat,y):
        hit=scene.ray([x,-.60,z],[0,1,0],3.7)
        rows.append(dict(label=name,origin=[x,-.60,z],direction=[0,1,0],expected_material=mat,expected_distance_m=.6+y,observed=hit,passed=bool(hit and hit['material']==mat and abs(hit['distance_m']-.60-y)<.002)))
    for c in CENTERS:
        for dx in (-.43,-.30,-.09,.09,.31,.43):
            for z in (1.008,1.34,1.69,1.82):
                ray('glass behind arch',c+dx,z,'glazing',.144)
            ray('timber transom',c+dx,1.549,'timber sash',.080)
            ray('lower panel',c+dx,.52,'light render',-.045)
            ray('visible panel edge',c+dx,.287,'stone trim',-.038)
        for dx in (-.206,.205):
            for z in (1.06,1.46,1.87):ray('timber stile',c+dx,z,'timber sash',.074)
        for dx in (-.30,-.15,0,.16,.31):
            # Sample midway between the two curved boundaries, not on a segment edge.
            mid=(sqrt(.570**2-dx**2)+sqrt(.612**2-dx**2))/2
            ray('projecting arch rim',c+dx,1.57+mid,'stone trim',-.033)
    for x in (-2.01,-1.13,-.413,.26,.918,1.88):
        ray('eaves band',x,2.41,'stone trim',-.082)
        ray('sill',x,.076,'aged coping',-.088)
    for x in (-.171,-.068,.065,.195):
        ray('small roof window',x,3.033,'glazing',.356)
    for x in (-.144,0,.143):
        ray('small window mullion',x,3.059,'dormer frame',.315)
    for x in (-.57,-.43,-.32,0,.33,.44,.56):
        ray('dormer eyebrow coping',x,eyebrow_top(x)+.016,'aged coping',.246)
    return dict(passed=all(i['passed'] for i in rows),samples=rows)

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
