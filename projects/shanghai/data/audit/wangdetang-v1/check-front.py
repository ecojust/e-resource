"""Check both curved gables, the central porch, stair void, south fanlight and balcony."""
from pathlib import Path
import argparse, hashlib, json, runpy

def check(scene):
    results=[]
    scales=(12.5463/20.768,.90,.89)
    def trace(name,origin,direction,length,allowed,low,high):
        origin=[o*scale for o,scale in zip(origin,scales)]
        unit=scales[next(i for i,k in enumerate(direction)if k)]
        low,high,length=low*unit,high*unit,length*unit
        hit=scene.ray(origin,direction,length)
        if allowed is None:
            assert hit is None,(name,hit)
        else:
            assert hit and hit['material'] in allowed and low<hit['distance_m']<high,(name,origin,hit,(low,high))
        results.append(dict(part=name,origin=origin,direction=direction,hit=hit))
    def south(name,x,z,d,mats):
        trace(name,[x,-5,z],[0,1,0],25,mats,d-.08,d+.08)
    wall={'rough ivory render'};glass={'sage window glass'};stone={'relief mortar'}
    for x in (-8.05,-4.32,4.32,8.05):
        south('ground sash glass',x+.13,1.49,5.225,glass)
        south('ground sash mullion',x,1.49,5.12,{'green window joinery'})
        south('curving ground-window hood',x+.08,4.11,4.905,stone)
    for x in (-8.38,-5.26,-2.20,3.73):
        south('upper sash glazing',x+.13,6.50,5.225,glass)
    south('porch back leaf after the deep reveal',.21,2.25,6.53,{'green window joinery'})
    south('central arch dressed stone',1.56,3.42,4.847,{'pink beige porch stone'})
    # First surfaces at the crown and haunches must be inside the portal reveal.
    for x,z in ((0,5.08),(-.68,4.93),(.68,4.93)):
        south('unobstructed upper curve of arched door',x,z,6.57,{'porch shade'})
    for x in (-1.12,0,1.12):
        trace('clear portico to the landing',[x,-1.89,2.15],[0,1,0],3.21,None,0,0)
    south('moulded plaque field',.36,5.90,4.973,stone)
    south('front upper gable backing',.11,11.99,5.98,{'porch shade'})
    south('front upper gable raised eye rim',(.38*.89/scales[0]+.055),11.91,5.68,stone)
    south('center of the upper recessed gallery glazing',7.94,6.61,6.675,glass)
    south('narrow balcony plate at upper gable',.13,8.53,4.475,{'stair terrazzo'})
    mid=(.17+7.08)/2
    for u,z,mats,offset in [(-1.61,2.45,{'blue fanlight glass'},.225),(1.26,6.13,glass,.225),(2.67,6.13,glass,.225),(.14,3.43,wall,.008)]:
        trace('south return fanlight and upper pair',[15,mid+u,z],[-1,0,0],9,mats,15-10.384+offset-.06,15-10.384+offset+.06)
    for y in (8.70,11.02,13.27):
        trace('southern road-facing upper window row',[15,y,6.52],[-1,0,0],8,glass,4.78,4.90)
    for y in (8.53,10.70,12.87):
        trace('south-side attic window row',[15,y,9.08],[-1,0,0],9,glass,5.47,5.57)
    for u in (-1.08,.12,1.31):
        trace('three arched lights below side gable oculus',[9,(.93+5.72)/2+u,9.70],[-1,0,0],8,glass,3.52,3.68)
    trace('side gable round opening',[9,(.93+5.72)/2+.11,11.99],[-1,0,0],6,{'porch shade'},3.55,3.70)
    for x,y,low,high,mats in [(0,-1.64,.14,.20,{'stair terrazzo'}),(0,-.42,.84,.91,{'stair terrazzo'}),(-6.13,2.19,8.95,9.31,{'baked roof tiles'})]:
        start=3.0 if y<0 else 20.0
        trace('stair and slope height',[x,y,start],[0,0,-1],start+.1,mats,start-high,start-low)
    for x,y in [(-8.2,-2.4),(4.43,7.0),(-11.1,2.22)]:
        trace('open ground outside bounded frontage',[x,y,17],[0,0,-1],17.2,None,0,0)
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
