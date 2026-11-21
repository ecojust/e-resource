from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-little-pearce-apartments-curved-cornice'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import sin,cos
    samples=[];r=7.4
    def shot(label,t,z,material,bounds):
        origin=[(r+1)*sin(t),r-(r+1)*cos(t),z];direction=[-sin(t),cos(t),0]
        hit=scene.ray(origin,direction,1.37)
        expect=[1-bounds[1],1-bounds[0]] if material else []
        ok=bool(hit and hit['material']in material and expect[0]<=hit['distance_m']<=expect[1]) if material else hit is None
        samples.append(dict(check=label,origin=origin,direction=direction,max_length=1.37,expected_materials=material,expected_distance=expect,hit=hit,passed=ok))
    for i in range(-26,27):
        t=i*.01515
        if abs(t)<.029:continue
        shot('Individual fine dentil front',t,.450,['dentil face'],[.138,.145])
        if -.026<t+.0070<-.019:
            shot('Exposed edge of centre scroll at the interruption in the fine dentil row',t+.0070,.445,['dentil face'],[.135,.162])
        else:
            shot('Open interval in the dentil course',t+.0070,.445,['shadowed stone'],[.044,.051])
    for i in (-5,-4,-3,-2,-1,1,2,3,4,5):
        t=i*.075
        shot('Front of main projecting square modillion',t,.762,['warm limestone'],[.302,.311])
        shot('Recessed space between square brackets',t+.032,.760,['shadowed stone'],[.083,.091])
    for t in (-.38,-.255,-.12,-.04,.035,.13,.25,.39):
        shot('Continuous overhanging cornice lip',t,.845,['top ledge'],[.355,.365])
        shot('Light upper wall fascia',t,1.27,['light render'],[.014,.022])
        shot('Lower moulded string course',t,.319,['warm limestone'],[.099,.113])
    for t in (-.016,0,.016):
        shot('Curled lower end of central corbel',t,.397,['shadowed stone'],[.098,.120])
        shot('Central scroll shoulder ahead of the bed',t,.738,['shadowed stone'],[.330,.348])
    for t in (-.022,.022):
        shot('Raised flanking strip of central scroll',t,.742,['dentil face'],[.346,.364])
    for t in (-.47,.47):shot('Beyond cropped arc',t,.73,[],[])
    return dict(samples=samples,passed=all(s['passed']for s in samples))


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
