"""Check balcony faces, open rail slot, exposed soffit, sash profiles and elevation limits."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-jianguo-618-historic-front'
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
    for x in (-1.64,-.87,-.16,.61):
        for z in (.67,1.08):
            front('lower independent sash glazing',x,z,'pale blue window glass',5.123,5.129)
    for x in (-1.26,.27):
        front('lower wide toplights',x,1.81,'pale blue window glass',5.123,5.129)
    for x in (-1.26,-.52,.22):
        front('lower casement join',x,.97,'painted ivory sash',5.076,5.082)
    for x in (-1.64,-.17,.62):
        front('lower transom',x,1.43,'painted ivory sash',5.033,5.039)
    for x in (-.38,.53):
        front('upper glazed leaves visible over parapet',x,4.76,'pale blue window glass',5.123,5.129)
        front('upper continuous toplight',x,5.38,'pale blue window glass',5.123,5.129)
        front('upper transom bar',x,5.0,'painted ivory sash',5.033,5.039)
    for x in (-1.31,-.71,.04,.73,1.42):
        front('separate solid parapet face',x,3.82,'light concrete face',3.905,3.912)
        front('forward projecting floor slab',x,3.37,'light concrete face',3.905,3.911)
        front('elevated top rail',x,4.363,'light balcony coping',3.914,3.921)
        if abs(x-.05)>.09:
            ray('open slot beneath top rail',[x,-1.25,4.29],[0,1,0],.25,None)
        ray('exposed cantilever underside',[x,-.54,2.92],[0,0,1],.5,
            'warm concrete soffit',.329,.336)
        ray('upper surface behind the solid parapet',[x,-.52,3.75],[0,0,-1],.4,
            'grey balcony deck',.225,.232)
    for x in (-1.593,.05,1.693):
        front('individual supports in rail slot',x,4.29,'light balcony coping',3.934,3.941)
    ray('right solid return viewed transversely',[2.02,-.54,3.87],[-1,0,0],.75,'light concrete face',.237,.244)
    for z in (1.0,2.56,4.72,5.62):
        front('wall finish remains flush',1.97,z,'ivory rendered wall',4.997,5.003)
    for z in (2.10,3.04,4.06,5.08):
        front('thin horizontal panel joint',2.19,z,'shadow in facade joint',5.015,5.021)
    front('vertical panel joint',2.05,2.79,'shadow in facade joint',5.015,5.021)
    for x in (-1.84,.18,2.08):
        front('upper slab fascia',x,6.02,'ivory rendered wall',4.896,4.901)
        front('upper roof-edge lip',x,6.102,'light concrete face',4.854,4.859)
    for x,y,z in [(2.61,.31,1.42),(-2.58,-.3,1.77),(.19,-1.27,5.19),(.21,.31,6.32)]:
        ray('air outside this partial elevation',[x,y,z],[0,0,1],.5,None)
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
