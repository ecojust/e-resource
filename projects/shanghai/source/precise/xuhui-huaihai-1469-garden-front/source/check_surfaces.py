"""Check historic bays, recessed lights, columns and the limits of the standalone elevation."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-huaihai-1469-garden-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label, origin, direction, length, material, low=None, high=None):
        hit=scene.ray(origin,direction,length)
        valid=hit is None if material is None else bool(hit and hit['material']==material and
                      (low is None or low <= hit['distance_m'] <= high))
        rows.append(dict(test=label,origin=origin,direction=direction,length_m=length,
                         expected_material=material,expected_distance_range=[low,high],hit=hit,passed=valid))
    def front(label,x,z,mat,lo=None,hi=None):
        ray(label,[x,-5,z],[0,1,0],8,mat,lo,hi)
    for x in [-5.52,0,5.52]:
        for u in [-1.49,-.61,.64,1.48]:
            for h in [5.27,6.23]:
                front('upper sash cells',x+u,h,'muted blue green glazing',5.116,5.120)
        for u in [-1.065,0,1.065]:
            front('upper vertical mullions',x+u,5.55,'deep green painted glazing bars',5.062,5.066)
    for x in [-5.52,5.52]:
        for u in [-1.52,-.61,.62,1.54]:
            for h in [1.38,2.76]:
                front('lower sash cells',x+u,h,'muted blue green glazing',5.116,5.120)
        for u in [-1.045,0,1.045]:
            front('lower vertical mullions',x+u,1.85,'deep green painted glazing bars',5.062,5.066)
        front('transom across lower glazing',x+.33,2.321,'deep green painted glazing bars',5.043,5.047)
    for x in [-7.40,-4.4,4.4,7.40]:
        front('inter-storey belt face',x,3.92,'pale warm masonry',4.827,4.832)
        front('projecting drip above belt',x,4.06,'slate grey cornice edge',4.793,4.797)
        front('upper continuous cornice',x,6.88,'cream mouldings and columns',4.831,4.837)
    for x in [-2.9,-2.62,2.62,2.9]:
        front('paired flat upper pilasters',x,5.62,'cream mouldings and columns',4.885,4.890)
    for x in [-3.08,3.08]:
        for y in [-1.79,-.38]:
            ray('free-standing slender support',[x,y-.31,2.4],[0,1,0],.55,'cream mouldings and columns',.142,.164)
            ray('clear space adjacent to support',[x+.31,y-.31,2.4],[0,1,0],.55,None)
    for i in range(6):
        y=-3.575+i*.30+.17
        ray('individual central stair tread',[.12,y,1.02],[0,0,-1],1.03,'grey tan stair stone',1.02-.104*(i+1)-.003,1.02-.104*(i+1)+.003)
    for x in [-2.16,2.16]:
        ray('pair of square step-side caps',[x,-1.75,1.002],[0,0,-1],.5,'cream mouldings and columns',.216,.221)
    for x,z in [(-1.12,1.65),(.05,2.32),(1.02,2.75)]:
        front('closed illustrative recess behind the porch',x,z,'dark red brown timber',5.738,5.743)
    for x in [-1.56,1.56]:
        front('small recessed joinery panels',x,1.69,'muted blue green glazing',5.706,5.711)
    for x in [-2.68,-.52,.93,2.67]:
        ray('open height below portico soffit',[x,-1.02,3.20],[0,0,1],.89,'warm shadowed soffit',.540,.546)
    for x,y,z in [(-8.55,0,4),(.12,1.20,3.2),(.11,-3.92,.28),(.17,.08,7.20)]:
        ray('limit of the archival elevation',[x,y,z],[0,0,1],.5,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(row['passed']for row in rows))


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
