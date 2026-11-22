from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-yongxing-telephone-exchange-arched-bay'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    import math
    rows=[]
    def shot(label,x,z,mat,front,tolerance=.014):
        result=scene.ray([x,-.72,z],[0,1,0],1.44)
        distance=.72+.058*x*x+front
        ok=result is not None and result['material']in mat and abs(result['distance_m']-distance)<tolerance
        rows.append(dict(feature=label,x=x,z=z,materials=sorted(mat),expected=distance,hit=result,passed=ok))
    for t in (.035,.071,.119,.174,.238,.31,.399,.457,.534,.613,.699,.753,.813,.866,.923,.969):
        for radius,mat,depth in [(1.40,'arch intrados',-.032),(1.475,'shadow course',-.063),(1.533,'dress stone',-.116),(1.64,'dress stone',-.191)]:
            a=t*math.pi
            shot('curved concentric archivolt',radius*math.cos(a),1.87+radius*math.sin(a),{mat},depth)
    for side in (-1,1):
        for x in (.50,.70,.96,1.18):
            for z in (.21,.489,.766,1.018,1.353,1.625):
                shot('recessed ashlar alongside the single casement',side*x,z,{'recess wall'},.009)
        for x in (.12,.24,.326):
            for z in (.24,.58,1.12,1.72):
                shot('glass behind the projecting jamb',side*x,z,{'glass'},.195)
        for z in (.43,.865,1.322,1.50):
            shot('steel horizontal on lower window',side*.21,z,{'casement steel'},.15)
    for x in (-1.00,0,.98):
        for z in (4.07,4.37,4.66,4.97,5.26):
            shot('three separate recessed upper lights',x,z,{'glass'},.181)
        for z in (4.20,4.53,4.80,5.12):
            shot('upper steel glazing bars',x,z,{'casement steel'},.13)
    for x in (-1.52,-.51,.54,1.52):
        for z in (4.08,4.38,4.79,5.17):
            shot('masonry between upper openings',x,z,{'upper facade'},-.098)
    for x in (-1.48,-1.01,-.64,-.18,.21,.68,1.14,1.59):
        shot('continuous intermediate cornice',x,3.86,{'stone sill'},-.247)
    return dict(samples=rows,passed=all(q['passed']for q in rows))

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
