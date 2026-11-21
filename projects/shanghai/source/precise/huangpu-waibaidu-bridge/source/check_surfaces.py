"""Intersect independently decoded bridge meshes with rays through roadways, truss frames and river openings."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-waibaidu-bridge'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows = []
    def probe(label, origin, direction, length, material=None, target=None, tolerance=.035):
        hit = scene.ray(origin, direction, length)
        if material is None:
            passed = hit is None
        else:
            passed = bool(hit and hit['material'] == material and abs(hit['distance_m']-target) <= tolerance)
        rows.append(dict(label=label, origin=origin, direction=direction, range_m=length,
                         expected_material=material, expected_distance_m=target, actual=hit, passed=passed))
    for y in (-45, -22, -.73, 22, 45):
        for x in (-7.3,7.3):
            probe('footway on either side', [x,y,.8], [0,0,-1], 1, 'pedestrian paving', .65)
        for x in (-3.55,3.55):
            probe('open carriageway on each span', [x,y,.8], [0,0,-1], 1, 'road surface', .81)
    for side in (-1,1):
        for y in (-31.7, 26.8):
            probe('upper pedestrian rail', [side*10,y,1.36], [-side,0,0], 1.5, 'river-side railing', .864)
            probe('free sight below the rail', [side*10,y,.28], [-side,0,0], 1.25)
    for x in (-4,4):
        probe('upstream/downstream pier face', [x,-4,-2.6], [0,1,0], 5, 'weathered pier stone', 2.22)
        for y in (-33,-16,16,33):
            probe('open river under each span', [x,y,-1.5], [0,0,-1], 5)
    for ybase in (-52.12,0):
        for panel in (1,5,10):
            y=ybase+52.12*panel/11
            t=(panel-1)/9;hz=7.30+1.90*(1-(2*t-1)**2)
            probe('opening under transverse portal', [0,y,1.65], [0,0,1], 3)
            probe('cross-frame lower edge above carriageway',[0,y,hz-1.45],[0,0,1],1.5,
                  'shaded ironwork', .7125)
            for sign in (-1,1):
                probe('side upright of each span', [sign*6.6,y,2.85],[-sign,0,0],1.1,
                      'soft grey bridge steel',.65)
    return dict(passed=all(v['passed'] for v in rows),total=len(rows),checks=rows)


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
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['checks'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
