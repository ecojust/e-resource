from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-shandao-hall-court-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def cast(kind,x,z,options,lo,hi):
        hit=scene.ray([x,-.5,z],[0,1,0],1.11)
        ok=hit is not None and hit['material'] in options and lo<=hit['distance_m']<=hi
        rows.append(dict(feature=kind,x=x,z=z,expected_material=sorted(options),depth_interval_m=[lo,hi],hit=hit,passed=ok))
    for side in (-1,1):
        for course in range(8):
            z=.14+(course+.5)*.24
            for fraction in (.23,.51,.84):
                width=.122 if course%2 else .235
                cast('side quoin',side*(.74+fraction*width),z,{'ochre stone','pale brown stone'},.471,.475)
            if course%2:
                cast('dark aggregate beyond short quoin',side*.948,z,{'dark aggregate','slate pebbles','olive pebbles','light pebbles'},.487,.502)
        c=side*.366
        for z in (.292,.56,.775,1.12,1.34):
            cast('straight centre of each grille',c,z,{'wrought iron'},.551,.563)
            cast('sash side stiles',side*.717,z,{'sash'},.546,.550)
            for dx in (-.260,.263):cast('glass visible through ironwork',c+dx,z,{'lower glass'},.649,.653)
        for i in range(7):
            z=.3+i*.167
            cast('outer forged frame',c+.315,z,{'wrought iron'},.553,.565)
        for i in range(9):cast('projecting sill',side*(.08+.118*i),.095,{'sill'},.447,.451)
    for i in range(13):cast('transom',-.68+.112*i,1.49,{'sash'},.546,.550)
    for i in range(7):cast('head rail',-.62+.207*i,2.026,{'sash'},.546,.550)
    for x in (-.34,0,.34):
        cast('transom uprights',x,1.75,{'wrought iron'},.571,.581)
        cast('upper glass beside uprights',x+.025,1.75,{'top glass'},.649,.653)
    return dict(samples=rows,passed=all(x['passed'] for x in rows))

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
