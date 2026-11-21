from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='yangpu-sacred-heart-octagonal-belfry-louvres'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import sin,cos,pi
    rows=[]
    for a in (-45,0,45):
        theta=a*pi/180;normal=(sin(theta),-cos(theta));tangent=(cos(theta),sin(theta))
        centre=[normal[0]*2.10,2.10+normal[1]*2.10]
        def shoot(label,u,z,material,expected_depth):
            start=[centre[0]+tangent[0]*u+normal[0]*1.15,centre[1]+tangent[1]*u+normal[1]*1.15,z]
            direction=[-normal[0],-normal[1],0]
            result=scene.ray(start,direction,1.70)
            ok=result and result['material']==material and abs(result['distance_m']-(1.15-expected_depth))<.010
            rows.append(dict(face_degrees=a,label=label,origin=start,direction=direction,expected_material=material,expected_surface_outward_m=expected_depth,observed=result,passed=bool(ok)))
        for name,base,pitch in [('lower',.35,.181),('upper',2.74,.202)]:
            for j in range(10):
                z=base+j*pitch
                for u in (-.08,.08):shoot(name+' louvre edge '+str(j+1),u,z+.016,'louvre upper face',-.055)
                shoot(name+' ventilation slot '+str(j+1),0,z+.137,'shaded belfry',-.325)
        for u in (-.55,.55):
            for z in (.53,1.26,2.82,3.56):shoot('recessed field',u,z,'recessed render',-.062)
        for u in (-.80,.80):
            for z in (1.20,2.8,4.36):shoot('proud tower pier',u,z,'weathered grey render',0.)
        shoot('central upper apron',0,2.56,'pale reveal',-.035)
        shoot('lower threshold',.08,.225,'pale reveal',.025)
    return dict(passed=all(v['passed']for v in rows),samples=rows)

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
