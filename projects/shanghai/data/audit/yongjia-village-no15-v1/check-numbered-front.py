"""Check the actual house-number plaque, arched porch, perforated concrete wall and east gable."""
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
    # The three upper window groups and three lower window recesses must survive both exports.
    for x in [-2.01,.15,2.94]:
        sight('upper red sash, recessed panes',[x+.12,-3,4.53],[0,1,0],{'recessed glass'},3.12,3.16)
    for x in [-1.86,.15,2.94]:
        sight('lower recessed window',[x+.055,-3,1.61],[0,1,0],{'recessed glass','dark iron','wine sash'},2.92,3.16)
    # The porch is physically open on two sides, with its doors against the house behind it.
    for x in [-4.02,-3.06]:
        sight('open garden-side arch reaches a door',[x,-2.05,1.27],[0,1,0],{'dark door','timber eaves'},2.16,2.29)
    sight('solid central porch pier',[-3.54,-2.05,1.33],[0,1,0],{'ivory roughcast'},.64,.71)
    sight('east arch opening reaches the west reveal',[-2.1,-.64,1.0],[-1,0,0],set(),0,0)
    sight('enamel plate faces east',[-2.08,-1.207,1.858],[-1,0,0],{'green enamel'},.30,.39)
    sight('numbered street sign has raised strokes',[-2.08,-1.207-.067,1.792],[-1,0,0],{'ivory numerals'},.30,.39)
    # Vertical cement fields have true voids. Rays through them go far enough to reach the house front.
    for i in [1,3,5,7,9,11,13]:
        x=-4.65+(i+.5)*9.05/14
        for z in [.504,.975]:
            hit=scene.ray([x,-4,z],[0,1,0],1.30)
            assert hit is None,('fence aperture',i,z,hit)
            results.append(dict(part='through octagonal fence cell',origin=[x,-4,z],direction=[0,1,0],clear_m=1.30))
        sight('cap bridges fence opening',[x,-4,1.267],[0,1,0],{'weathered concrete'},.99,1.05)
        sight('base below perforated screen',[x,-4,.10],[0,1,0],{'red oxide base'},1.03,1.07)
    for y,minimum in [(.90,6.5),(1.4,6.65),(2.27,6.44),(3.07,6.72)]:
        h=scene.ray([4.50,y,9.5],[0,0,-1],4.5)
        assert h and h['material']=='ivory roughcast' and h['point_enu_m'][2]>minimum, ('undulating gable',y,h)
        results.append(dict(part='shaped east gable top',position=[4.50,y],hit=h))
    for x in [-4.28,-2.81]:
        sight('porch tiled roof covers both pitches',[x,-.72,6.50],[0,0,-1],{'grey porch tile'},3.57,3.98)
    sight('east return corner is a real wall',[7.5,.55,3.07],[-1,0,0],{'ivory roughcast'},2.83,2.88)
    sight('inside of returned garden fence',[6.20,-1.05,1.27],[-1,0,0],{'weathered concrete'},1.64,1.74)
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
