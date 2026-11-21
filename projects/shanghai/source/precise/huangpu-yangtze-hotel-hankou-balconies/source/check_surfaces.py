"""Probe the twelve open balconies, clipped corners, steel frames and sheltered entrance."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-yangtze-hotel-hankou-balconies'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def check(name,origin,direction,allowed,distances,limit):
        hit=scene.ray(origin,direction,limit)
        valid=hit is None if not allowed else bool(hit and hit['material'] in allowed and distances[0]<=hit['distance_m']<=distances[1])
        samples.append(dict(check=name,origin=origin,direction=direction,allowed=allowed,distance_range=distances,passed=valid,actual=hit))
    def front(label,x,z,mat,d0,d1):
        check(label,[x,-3.,z],[0,1,0],mat,[3-d1,3-d0],6)
    def down(label,x,y,z,depth_max,mat,expected):
        check(label,[x,y,z],[0,0,-1],mat,[expected-.012,expected+.012],depth_max)
    for axis in [-4.76,0,4.76]:
        for base in [4.53,8.32,12.10,15.89]:
            for x in [-1.24,-.82,-.27,.27,.82,1.24]:
                down('faceted balcony floor',axis+x,-.57,base+.53,.63,['pale cast stone coping'],.53)
            for side in [-1,1]:
                # The splayed front corners are open outside the actual plan and solid just inside.
                down('clipped front corner is open',axis+side*1.32,-1.13,base+.08,.18,[],0.)
                down('slab inside splay',axis+side*1.23,-.85,base+.12,.19,['pale cast stone coping'],.12)
                front('glazing behind balcony rails',axis+side*.20,base+1.27,['blue grey window glass'],-.152,-.136)
                front('open railing at raised level',axis+side*.58,base+.938,['charcoal balcony iron'],1.16,1.24)
            front('center casement upright',axis,base+1.23,['charcoal balcony iron'],-.087,-.068)
            front('handrail perforation reaches the glass',axis+.13,base+.74,['blue grey window glass'],-.155,-.133)
            for x in [-.61,.61]:
                front('stone bracket below projecting slab',axis+x,base-.285,['warm grey limestone'],.79,.85)
            # A sampled small bouquet may differ in shape and count between the two LODs.
            hits=[]
            for j in range(17):
                px=axis-.86+1.72*j/16
                hit=scene.ray([px,-2.,base+.16],[0,1,0],1.0)
                if hit and hit['material'] in ['leaf green planter','deep rose flower clusters','vermilion flower petals']:
                    hits.append([px,hit['material']])
            samples.append(dict(check='detachable red and green flower display',axis=axis,base=base,first_hits=hits,passed=len(hits)>=9))
    for x in [-2.38,2.38]:
        for base in [4.53,8.32,12.10,15.89]:
            sill=base+(1.18 if base==4.53 else .83)
            front('separate recessed companion window',x+.18,sill+.43,['blue grey window glass'],-.154,-.135)
            front('companion sill proud of the wall',x+.2,sill-.035,['pale cast stone coping'],.100,.12)
            front('companion steel mullion',x,sill+.43,['charcoal balcony iron'],-.085,-.066)
    for x in [-.70,-.34,.34,.70]:
        for z in [.68,1.40,2.12]:
            front('recessed closed entrance glass',x,z,['amber vestibule glass'],-.442,-.426)
    for x in [-1.63,-1.43,1.43,1.63]:
        front('rounded sidelight glass',x,1.43,['amber vestibule glass','dark bronze entrance framing'],.015,.15)
    for x in [-2.30,-1.72,-.57,.49,1.68,2.33]:
        down('real canopy over entrance',x,-.67,3.90,.29,['dark bronze entrance framing'],.22)
    for x in [-3.55,3.52]:
        front('stone jamb outside glazing',x,1.25,['warm grey limestone'],.002,.014)
    for x,z in [(-7.,3),(7.,11),(-4.5,1.55),(4.4,2.3),(0,19.85)]:
        check('retained part beyond the study',[x,-3.,z],[0,1,0],[],[],8)
    return dict(passed=all(q['passed']for q in samples),samples=samples)
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
