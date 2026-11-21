"""Independently trace both garden arcades, upper balustrades, casements and cut roof."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-ailu-residence-garden-loggia'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def probe(label,origin,direction,mats,lo,hi):
        hit=scene.ray(origin,direction,40)
        passed=hit is None if mats is None else hit is not None and hit['material'] in mats and lo<=hit['distance_m']<=hi
        rows.append(dict(label=label,origin=origin,direction=direction,expected_materials=mats,distance_bounds_m=[lo,hi],actual=hit,passed=passed))
    def south(label,x,z,mats,lo,hi):
        probe(label,[x,-2,z],[0,1,0],mats,lo,hi)
    stone=['dressed grey stone']
    top=['weathered coping']
    glass=['cool window glass','dark timber sash']
    render=['pebbled grey render','sheltered render']
    for label,xcenter,w,y,inner in [('broad',6.61,8.12,0.,4.33),('small',-1.96,4.88,2.62,5.53)]:
        for side in (-1,1):
            for z in (.67,1.14,1.70):
                south(label+' independently jointed arch jamb',xcenter+side*(w/2+.135),z,stone,2+y-.165,2+y-.065)
        south(label+' central keystone',xcenter,4.05,stone,2+y-.215,2+y-.10)
        for delta in (-.70,.11,.73):
            south(label+' through broad arch to shaded door or window',xcenter+delta,1.42,glass,2+inner+.01,2+inner+.147)
        for xratio in (-.29,0,.29):
            south(label+' upper floor sashes beyond balustrade',xcenter+xratio*(10.26 if label=='broad'else 6.88)+.12,6.28,glass,2+inner+.01,2+inner+.147)
        south(label+' storey moulding',xcenter+w*.32,4.24,top,2+y-.15,2+y-.08)
        for sign in (-1,1):
            south(label+' solid upper stone corner pier',xcenter+sign*((10.26 if label=='broad'else 6.88)/2-.31),7.31,stone,2+y-.09,2+y-.045)
    south('main balcony midsection projects past the side groups',6.61,5.70,stone,1.18,1.25)
    for x in (3.51,9.71):
        south('upper handrail flanking the stepped balcony',x,5.70,stone,1.80,1.87)
    for y in (.68,3.63):
        probe('side arch cut jamb',[14,y,1.12],[-1,0,0],stone,2.08,2.17)
    probe('side arch to opposite inner section',[14,2.12,1.4],[-1,0,0],None,0,0)
    probe('side keystone to lower return arch',[14,2.165,4.04],[-1,0,0],stone,2.06,2.15)
    for x in (-9.23,-8.93):
        south('smaller west casement',x,5.75,glass,5.16,5.30)
    for x,y,lo,hi in [(6.61,6.8,4.7,5.1),(2.14,3.05,6.1,7.5),(-2.14,5.96,5.3,6.2)]:
        probe('pitched roof surface over garden pavilion',[x,y,16],[0,0,-1],['muted clay tile'],lo,hi)
    for x,y in [(9.92,6.08),(9.92,10.13)]:
        probe('two photograph-visible pale chimney caps',[x,y,13],[0,0,-1],stone,1.80,1.88)
    south('amber arched fanlight beyond the stone porch',6.61+10.26*.32-.24,3.23,['amber fanlight'],6.41,6.46)
    probe('recessed arch on east return',[14,7.715+2.1,1.20],[-1,0,0],['sheltered render'],2.82,2.91)
    probe('west lean-to roof',[-8.22,2.46,7.0],[0,0,-1],['muted clay tile'],3.44,3.57)
    probe('east downpipe outside wall',[14,4.29,2.8],[-1,0,0],['aged rainwater pipe'],2.00,2.15)
    for x,y in [(-9,1),(-5,-2),(3,-2),(14,2),(8,16),(-3,14)]:
        probe('open garden or excluded rear',[x,y,16],[0,0,-1],None,0,0)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)


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
