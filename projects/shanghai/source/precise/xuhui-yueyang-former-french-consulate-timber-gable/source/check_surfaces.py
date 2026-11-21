from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-yueyang-former-french-consulate-timber-gable'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def ray(label,x,z,materials,low,high):
        origin=[x,-1.,z];direction=[0,1,0]
        hit=scene.ray(origin,direction,1.5)
        ok=hit is None if not materials else bool(hit and hit['material'] in materials and low<=hit['distance_m']<=high)
        samples.append(dict(check=label,origin=origin,direction=direction,max_length=1.5,expected_materials=materials,expected_distance=[low,high],hit=hit,passed=ok))
    for cx in (-1.03,1.03):
        xa=cx-.46+.064;xb=cx+.46-.064;za=.275+.066;zb=1.77-.066
        for col in range(4):
            for row in range(6):
                ray('Recessed individual pane',xa+(xb-xa)*(col+.5)/4,za+(zb-za)*(row+.5)/6,['smoky glazing','green grey glazing'],1.117,1.123)
        for j in range(1,4):
            for f in (.12,.35,.72):
                ray('Upright muntin',xa+(xb-xa)*j/4,za+(zb-za)*f,['window wood'],1.004,1.01)
        for j in range(1,6):
            ray('Transverse muntin',cx+.12,za+(zb-za)*j/6,['window wood'],1.017,1.023)
        for x in (cx-.424,cx+.424):
            for z in (.52,.95,1.54):ray('Jamb in front of glazing',x,z,['window wood'],.931,.94)
        ray('Sill nosing',cx,.250,['painted stone sill'],.838,.855)
    from math import asin,cos
    for j in range(9):
        x=-2+.50*j
        for z in (1.90,2.07,2.18):
            rise=(z-1.839)/.418
            front=1-.008-.218*(1-cos(asin(rise)))
            ray('Curved timber over plaster',x,z,['old dark framing'],front-.056,front-.03)
        if j<8:ray('Cove between curved ribs',x+.25,2.07,['coved soffit'],.939,.969)
    for x in (-1.06,-.596,0,.596,1.06):
        for z in (2.47,2.55):ray('Timber upright',x,z,['old dark framing'],.773,.79)
    for x in (-1.53,-.783,.24,.78,1.51):
        ray('White triangular infill',x,2.47,['cream roughcast'],.819,.828)
    for x in (-2.5,2.5):ray('Outside the retained wall section',x,1.12,[],0,0)
    return dict(samples=samples,passed=all(s['passed'] for s in samples))


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
