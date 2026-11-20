"""Test the paired windows, twelve rose petals, eleven trefoils and actual entrance in all three delivered GLBs."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-jingling-church-north-front'
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
    from math import cos, pi, sin
    def front(label,x,z,mat,depth):
        sample(label,[x,-4,z],[0,1,0],mat,None if depth is None else 4-depth,.038)
    def vertical(label,x,y,z,mat):
        sample(label,[x,y,30],[0,0,-1],mat,None if z is None else 30-z,.025)
    front('cross upright',0,24.74,'pale concrete coping',.086)
    front('west cross arm',.31,24.40,'pale concrete coping',.086)
    front('east cross arm',-.31,24.40,'pale concrete coping',.086)
    for side in [-1,1]:
        front('side circular glazing',side*9.64+.17,15.78,'indigo architectural glass',-.255)
        front('side oculus brick rim',side*9.64,16.225,'red arch courses',.10)
        front('upper side lancet',side*9.67,10.85,'blue green glass',-.255)
        front('low arched window',side*6.32,2.03,'indigo architectural glass',-.255)
        front('flanking buttress',side*4.72,12.02,'red fair-faced brick',.335)
        front('buttress cap',side*4.72,14.50,'warm grey granite',.455)
        front('rainwater hopper',side*7.11,15.54,'aged rainwater iron',.225)
        front('outside side gable silhouette',side*12.2,20,None,None)
    for i in range(12):
        a=(i+.5)*pi/6
        front('flower head '+str(i+1),-.813*sin(a)+.050,16.54+.813*cos(a),'pale blue glass',-.081)
        front('amber rose petal '+str(i+1),-.615*sin(a),16.54+.615*cos(a),'honey glass',-.103)
    front('central rose bead',0,16.54,'blue green glass',-.052)
    for side in [-1,1]:
        front('lateral circular jewel',side*1.49,15.81,'muted ruby glass',-.10)
    for x in [-1.91,-1.17,0,1.17,1.91]:
        for z in [9.17,11.91,13.08]:
            front('continuous upright through former plaque height',x,z,'dark walnut frames',-.13)
    front('central red robe pane',-.63,9.03,'muted ruby glass',-.229)
    front('central pale mantle',-.51,10.91,'pale blue glass',-.215)
    front('side figure ochre pane',.64,9.12,'honey glass',-.234)
    for j in range(11):
        x=(j-5)*.765
        front('trefoil recessed stem '+str(j+1),x,6.05,'warm grey granite',.739)
        front('middle lobe '+str(j+1),x,6.75,'warm grey granite',.739)
        front('solid beside trefoil '+str(j+1),x+.27,6.64,'pale concrete coping',1.027)
    for i in range(7):
        y=-(2.40-.30*i)
        sample('front entrance rise '+str(i+1),[.92,y,4.0],[0,0,-1],'warm grey granite',4-(i+1)*.17,.025)
    for sign in [-1,1]:
        front('stone door jamb',sign*2.09,2.83,'pale concrete coping',.125)
        front('fanlight timber',sign*.86,3.87,'dark walnut frames',-.185)
        front('dark entrance leaf',sign*.55,1.64,'dark walnut frames',-.205)
    front('colored entrance fanlight',.20,3.91,'blue green glass',-.291)
    vertical('paving beyond relief',0,-3.10,None,None)
    vertical('unmodeled interior behind front',0,3.20,None,None)
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
