from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-yuyuan-1039-iron-gate-crest'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def model_point(u,v):
        scale=.80+.20*(u-62)/692
        return [2.12*((u-62)/692)/scale,-.75,(533-86*((u-62)/692)-v)*.00315/scale]
    def direct(u,v,materials,label,flex=0):
        offsets=[(0,0)] if flex==0 else [(0,0),(-flex,0),(flex,0),(0,flex),(0,-flex)]
        rays=[]
        for a,b in offsets:
            ray=scene.ray(model_point(u+a,v+b),[0,1,0],1.3)
            rays.append(ray)
        if materials:ok=any(ray and ray['material']in materials for ray in rays)
        else:ok=all(ray is None for ray in rays)
        rows.append(dict(feature=label,photo_pixel=[u,v],origin=model_point(u,v),neighbourhood_px=flex,materials=materials,first_hits=rays,passed=ok))
    iron=['black flat-iron scroll','black leaf terminals','painted steel frame','weathered iron edge','rivet heads']
    centres=[(79,437),(151,456),(78,444),(102,513),(121,517),(169,476),(185,502),(277,342),(306,460),(205,414),(249,411),(289,395),(312,380),(211,464),(250,424),(267,461),(220,480),(245,447),(338,420),(349,337),(420,302),(414,345),(342,355),(376,322),(410,347),(338,426),(398,420),(383,415),(473,369),(485,283),(441,335),(384,417),(453,381),(490,360),(515,297),(540,321),(491,360),(530,348),(533,363),(638,317),(628,229),(573,250),(598,285),(556,355),(562,318),(643,327),(665,247),(723,212),(737,254),(645,315),(655,270),(650,311),(700,328),(225,354),(200,323),(249,292),(224,355),(267,324),(267,282),(262,337),(327,269),(393,174),(443,227),(390,262),(393,217),(429,249),(473,213),(468,228),(521,207),(506,165),(521,216),(545,158),(592,143),(533,194),(574,203),(552,153),(622,142),(679,105),(646,76),(601,142),(585,116),(648,139),(678,102),(714,56),(759,105),(678,110),(710,122)]
    centres.append((257,451))
    for u,v in centres:direct(u,v,iron,'flat-iron silhouette traced at a turn in the dated photograph',1)
    open_centres=[(234,400),(268,440),(366,370),(451,297),(520,316),(594,248),(716,225),(412,201),(694,88),(353,249),(545,178),(279,294)]
    for u,v in open_centres:direct(u,v,[],'clear view through the iron foliage')
    return dict(samples=rows,passed=all(v['passed']for v in rows))

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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
