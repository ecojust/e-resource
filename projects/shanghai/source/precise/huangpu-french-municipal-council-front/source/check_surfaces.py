"""Probe the retained street shell, open window reveals, dormers, stair and present doorway."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-french-municipal-council-front'
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
    for x,y in [(-24.525,.15),(-16.30,1.32),(-8.70,1.32),(8.70,1.32),(16.30,1.32),(24.525,.15)]:
        for dx in [-1.12,.14,1.12]:
            for z in [2.08,9.17]:probe('separate tall upper and lower three-light casements',[x+dx,-2,z],[0,1,0],'shop and office glass',2+y+.34)
        probe('street-facing awning valance',[x+.22,-2,5.25],[0,1,0],'wine red canvas',2+y-.93)
    for x in [-2.75,2.75]:probe('narrow opening flanking the door',[x+.11,-2,2.38],[0,1,0],'shop and office glass',2.34)
    for x in [-1.72,.21,1.72]:probe('upper central three-light window',[x,-2,9.53],[0,1,0],'shop and office glass',2.34)
    probe('recessed central door glass',[.58,-2,2.01],[0,1,0],'shop and office glass',2.81)
    probe('bronze spoke within stone arch',[.57,-2,5.55],[0,1,0],'dark bronze casements',2.647)
    probe('semicircular glazed fanlight between spokes',[.82,-2,5.44],[0,1,0],'shop and office glass',2.81)
    for x in [-1.91,1.91]:probe('pale stone jamb outside the door',[x,-2,2.14],[0,1,0],'pale stone door surround',1.735)
    probe('pale plaque margin',[3.28,-2,7.20],[0,1,0],'pale stone door surround',2-.245)
    for mid in [-12.5,12.5]:
        for off in [-4.44,0,4.44]:
            probe('glazed opening through a roof dormer',[mid+off+.23,-2,12.91],[0,1,0],'shop and office glass',5.02)
        y=3.91;z=11.72+(y-(1.32-.14))*2.30/4.10
        probe('sloping clay tile between dormers',[mid+2.1,y,22],[0,0,-1],'weathered clay roof',22-z)
    for x,z in [(0,14.16),(-24.5,13.51),(24.5,13.51)]:probe('flat roof behind raised pavilion coping',[x,4.92,22],[0,0,-1],'roof flashing',22-z)
    for n in range(4):
        y=-1.42+n*.355+.19;probe('granite tread toward the public door',[.37,y,3],[0,0,-1],'street entrance granite',3-(n+1)*.113)
    for x,y in [(-31,2),(31,2),(0,-2.7),(0,9.42),(2,18)]:probe('street, adjacent shop or retained rear roof',[x,y,22],[0,0,-1],None,None)
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
