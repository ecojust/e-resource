from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-wuyuan-314-welfare-house-lion-portico'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def measure(label,origin,direction,maximum,materials,distance):
        hit=scene.ray(origin,direction,maximum)
        ok=hit is None if not materials else bool(hit and hit['material'] in materials and distance[0]<=hit['distance_m']<=distance[1])
        rows.append(dict(check=label,origin=origin,direction=direction,materials=materials,distance=distance,hit=hit,passed=ok))
    def garden(label,x,z,mat,dist):
        measure(label,[x,-1,z],[0,1,0],5.2,[mat],dist)
    for x in (-1.2975,-.4325,.4325,1.2975):
        garden('recessed solid oak field',x,.82,'recessed oak',[4.02,4.08])
        garden('oak lower glazing rail',x,1.44,'stained oak',[4.03,4.09])
        for dz in (1.62,2.18,2.65,2.76):
            garden('glazing behind decorated ironwork',x+.14,dz,'door glass',[4.11,4.16])
        garden('short stepped grille in leaf',x+.291,2.03,'glazing grille',[4.04,4.10])
    for x in (-.865,0,.865):
        garden('timber door stile at glazing plane',x,1.75,'stained oak',[4.02,4.08])
    for x in (-1.12,-.62,.62,1.12):
        garden('transom rail below arched fanlight',x,2.47,'stained oak',[4.01,4.08])
    for sign in (-1,1):
        for z in (.65,1.86,2.72):
            garden('receding daylight arch fillisters',sign*1.959,z,'pale stone trim',[.955,.975])
            garden('middle pale arch fillet',sign*2.00,z,'pale stone trim',[.913,.941])
        garden('sunken post shaft',sign*2.40,1.475,'pale stone trim',[.51,.58])
        garden('lantern glazing',sign*2.40,3.56,'translucent lamp',[.55,.65])
        garden('dark lantern cap',sign*2.40,3.735,'bronze fitting',[.52,.62])
        for dx in (-.045,.045):
            measure('stone lion muzzle',[sign*2.03+dx,.90,.967],[0,1,0],1.8,['lion limestone'],[.75,.83])
            measure('stone base under carved lion',[sign*2.03+dx,.90,.253],[0,1,0],1.8,['lion limestone'],[.89,.95])
        garden('raked shoulder of stone arch',sign*1.34,3.653,'pale stone trim',[.875,.975])
    for x,y in ((-.37,.64),(.56,1.54),(-1.28,2.05),(1.18,1.74)):
        measure('individual stone paving slab',[x,y,2.10],[0,0,-1],2.30,['paving slab'],[2.085,2.110])
        measure('soffit above deep open portico',[x,y,2.10],[0,0,1],2.35,['soffit plaster'],[1.96,2.04])
    # Horizontal cross-sections at eye height establish that both lateral
    # openings are clear from the garden path to the reception threshold.
    for z in (1.36,1.99,2.48):
        measure('passage across both side arches',[-3.55,1.51,z],[1,0,0],7.1,[],[])
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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
