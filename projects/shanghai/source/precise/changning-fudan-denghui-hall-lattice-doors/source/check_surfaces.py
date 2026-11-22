from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-fudan-denghui-hall-lattice-doors'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from lattice_doors import CENTRES,LIGHT_BOTTOM,CELL_X,CELL_Z,LIGHT_WIDTH
    rows=[]
    def ray(name,x,z,mat,y=0):
        hit=scene.ray([x,-.55,z],[0,1,0],.92)
        passed=(hit is None) if mat is None else (hit and hit['material']==mat and abs(hit['distance_m']-.55-y)<.002)
        rows.append(dict(label=name,origin=[x,-.55,z],direction=[0,1,0],expected_material=mat,expected_distance_m=.55+y if mat else None,observed=hit,passed=bool(passed)))
    for c in CENTRES:
        x0=c-LIGHT_WIDTH/2
        for row in range(1,13):
            z=LIGHT_BOTTOM+row*CELL_Z
            for col in (1,2,4):
                x=x0+col*CELL_X
                ray('continuous timber crossbar',x+.022,z,'openwork dark wood',.022)
                ray('vertical square-lattice bar',x,z+.031,'openwork dark wood',.027)
                ray('clear opening through upper leaf',x+.019,z+.033,None)
            if row%2==0:
                ray('half-height return',x0+CELL_X*.50,z+.8*CELL_Z,'openwork dark wood',.030)
        for x in (-.18,-.09,.08,.175):
            for z in (.329,.524,.798,.964):ray('recessed solid lower panel',c+x,z,'panel field',.031)
            for z in (.195,1.12,2.795):ray('closed horizontal rail',c+x,z,'red lacquer',.001)
        for x in (-.265,.265):
            for z in (.423,.903,1.47,2.08,2.74):ray('red outer stile',c+x,z,'red lacquer',.0)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)

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
