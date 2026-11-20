"""Measure the actual decoded full/LOD, and sample their east entry and two open courts."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2]
SRC=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
def digest(path):return sha256(path.read_bytes()).hexdigest()

def witnesses(scene):
    out=[]
    def ray(name,start,direction,material,expected,far=7):
        hit=scene.ray(start,direction,far)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-expected)<.025)
        out.append(dict(name=name,origin=start,direction=direction,material=material,expected_distance_m=expected,actual=hit,passed=passed))
    for side in [-1,1]:
        for feature,u,z,mat,depth in [('trefoil opening',.24,2.13,'glass grey',-.283),('upper crossed web',.48,2.68,'old red door',-.109),
            ('second floral aperture',.20,2.68,'glass grey',-.283),('cloud crown',.65,1.03,'brass',-.060),
            ('panel field',.65,.77,'old red door',-.116),('narrow panel moulding',.65,1.336,'old red door',-.055),
            ('side scroll band field',2.50,.76,'entrance stone recess',.085),
            ('inner door jamb',1.36,2.,'stone carved',.170),('arch field',.48,3.91,'entrance stone recess',.104)]:
            ray(feature+' '+str(side),[20,-1.12+side*u,z],[-1,0,0],mat,1.06-depth)
    ray('two unobstructed leaves beneath arch field',[20,-1.12,1.279],[-1,0,0],'old red door',1.06+.116)
    ray('central floral medallion',[20,-1.12,3.87],[-1,0,0],'stone carved',1.06-.139)
    for n,y in [('south court',-16.425),('north court',19.545)]:
        ray(n+' open sky above walking height',[1.335,y,24],[0,0,-1],None,None,22.2)
    assert all(r['passed']for r in out),[(r['name'],r['actual'])for r in out if not r['passed']]
    return out

def main():
    cli=ArgumentParser(description=__doc__)
    for name in ['raw','web','lod-source','lod','out']:cli.add_argument('--'+name,type=Path,required=True)
    args=cli.parse_args();reader=runpy.run_path(str(READER))['SerialScene'];report={}
    with tempfile.TemporaryDirectory()as tmp:
        for name,source,packed in [('full',args.raw,args.web),('lod',args.lod_source,args.lod)]:
            decoded=Path(tmp)/(name+'.glb')
            subprocess.run(['node',SRC,packed,decoded,PROJECT/'vendor/meshopt_decoder.module.js'],check=True)
            raw=reader(source);orientation=raw.surface_digest();a=witnesses(raw);del raw
            web=reader(decoded);assert orientation==web.surface_digest()
            b=witnesses(web);assert len(a)==len(b)
            report[name]=dict(source_sha256=digest(source),packed_sha256=digest(packed),triangles=len(web.tri),
                oriented_material_surfaces=orientation,source_rays=a,decoded_rays=b)
    args.out.write_text(json.dumps(dict(checker_sha256=digest(Path(__file__)),reader_sha256=digest(READER),passed=True,
          variants=report),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
