from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-wukang-2-garden-villa-curved-balcony'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import cos,sin,pi,radians
    rows=[]
    def measure(label,origin,vector,maximum,material,interval):
        hit=scene.ray(origin,vector,maximum)
        ok=hit is None if material is None else bool(hit and hit['material']==material and interval[0]<=hit['distance_m']<=interval[1])
        rows.append({'check':label,'origin':origin,'direction':vector,'maximum_m':maximum,'material':material,'distance_m':interval,'hit':hit,'passed':ok})
    for sign in (-1,1):
        for z in (.48,.81,1.60,2.21,2.84):
            measure('Tuscan shaft', [sign*1.86,-3.50,z],[0,1,0],3,'ivory column',[1.579,1.653])
        measure('square abacus above shaft',[sign*1.86,-3.50,3.25],[0,1,0],2,'ivory column',[1.506,1.524])
        measure('plinth',[sign*1.86,-3.50,.081],[0,1,0],2,'pale balcony render',[1.518,1.538])
        measure('column-free walking space',[sign*.73,-2.56,1.81],[0,1,0],2.70,None,[])
    for x in (-1.32,-.74,.74,1.32):
        for z in (1.41,1.94,2.19):
            measure('recessed entrance glass',[x,-3.50,z],[0,1,0],5.2,'glazing in shade',[4.52,4.54])
        measure('timber door rails',[x,-3.50,1.06],[0,1,0],5.2,'timber finish',[4.44,4.46])
    for x in (-.76,-.47,.47,.76):
        for y in (-1.48,-.70,.31):
            measure('underside of balcony',[x,y,2.0],[0,0,1],2.5,'pale balcony render',[1.33,1.35])
            measure('upper terrace paving',[x,y,5.50],[0,0,-1],2.3,'balcony floor',[1.78,1.80])
            measure('under-column paving',[x,y,1.65],[0,0,-1],2.1,'entry paving',[1.63,1.66])
    def radial(label,a,depth,z,material,interval):
        x=(3.04-depth)*sin(a); y=-(2.60-depth)*cos(a)
        d=(sin(a),-cos(a))
        measure(label,[x+d[0]*.28,y+d[1]*.28,z],[-d[0],-d[1],0],.57,material,interval)
    boundaries=[-pi/2,radians(-36),radians(36),pi/2]
    for a in boundaries:
        radial('cream masonry between iron panels',a,.13,4.43,'pale balcony render',[.163,.20])
    for index,(aa,bb) in enumerate(zip(boundaries,boundaries[1:])):
        count=6 if index==1 else 5
        lo,hi=aa+.056,bb-.056
        for j in range(count):
            p=(hi-lo)/count;mid=lo+(j+.5)*p
            radial('oval ring side',mid+.396*p*cos(.50),.135,4.414+.333*sin(.50),'bronze green circles',[.28 - .048 - .005, .28 + .002])
            radial('transparency through centre of oval',mid,.135,4.414,None,[])
            radial('continuous upper green bar',mid+.31*p,.135,4.77,'green stretcher rails',[.241,.271])
        for a in (lo+.137*(hi-lo),lo+.61*(hi-lo)):
            radial('pale upper stone cap',a,.032,4.91,'pale balcony render',[.263,.304])
            radial('projecting balcony nose',a,-.038,3.65,'ivory column',[.263,.304])
    return {'passed':all(r['passed'] for r in rows),'samples':rows}

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
