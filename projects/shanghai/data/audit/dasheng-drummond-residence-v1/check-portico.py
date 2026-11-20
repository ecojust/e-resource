"""Check actual first-hit surfaces, the three-part roof and the open depths of the garden galleries."""
from pathlib import Path
import argparse, hashlib, json, runpy

def check(scene):
    results=[]
    def sight(name,origin,direction,wanted,low,high):
        hit=scene.ray(origin,direction,25)
        if wanted:
            assert hit and hit['material'] in wanted and low<hit['distance_m']<high,(name,hit,low,high)
        else:
            assert hit is None,(name,hit)
        results.append({'part':name,'origin':origin,'direction':direction,'hit':hit})
    for x in [-2.40,2.40]:
        sight('recessed lower glass', [x,-3,3.28],[0,1,0],{'sash glazing','dark gallery timber'},5.63,5.82)
    for x in [-1.84,.10,1.98]:
        sight('upper glazed sash', [x,-3,6.77],[0,1,0],{'sash glazing'},5.735,5.82)
    for x in [-1.14,1.14]:
        sight('turned upper portico shaft',[x,-3,6.71],[0,1,0],{'moulded red stone'},5.20,5.30)
        sight('banded lower brick pier',[x,-3,3.28],[0,1,0],{'moulded red stone'},5.25,5.53)
    for x in [-2.17,-.25,1.64]:
        sight('opening through upper parapet',[x,-3,9.86],[0,1,0],set(),0,0)
    # Oblique camera alone can hide an erroneously placed third gable. Downward rays distinguish both gables and flat centre.
    for x in [-5.75,5.75]:
        for delta in [.14,.73,1.61]:
            expected=9.96-(9.96-7.95)*delta/(4.67/2+.18)+.12
            sight('sloped clay gable roof',[x+delta,4.27,15],[0,0,-1],{'red clay roof'},15-expected-.11,15-expected+.12)
    for x in [-2.08,.02,1.62]:
        sight('flat roof above central garden portico',[x,4.27,15],[0,0,-1],{'grey stone caps'},5.34,5.45)
    for x in [-5.75,5.75]:
        sight('recessed gallery door / upper level',[x+.075,-3,6.24],[0,1,0],{'sash glazing'},8.88,8.99)
        sight('recessed gallery door / lower level',[x+.075,-3,3.23],[0,1,0],{'sash glazing'},8.88,8.99)
        sight('gallery floor',[x+.71,4.55,5.70],[0,0,-1],{'gallery floor'},.38,.50)
        sight('basement window behind gallery',[x+.1,-3,.55],[0,1,0],{'dark gallery timber'},6.12,6.25)
        sight('infilled timber gable',[x+.46,-3,8.44],[0,1,0],{'white gable plaster'},5.88,5.98)
    for x in [-3.71,-1.68,1.68,3.71]:
        top=1.19 if abs(x)>3 else 2.70
        sight('round finials above square garden piers',[x,.29,top+1.4],[0,0,-1],{'ivory stone finials'},.80,1.07)
    for x in [-2.15,0,2.15]:
        sight('blind arch face in stair enclosure',[x,-3,.43],[0,1,0],{'red face brick'},3.40,3.47)
    for side in [-1,1]:
        for step in [1,3,6]:
            x=side*(3.23+(7-step)*.282)
            sight('ascending lateral stone stair',[x,1.3,2],[0,0,-1],{'grey stone caps'},
                  2-1.5*(step+1)/8-.024,2-1.5*(step+1)/8+.024)
    return results

def run():
    parser=argparse.ArgumentParser()
    for flag in ('project','manifest','decoded','out'):parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args();manifest=json.loads(a.manifest.read_bytes())
    helper=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    variants=[]
    for role in ['full','lod','raw']:
        rec=manifest['assets'][role];file=a.manifest.parent/rec['file']
        assert h(file)==rec['sha256']
        decoded=file if role=='raw' else a.decoded/(role+'.glb')
        scene=helper['SerialScene'](decoded);probes=check(scene)
        assert len(scene.tri)==rec['triangles']
        variants.append(dict(role=role,triangles=len(scene.tri),sha256=h(file),decoded_sha256=h(decoded),samples=probes))
    data=dict(id=manifest['id'],passed=True,manifest_sha256=h(a.manifest),script_sha256=h(Path(__file__)),
              count=sum(len(v['samples'])for v in variants),variants=variants)
    a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':run()
