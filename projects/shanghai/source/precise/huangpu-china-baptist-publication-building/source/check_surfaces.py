"""Verify the drawn fourteen-bay window grid, arched heads, masonry ribs and three roof levels."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-china-baptist-publication-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def sample(label,origin,direction,material,position,tolerance=.040):
        hit=scene.ray(origin,direction,55)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-position)<tolerance
        rows.append(dict(label=label,origin=origin,direction=direction,expected_material=material,expected_distance=position,actual=hit,passed=passed))
    def front(label,x,z,material,y,tolerance=.040):
        sample(label,[x,-3,z],[0,1,0],material,3+y if y is not None else None,tolerance)
    xs=[-10.24,-8.82,-7.17,-5.77,-3.925,-2.60,-.84,.52,2.26,3.63,5.40,6.79,8.52,9.91]
    for x in xs:
        for z in [5.50,11.65,17.75]:
            front('glazed light in one of fourteen lower stacks',x+.17,z,'blue-grey glazing',.38)
    for x in xs[5:9]:
        front('glass beneath the pointed head',x+.07,24.89,'blue-grey glazing',.38)
        front('arched head below the pier stone',x+.48,24.99,'brown face brick',.10)
        front('rectangular recess above pointed arcade',x,27.72,'deep stone reveal',.43)
        front('projecting brick brow above the pointed window',x+.35,25.00,'dark purple-brown rib brick',-.06,.025)
        front('stone apex of the projecting pointed hood',x,25.24,'pale water-washed stone',-.085,.025)
    for x in [-8.01,-4.79,-1.69,1.42,4.53,7.71]:
        front('forward ridge of crown-profile brick pilaster',x+.025,11.4,'dark purple-brown rib brick',-.26,.080)
    for x in [-9.53,-6.47,-3.2625,-.16,2.945,6.095,9.215]:
        front('single ridge of secondary brick pilaster',x+.01,11.4,'dark purple-brown rib brick',-.113,.035)
    for x in [-8.61,-4.94,4.96,8.6]:
        front('glazed shopfront in the pale stone base',x+.33,1.54,'blue-grey glazing',.51)
    front('recessed double door',.38,1.62,'blue-grey glazing',.62)
    front('historical stepped stone name panel',-2.21,3.75,'pale water-washed stone',-.117)
    for x,z in [(-1.24523,3.73577),(-.30025,3.61593),(.52928,3.80483),(.85593,3.67517)]:
        front('raised bronze plaque character',x,z,'bronze lettering',-.163,.015)
    for x in [-4.79,1.42,7.71]:
        front('folded stone tip on a broad brick rib',x-.2426,16.7108,'pale water-washed stone',-.133,.026)
        front('projecting shaft collar below the folded stone tip',x,16.61,'pale water-washed stone',-.343,.025)
    for x,z in [(0,29.57),(-9,26.73),(9.50,28.53)]:
        sample('height of separate parapet range',[x,1.5,35],[0,0,-1],'neutral section',35-z)
    sample('rear of the architectural study',[0,2.4,35],[0,0,-1],None,None)
    front('open space beyond south end',-11.9,9,None,None)
    front('open space beyond north end',11.9,9,None,None)
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
