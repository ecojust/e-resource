from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-hongqiaoyuan-east-upturned-eave-corner'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from upturned_eaves import zroof,place,PITCH
    rows=[]
    def vertical(label,side,a,b,z,mats,tol=.016):
        p=place(side,a,b,z+.17)
        hit=scene.ray(p,[0,0,-1],.34)
        rows.append(dict(label=label,origin=p,direction=[0,0,-1],expected_material=mats,expected_height=z,observed=hit,passed=bool(hit and hit['material']in mats and abs(hit['distance_m']-.17)<tol)))
    for s in (0,1):
        for col in (2,4,6,8,10,12,14):
            x=(col+.5)*PITCH
            for y in (.063,.156,.229):
                if x-y<.106:
                    q=(x+y)/2
                    vertical('raised edge of hip in front of cover tile',s,x,y,zroof(q,q)+.070,['gray cover tile'])
                else:
                    vertical('round top of raised cover tile',s,x,y,zroof(x,y)+.041,['charcoal tile','gray cover tile','light cover tile'])
                vertical('gray pan between two rolls',s,x+.055,y,zroof(x+.055,y),['gray clay bed'])
        for c in (.18,.45,.81,1.1,1.68,1.83):
            vertical('face of upturned fascia',s,c,-.044,zroof(c,0)-.050,['rafters and barge'])
        for k in (3,6,9,13):
            x=.13+k*.122; y=.091;z=zroof(x,y)-.166
            pos=place(s,x,y,z-.15);hit=scene.ray(pos,[0,0,1],.32)
            rows.append(dict(label='visible lower edge of timber rafter',origin=pos,expected_material='weathered timber',observed=hit,passed=bool(hit and hit['material']=='weathered timber' and abs(hit['distance_m']-.15)<.008)))
    for q in (.12,.22,.4,.56,.71,.85):
        vertical('diagonal crown over both slopes',0,q,q,zroof(q,q)+.058,['bedded gray ridge'])
    for t in (.36,.48,.64,.82,.95):
        q=-.045-.157*t
        z=zroof(0,0)-.027+.219*t**1.45
        vertical('tip of upward-curved corner timber',0,q,q,z,['rafters and barge'],.002)
    for t in (.64,.82,.95):
        q=-.045-.157*t
        z=zroof(0,0)-.027+.219*t**1.45
        width=.049*(1-t)+.007*t
        p=[q+width+.012,q-width-.012,z+.12]
        hit=scene.ray(p,[0,0,-1],.24)
        rows.append(dict(label='open space beside tapering timber',origin=p,observed=hit,passed=hit is None))
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
