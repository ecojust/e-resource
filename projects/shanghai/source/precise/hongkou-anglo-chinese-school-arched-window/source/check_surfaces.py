from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-anglo-chinese-school-arched-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import pi,cos,sin
    probes=[]
    def ray(name,x,z,mat,front):
        origin=[x,-.8,z];direction=[0,1,0];hit=scene.ray(origin,direction,1.35)
        ok=(hit is not None and hit['material'] in mat and abs(hit['distance_m']-(.8+front))<.013) if mat else hit is None
        probes.append(dict(check=name,origin=origin,direction=direction,expected_materials=mat,expected_distance_m=None if not mat else .8+front,hit=hit,passed=ok))
    for i in range(32):
        t=pi*(i+.48)/32
        outer_x=(1.56+.244)*cos(t);outer_z=1.47+(1.23+.244)*sin(t)
        mould_x=(1.56+.145)*cos(t);mould_z=1.47+(1.23+.145)*sin(t)
        if i in (0,31):
            ray('Springer in front of the outer brick ring',outer_x,outer_z,['dark fired brick'],-.196)
            ray('Springer in front of the inner moulding',mould_x,mould_z,['dark fired brick'],-.155 if mould_z<1.537 else -.196)
        else:
            ray('Outer arch brick group',outer_x,outer_z,['grey voussoir' if (i//4)%2==0 else 'radial red brick'],-.064)
            ray('Projecting concentric moulding',mould_x,mould_z,['dark fired brick'],-.105)
    for t in (1.42,1.48,1.55,1.61,1.69):
        origin=[(1.56+.379)*cos(t),-.8,1.47+(1.23+.379)*sin(t)];hit=scene.ray(origin,[0,1,0],1.35)
        probes.append(dict(check='Masonry immediately above arch',origin=origin,hit=hit,passed=bool(hit and hit['material'] in ('dark grey brick','grey stretcher','pointing'))))
    ray('Glazing above the meeting stile',0,2.20,['grey pane'],.152)
    for s in (-1,1):
        for x in (.189,.339,.49,.639):
            for z in (1.030,1.208,1.594,1.839):ray('Thin vertical guard on paired casements',s*x,z,['red painted bars'],-.01)
        for x in (.111,.258,.413,.57):
            ray('Glass behind open guard',s*x,1.20,['grey pane','pale pane'],.151)
            ray('Crossbar forward of glass',s*x,1.404,['red painted bars'],-.026)
        for z in (1.276,1.682):ray('Transom in outer sidelight',s*1.110,z,['rust red joinery'],.059)
        for z in (1.088,1.465,1.796):ray('Outer lit pane',s*1.11,z,['grey pane','pale pane'],.151)
    for x in (-1.57,-.362,-.267,.267,.362,1.57):
        ray('Structural divisions of the pierced skirt',x,.655,['rust red joinery'],-.080)
    for x in (-1.48,-.93,-.45,.085,.46,1.03,1.49):
        ray('Shadow through open scrollwork above the curls',x,.655,[],0)
        ray('Upper horizontal ledge of the skirt',x,.785,['rust red joinery'],-.082)
        ray('Pale lower sill edging',x,.175,['limestone edge'],-.20)
    for x in (-1.93,1.93):
        for z,depth in ((1.464,-.11),(1.505,-.155),(1.564,-.196)):
            ray('Stepped springer extension',x,z,['dark fired brick'],depth)
    return dict(passed=all(r['passed'] for r in probes),samples=probes)


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
