"""Check two recessed doors, paired casements on both upper levels and painted house numbers."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-remi-apartments-181-183'
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
    def front(label,x,z,material,depth):
        sample(label,[x,-3,z],[0,1,0],material,None if depth is None else 3-depth,.012)
    def above(label,x,y,z,material):
        sample(label,[x,y,9],[0,0,-1],material,None if z is None else 9-z,.013)
    for center,width in [(-.565,.815),(.535,.835)]:
        for height in [.22,.89,1.39]:
            front('recessed wooden door',center+.095,height,'brown wooden doors',-.311)
        front('metal door fitting',center-width*.32,.91,'grey security bars',-.2465)
        front('threshold',center,.021,'charcoal plinth',-.045)
        front('roughcast outside small arch',center+.34,1.82,'sand coloured roughcast',0)
    for (z0,h),windows in [((3.70,1.08),[(-.86,1.01),(.905,.97)]),
                            ((7.30,1.11),[(-.59,.99),(1.00,1.01)])]:
        for cx,width in windows:
            for dx in [-.153,.143]:
                for dz in [.16,.53,.86]:
                    front('small casement pane',cx+dx,z0+dz,'blue grey glass',-.153)
            front('middle vertical casement mullion',cx,z0+.19,'dark painted steel',-.098)
            front('brick casement sill',cx,z0-.04,'burgundy brick',.128)
            for dy in [.37,.68]:
                front('horizontal casement muntin',cx+.17,z0+h*dy,'dark painted steel',-.098)
    # The left-hand small sash above each door has no exterior guard. The right middle one does.
    for height in [3.84,4.08,4.43]:front('vertical grilles above 183',.905-.97*.45,height,'grey security bars',.066)
    for cx,cz,num in [(-.622,2.026,'181'),(1.708,1.865,'183')]:
        front('green enamel number '+num,cx-.129,cz,'enamel house plate',.0385)
        for j,digit in enumerate(num):
            xy={'1':(.08,0),'8':(0,.02),'3':(.26,.34)}[digit]
            front('traced enamel glyph '+digit,cx+(j-1)*.064+xy[0]*.078,cz+xy[1]*.098,'ivory enamel digits',.045)
    front('small marker between doors',.015,1.35,'blue community plaque',.0275)
    for x in [-2.86,-2.30,2.2,3.63]:
        front('dark foot',x,.08,'charcoal plinth',.011)
        front('rendered wall flank',x,3.16,'sand coloured roughcast',0)
    for x in [-2.88,-.85,.41,1.5,3.62]:front('red upper floor course',x,5.82,'burgundy brick',.086)
    for x in [-1.76,1.80]:
        front('three-level spring impost',x,1.59,'cream render moulding',.154)
    front('inner moulded archivolt at top',.02,1.52+1.295,'cream render moulding',.168)
    front('upper corbel',.25,9.31,'cream render moulding',.121)
    for cx,ztop in [(-1.57,10.84),(2.89,10.47)]:
        front('parapet upright',cx,8.81,'sand coloured roughcast',.054)
        front('light parapet coping',cx,ztop-.027,'cream render moulding',.111)
    for cx,z in [(-3.5,10.96),(3.95,10.66),(0,11.15),(-3.85,4.24),(4.42,1.54)]:
        front('clear ground or sky around measured gable',cx,z,None,None)
    return dict(passed=all(r['passed']for r in rows),samples=rows)


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
