"""Probe the blind rounded brick wall, two distinct street fronts, shallow arches and recessed openings at 115 Middle Jiangxi Road."""
from argparse import ArgumentParser
import numpy as np
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-hengye-li-jiangxi-corner'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    from math import cos,sin,radians,tan
    radius=1.38
    theta=radians(89.02736888496747)
    center=np.array([-radius*tan(theta/2),radius])
    east0=center+radius*np.array([sin(theta),-cos(theta)])
    east_t=np.array([cos(theta),sin(theta)])
    south0=np.array([center[0]-7.26,0.])
    results=[]
    def shoot(name,point,normal,z,material,low,high):
        origin=[float(v) for v in point+2.*normal]+[z]
        direction=[float(v)for v in -normal]+[0.]
        hit=scene.ray(origin,direction,4.2)
        ok=(hit is None) if material is None else bool(hit and hit['material']==material and low<=hit['distance_m']<=high)
        results.append(dict(test=name,origin=origin,direction=direction,expected=material,permitted_distance_m=[low,high],hit=hit,passed=ok))
    for name,first,t,span in [('Sijing',south0,np.array([1.,0.]),7.26),('Jiangxi',east0,east_t,6.90)]:
        normal=np.array([t[1],-t[0]])
        def check(label,along,z,mat,low,high):shoot(name+' '+label,first+along*t,normal,z,mat,low,high)
        for number in range(3):
            axis=(number+.5)*span/3
            for floor,glass_z,sash_z,crown in [(2,5.82,5.70,7.72),(3,9.24,9.64,10.84)]:
                check(f'floor {floor}, bay {number+1} glazing',axis+.21,glass_z,'smoky window glass',2.30,2.34)
                check(f'floor {floor}, bay {number+1} sash',axis,sash_z,'dark painted sash',2.14,2.18)
                check(f'floor {floor}, bay {number+1} arch',axis+.10,crown,'radial red brick',1.92,1.96)
            if name=='Sijing':
                check(f'lower arched bay {number+1} glazing',axis+.18,1.70,'smoky window glass',2.30,2.34)
                check(f'lower arched bay {number+1} sill',axis-.24,.94,'carved pale stone',1.58,1.62)
                check(f'lower arched bay {number+1} brick arch',axis+.10,3.65,'radial red brick',1.92,1.96)
        if name=='Jiangxi':
            for along,z,label in [(1.56,1.53,'higher rectangular display'),(4.24,.76,'lower door')]:
                check(label,along+.16,z,'smoky window glass',2.30,2.34)
            check('brick outside rectangular display',.62,2.15,'charcoal grey face brick',1.98,2.02)
        for z,mat,low,high,label in [(.19,'dark stone plinth',1.96,1.99,'plinth'),(4.4,'dull red face brick',1.80,1.84,'projected belt'),(8.13,'weathered pale sill',1.84,1.88,'wrapped upper course'),(11.39,'pale eave soffit',1.65,1.71,'eave'),(12.05,None,0,4.2,'air above eave')]:
            check(label,.21,z,mat,low,high)
    for degree in (18,42,69):
        normal=np.array([sin(radians(degree)),-cos(radians(degree))])
        point=center+radius*normal
        for z,mat,low,high,label in [(2.11,'charcoal grey face brick',1.98,2.025,'solid brick'),(1.25,'dull red face brick',1.97,2.01,'lower red band'),(4.4,'dull red face brick',1.80,1.85,'projecting belt'),(10.12,'charcoal grey face brick',1.98,2.025,'unwindowed upper corner'),(11.39,'pale eave soffit',1.66,1.71,'curved soffit'),(12.05,None,0,4.2,'air above')]:
            shoot(f'curved corner {degree} degrees {label}',point,normal,z,mat,low,high)
    return dict(passed=all(v['passed']for v in results),samples=results)


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
