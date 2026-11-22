"""Check the three real arch openings, projecting cornice, shuttered windows, ochre reliefs and roof."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-shi-liangcai-residence-carriage-porch'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def cast(label,start,direction,maxlen,materials,interval):
        hit=scene.ray(start,direction,maxlen)
        if materials:
            ok=bool(hit and hit['material'] in materials and interval[0] <= hit['distance_m'] <= interval[1])
        else:
            ok=hit is None
        samples.append(dict(check=label,start=start,direction=direction,maxlen=maxlen,
                            expected_materials=materials,expected_distance_m=interval,actual=hit,passed=ok))
    for side in [-1,1]:
        for y in [-2.67,-1.91,-1.23]:
            for z in [.49,1.52,2.37,2.91]:
                cast('side-to-side unobstructed drive', [side*3.2,y,z],[-side,0,0],6.4,[],[0,0])
        for y in [-3.73,-.15]:
            for z in [.45,1.43,1.94]:
                cast('standing side pier',[side*3.2,y,z],[-side,0,0],1.1,['warm lime render'],[.77,.79])
        for y in [-2.96,-.94]:
            for z in [4.73,6.08,7.33]:
                cast('upper side wall',[side*3.2,y,z],[-side,0,0],1.1,['warm lime render','recessed joint'],[.77,.79])
        for z,mat,dist in [(7.69,'dark drip edge',.685),(7.81,'red roof fascia',.725),(7.97,'pale carved stucco',.68)]:
            cast('vertical order of red parapet and cap',[side*3.2,-2.48,z],[-side,0,0],1.1,[mat],[dist-.008,dist+.008])
    for x in [-.89,-.35,.33,.94]:
        for z in [.41,1.2,2.03,2.93]:
            cast('front opening to depth of the porch',[x,-5.4,z],[0,1,0],4.65,[],[0,0])
    for x in [-2.17,2.16]:
        for z in [.41,1.35,1.86]:
            cast('frontal square piers',[x,-5.4,z],[0,1,0],2.6,['warm lime render'],[1.51,1.55])
    for x in [-.61,.23,.65]:
        for z in [5.15,5.47,6.16,6.64,6.98]:
            cast('closed front louvres and shutter backing',[x,-5.4,z],[0,1,0],2,['louvre shadow','mahogany window wood'],[.87,1.16])
    for y in [-2.34,-1.54]:
        for z in [5.17,5.49,6.32,6.81]:
            cast('open south window with recessed glasses',[-3.2,y,z],[1,0,0],1.2,['aged window glass','mahogany window wood'],[.855,1.04])
    for x in [-.44,.39]:
        for z in [4.36,4.54,4.70]:
            cast('ochre relief on the bowed upper front',[x,-5.4,z],[0,1,0],2,['ochre relief ground','gilt ochre ornament','pale carved stucco'],[.746,.86])
    for xy in [(-1.32,-2.4),(0,-1.79),(1.37,-1.09)]:
        cast('roof above all arch openings',[*xy,8.45],[0,0,-1],.8,['terrace roof finish'],[.43,.45])
        cast('open passage has actual paving',[*xy,1],[0,0,-1],1.3,['sandstone paving'],[.963,.975])
    for start in [(-2.81,-2.5,8.5),(2.82,-.35,8.5),(0,-5.12,8.5),(0,.62,8.5)]:
        cast('adjoining house is outside the independent model',start,[0,0,-1],9,[],[0,0])
    return dict(passed=all(s['passed']for s in samples),samples=samples)

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
