from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-yangshupu-213-paired-fanlights'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import cos,sin,pi
    rows=[]
    def shoot(label,x,z,materials,depth):
        hit=scene.ray([x,-1.,z],[0.,1.,0.],1.7)
        passed=bool(hit and hit['material'] in materials and abs(hit['distance_m']-(1+depth))<.012)
        rows.append(dict(label=label,origin=[x,-1.,z],direction=[0.,1.,0.],expected_materials=materials,expected_surface_y=depth,observed=hit,passed=passed))
    for i,x in enumerate((-.81,.81)):
        for j in range(29):
            a=pi*(j+.5)/29
            shoot('Inner arch soldier '+str(j+1),x+.68*cos(a),1.51+.611*sin(a),['vermilion brick','deep red brick','ochre brick'],-(.089 if j in (0,28) else .066 if abs(a-pi/2)<.09 else .038))
        for j in range(1,32,3):
            a=pi*(j+.5)/32
            shoot('Outer brick arch thread',x+.765*cos(a),1.51+.696*sin(a),['vermilion brick','deep red brick','ochre brick'],-.048)
        for theta in (pi/4,pi/2,3*pi/4):
            for scale in (.34,.59,.79):
                shoot('Fanlight radial bar',x+.579*scale*cos(theta),1.51+.014*(1-scale)+.51*scale*sin(theta),['fanlight bars'],.109)
        for theta in (pi/8,3*pi/8,5*pi/8,7*pi/8):
            for scale in (.34,.69):
                shoot('Glazing between radial bars',x+.56*scale*cos(theta),1.51+.50*scale*sin(theta),['fanlight glass'],.143)
        for z in (.48,.85,1.12,1.34):
            for delta in (-.32,.31):shoot('Lower sash glazing',x+delta,z,['sash glass'],.153)
            shoot('Lower meeting stile',x,z,['pale frame'],.084)
        for side in (-1,1):
            for z,depth in [(1.44,-.058),(1.488,-.075),(1.52,-.089)]:
                shoot('Stepped arch springing',x+side*.678,z,['vermilion brick','deep red brick','ochre brick'],depth)
        for dx in (-.39,.05,.4):shoot('Projecting lower sill',x+dx,.258,['sill concrete'],-.056)
    for x in (-1.36,-.4,.35,1.36):
        shoot('Upper brick course',x,2.418,['deep red brick'],-.073)
    return dict(passed=all(v['passed'] for v in rows),samples=rows)

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
