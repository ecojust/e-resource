"""Review photographed entrance recesses, glazed canopies, sash rows, six circular ornaments and seven separate gilded characters against all delivery meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-yanan-road-telegraph-exchange'
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
    stone='light dressed limestone'
    glass='grey green window glass'
    def front(label,x,z,materials,a,b):
        probe(label,[x,-2,z],[0,1,0],materials,a,b)
    for name,x in [('west',-11.70),('middle',0),('east',11.70)]:
        front(name+' recessed entrance backing',x,1.58,['bronze entry door'],3.38,3.42)
        front(name+' paired door glazing',x+.50,1.31,[glass],3.28,3.34)
        front(name+' stone jamb and round column',x+1.18,1.5,[stone],2.37,2.45)
        front(name+' jamb capital',x-1.27,2.74,[stone],2.44,2.53)
        front(name+' curved stone head',x+.025,3.78,[stone],2.63,2.71)
        front(name+' leading canopy rail',x+.61,3.11,['charcoal metal casement'],1.58,1.65)
        probe(name+' projecting glass canopy',[x+.55,.08,5],[0,0,-1],['green-grey canopy glass'],1.79,1.87)
        probe(name+' open space below canopy',[x+.55,.08,2.52],[0,0,-1],None,0,0)
    for row,(z,height) in enumerate([(4.75,2.68),(8.79,2.92),(12.62,2.82),(16.43,2.68),(20.57,1.73)]):
        for col,x in enumerate([-12.65,-10.12,-6.25,-3.75,-1.25,1.25,3.75,6.25,10.12,12.65]):
            front(f'tier {row+2} individual recessed sash {col+1}',x+.25,z+height*.35,[glass],3.21,3.25)
    for index,x in enumerate([-6.25,-3.75,-1.25,1.25,3.75,6.25]):
        front(f'round flower {index+1} raised centre',x,12.12,[stone],2.61,2.65)
        front(f'round flower {index+1} outline',x+.205,12.12,[stone],2.63,2.67)
        front(f'round flower {index+1} recessed groove',x+.11,12.20,['recessed stone'],2.68,2.73)
    for x in [-7.55,-5.,-2.5,0,2.5,5.,7.55]:
        front(f'giant order at {x}',x,15.24,[stone,'buff sandstone'],2.61,2.66)
    for ch,x,z in [('上',-2.74802,8.01473),('海',-1.59120,8.18588),('电',-1.22415,8.01437),
                   ('信',-.26123,7.94715),('博',.60545,7.82333),('物',1.57827,7.85840),('馆',2.684,7.89572)]:
        front('gilded sign character '+ch,x,z,['gilded sign characters'],2.44,2.47)
    front('black tablet surrounding the letters',3.37,7.94,['black museum sign'],2.47,2.51)
    for side,x in [('west',-11.56),('east',11.56)]:
        front(side+' parapet round relief',x+.08,24.14,[stone],2.76,2.80)
        front(side+' parapet cap',x,24.82,[stone],2.75,2.82)
    for x in [-10.,0,10.]:
        probe('roof behind the facade '+str(x),[x,2.15,28],[0,0,-1],['grey roof cap'],4.56,4.62)
    probe('beyond the south street section',[15.65,-2,9.17],[0,1,0],None,0,0)
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
