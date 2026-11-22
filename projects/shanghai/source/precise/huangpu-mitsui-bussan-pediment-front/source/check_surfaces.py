"""Check the street pediment, individual arch bays, 181 portal, rusticated corner and published materials in each delivery mesh."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-mitsui-bussan-pediment-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples = []
    def probe(label, origin, direction, material, minimum, maximum, length=30):
        hit = scene.ray(origin,direction,length)
        valid = hit is None if material is None else (hit is not None and
                hit['material'] in material and minimum <= hit['distance_m'] <= maximum)
        samples.append(dict(label=label,origin=origin,direction=direction,allowed=material,
                            expected_distance_m=[minimum,maximum],hit=hit,passed=valid))
    stone='pale limestone'; shade='recessed warm stone'; glass='deep blue-grey glass'
    brick='warm red running-bond brick'; door='dark bronze door'
    def front(label,x,z,materials,a,b):
        probe(label,[x,-2,z],[0,1,0],materials,a,b)
    for row,xs,z in [(1,[-2.05,-.61],2.45),(2,[-2.06,-.60],5.84),(3,[-2.35,-1.33,-.31],9.44)]:
        for col,x in enumerate(xs):
            front(f'tier {row} recessed sash {col+1}',x+.17,z,[glass],3.22,3.31)
    for z in [5.89,9.47,12.44]:
        front('plain northern bay '+str(z),3.03,z,[glass],3.22,3.31)
    for x in [-1.97,-.69]:
        front('independent attic window '+str(x),x+.13,12.59,[glass],3.22,3.31)
    for x in [-2.78,-1.33,.12]:
        front('double-window pier '+str(x),x+.053,5.52,[stone,shade],2.66,2.82)
    for x in [-2.88,-1.84,-.82,.22]:
        front('triple-window pier '+str(x),x+.038,9.23,[stone,shade],2.66,2.82)
    front('pediment inner tympanum',-1.33,11.27,[shade],2.71,2.77)
    front('pediment rising moulding',-1.33,11.79,[stone],2.56,2.65)
    front('pediment horizontal bed',-1.33,10.64,[stone],2.43,2.65)
    front('portal deep leaf',2.53,1.23,[door],3.30,3.41)
    front('portal jamb',4.05,2.31,[stone,shade],2.64,2.84)
    front('door moulded lintel',2.85,3.43,[stone],2.31,2.50)
    front('portal crest',2.85,3.95,[stone],2.62,2.68)
    front('green number plaque enamel',4.40+.11,1.67,['green enamel'],2.83,2.87)
    for offset in [-.071,.071]:
        front('181 raised one '+str(offset),4.40+offset,1.63,['enamel lettering'],2.83,2.85)
    for z in [1.63-.019-.020,1.63+.023+.020]:
        front('181 figure eight loop '+str(z),4.40,z,['enamel lettering'],2.83,2.85)
    for i in [0,4,12,20,24]:
        front('south corner alternating stone '+str(i),-5.52,.53+.50*i,[stone],2.66,2.76)
        front('red brick bed between corner stones '+str(i),-5.52,.76+.50*i,[brick,stone],2.69,2.96)
    for z in [2.1,6.5,9.5,12.4]:
        front('unobstructed brick panel at '+str(z),1.41,z,[brick],2.92,2.96)
    for x in [-4.7,.89,4.61]:
        probe('roof section '+str(x),[x,1.72,17],[0,0,-1],['grey metal coping'],3.30,3.39)
    probe('outside narrow photographed front',[6.17,-2,8.71],[0,1,0],None,0,0)
    return dict(passed=all(row['passed'] for row in samples),samples=samples)


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
