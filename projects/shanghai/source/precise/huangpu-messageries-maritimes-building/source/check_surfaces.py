"""Probe the river casements, side windows, gallery entrance, terraces and free ground."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-messageries-maritimes-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    import numpy as np
    rows=[]
    def probe(label,origin,direction,material,depth,tol=.043):
        hit=scene.ray(list(origin),list(direction),50)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-depth)<tol)
        rows.append(dict(label=label,origin=list(origin),direction=list(direction),reference_depth_m=depth,
                         expected_material=material,hit=hit,passed=ok))
    # The reference rays use photo-identified axes, floor sequence and observed material transitions.
    for level in range(10):
        sill=7.95+3.52*level
        for bay in (-4.94,0,4.94):
            for dx in (-1.14,0,1.14):
                probe('three triplets in the high central mass',[bay+dx+.095,-2,sill+.84],[0,1,0],'smoked archive glazing',2.355)
                if level>0:probe('grey-blue spandrel in each vertical run',[bay+dx+.07,-2,sill-.68],[0,1,0],'grey blue spandrel panel',2.019)
        if level<8:
            for wing in [-10.57,10.57]:
                for dx in [-.59,.59]:
                    probe('double windows in the lower outer wings',[wing+dx+.14,-2,sill+.94],[0,1,0],'smoked archive glazing',2.355)
    probe('deep archive street entrance',[.23,-2,2.79],[0,1,0],'smoked archive glazing',3.02)
    for x in [-5.08,5.08]:probe('flanking archive sidelights',[x+.18,-2,3.38],[0,1,0],'smoked archive glazing',2.45)
    for item in json.loads((SOURCE/'sign-probes.json').read_bytes()):
        probe('unobstructed gilded '+item['character']+' '+item['zone'],[item['x'],-2,item['z']],[0,1,0],'gilded archive name',2.06-.423,.018)
    for i in range(5):
        # The outer gaps cross the two raised granite jambs at their top edge.
        depth=2.06-(.465 if i in [0,4] else .32)
        probe('visible granite spacing between archive characters',[(i-2)*1.51,-2,6.80],[0,1,0],'charcoal polished granite',depth)
    for x in [-7.58,-2.87,2.87,7.58]:probe('granite name-bay pier',[x,-2,3.15],[0,1,0],'charcoal polished granite',2.06-.465)
    for x in [-10.63,10.63]:probe('pale granite river plinth',[x,-2,.81],[0,1,0],'pale granite plinth',2.06-.09)
    for x,y,z in [(4,3,42.87),(10,6,39.32),(-10,7,39.32),(10,1.4,35.79),(-11,1.6,35.79),(0,24,35.79),(-7,32,35.79)]:
        probe('flat roof at a documented stage of the stepped silhouette',[x,y,51],[0,0,-1],'asphalt roof terrace',51-z)
    for x,y in [(-15,.1),(15,2),(2,-1),(15,24),(0,39)]:probe('street, independent neighbour or space outside the parcel',[x,y,51],[0,0,-1],None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(x['passed']for x in rows))


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
