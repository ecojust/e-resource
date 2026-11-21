from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-jingu-village-shaoxing-gatepost'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




"""Test the carved address pier, the free passage on its left and the adjoining wall."""
def test(scene):
    import sys
    common = PROJECT / 'source/precise/hongkou-general-post-office/source/common'
    sys.path.insert(0, str(common))
    from inscribed_pier import STROKES
    rows=[]
    def sample(name,x,z,material=None,depth=None,reach=1.5):
        hit=scene.ray([x,-.65,z],[0,1,0],reach)
        if material is None: ok=hit is None
        else:ok=hit is not None and hit['material'] in material and abs(hit['distance_m']-(.65-depth))<=.005
        rows.append(dict(name=name,origin=[x,-.65,z],direction=[0,1,0],expected_material=material,front_depth_m=depth,hit=hit,passed=ok))
    for x in [-.86,-.59,-.45]:
        for z in [.05,.20,.405,.82,1.06,1.6,1.9,2.065]:
            sample('Free passage remains open',x,z)
    for x in [-.30,-.17,.15,.30]:
        sample('Street plinth projects',x,.095,['weathered stone base'],.055)
        sample('Upper plinth shoulders',x,.246,['stepped stone edging'],.04)
        sample('Set-back below small cap',x,2.013,['stepped stone edging'],.0105)
    for x in [-.28,.28]:
        for z in [.44,.776,1.144,1.47,1.79]:
            sample('Separate dressed stone courses',x,z,['grey dressed stone'],.013)
        for z in [.6935,1.0325,1.3535,1.6515]:
            sample('Masonry joints recede between the courses',x,z,['recessed stone joint'],.01)
    for x in [-.242,.242]:
        for z in [.49,.83,1.29,1.69]:
            sample('Raised stone surround at title tablet',x,z,['stepped stone edging'],.065)
    for x in [-.184,.181]:
        for z in [.62,1.08,1.457]:
            sample('Light stone title panel separate from bronze letters',x,z,['light stone face'],.0615)
    for char,center_z in zip('金谷邨',(1.457,1.071,.636)):
        for path in STROKES[char]:
            a,b=path[:2]
            x=((a[0]+b[0])/2-.5)*.251;z=center_z+((a[1]+b[1])/2-.5)*.255
            sample('Raised characters '+char,x,z,['raised bronze gold'],.077)
    for x in [-.217,.217]:
        for z in [1.833,1.892,1.945]:sample('Green enamel address border',x,z,['green enamel sign'],.060)
    for i,char in enumerate('18弄1–83号'):
        stroke=STROKES[char][0];a,b=stroke[:2]
        sample('Individually formed painted address '+char,(i-3.5)*.048+((a[0]+b[0])/2-.5)*.038,
               1.913+((a[1]+b[1])/2-.5)*.061,['cream sign letters'],.0625)
    sample('Pier plinth extends across the wall joint',.42,.12,['weathered stone base'],.055)
    for x in [.46,.62,.84]:
        sample('Set-back wall base beyond the end of the plinth',x,.12,['weathered stone base'],-.0705)
        sample('Short coping on adjoining wall',x,1.655,['stepped stone edging'],-.065)
        sample('Wall crest below the top of the name pier',x,1.715,['light stone face'],-.0755)
        sample('Sky above short boundary screen',x,1.89)
    for x in [1.01,1.31]:
        for z in [.1,.75,1.49,2.02]:sample('No adjoining building added',x,z)
    return dict(passed=all(row['passed']for row in rows),samples=rows)

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
