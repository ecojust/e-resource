"""Cast rays directly into the three serialized south fronts, in model metres."""
from pathlib import Path
import argparse, hashlib, json, runpy

def check(scene):
    rows=[]
    def ray(name,origin,direction,maximum,material=None,distance=None,tolerance=.035):
        hit=scene.ray(origin,direction,maximum)
        if material is None:
            assert hit is None,(name,origin,hit)
        else:
            assert hit and hit['material']==material and abs(hit['distance_m']-distance)<=tolerance,(name,origin,material,distance,hit)
        rows.append(dict(feature=name,origin_m=origin,direction=direction,maximum_distance_m=maximum,first_hit=hit))
    def front(name,x,z,y,material):
        ray(name,[x,-6.,z],[0,1,0],12.,material,6+y)
    def above(name,x,y,z,material):
        ray(name,[x,y,59.],[0,0,-1],59.,material,59-z)
    for side in (-1,1):
        for k in (0,3,7,12):
            z=8.28+3.57*k
            front('deep loggia glazing behind railing',side*3.0+.22,z+1.42,2.05,'gray garden glazing')
            front('balcony slab',side*3.0+.36,z+.034,-.98,'light vertical tower ribs')
            front('balcony upper handrail',side*3.0+.07,z+1.02,-.917,'bronze balcony rail')
            front('continuous outer blade',side*4.245,z+1.42,-.11,'light vertical tower ribs')
            front('taller inner blade',side*1.73,z+1.42,-.39,'light vertical tower ribs')
            front('small window on central axis',side*.56+.12,z+1.19,.25,'gray garden glazing')
        for x,height,width,depth in ((5.83,12,1.88,0),(9.08,11,2,0),(12.12,11,.77,0),(14.42,9,1.66,.50)):
            for k in (0,height-1):
                front('garden wing upper and lower windows',side*x+.16,8.28+3.57*k+1.28,depth+.25,'gray garden glazing')
            above('stepped wing roof',side*x,2.50,8.28+3.57*height+.365,'dark roof metal')
        for x,d in ((6.29,0.),(9.08,0.),(12.12,0.),(14.42,.50)):
            front('lower wing window alongside central black pavilion',side*x+.14,7.18,d+.25,'gray garden glazing')
        front('earthen water washed south spandrel',side*7.03,24.0,0,'warm water washed aggregate')
        front('pale outer wing',side*13.43,25.78,.50,'pale water washed aggregate')
    above('fifteen-storey central spine',0,2.1,55.835,'dark roof metal')
    for x,width in ((-4.15,1.55),(0.,3.35),(4.15,1.55)):
        # Upper solid timber rail and deeply panelled front lower leaf are independently visible.
        front('closed door rail at back of reveal',x+.18,3.38,.44,'warm entrance timber')
        panelx=x if x else -.83
        front('recessed timber panel',panelx,1.97,.342,'recessed timber panel')
        front('cut artificial stone portal jamb',x+width/2+.24,1.31,-.01,'cut artificial stone')
    for x in (-2.59,2.59):
        front('cut-metal and milk-glass vertical lamps',x,2.79,-.2675,'cut artificial stone')
    for x in (-3.9,-.6,.6,3.9):
        front('square window in the dark pavilion',x+.18,6.22,.25,'gray garden glazing')
    front('dark tile pier between the paired pavilion lights',.06,6.28,0,'black square ceramic')
    for side in (-1,1):
        for xx in (8.25,10.71):
            front('ground floor garden light in square tiled return',side*xx+.14,1.43,.25,'gray garden glazing')
    for x in (-10.0,10.0):
        front('shadow of black tile base',x+.05,1.45,0,'black square ceramic')
        front('light outer belt',x,6.46,-.335,'cut artificial stone')
    for x in (-3.57,0.,3.57):
        ray('open center and flanking slots above canopy',[x,-2.60,5.03],[0,1,0],1.90)
    for x in (-2.17,2.17):
        front('solid pier between the three screen openings',x,5.05,-1.31,'cut artificial stone')
    for x in (-3.36,-1.12,1.12,3.36):
        for y in (-.86,-2.18,-3.53):
            ray('three coffer rows across the projecting canopy',[x,y,1.55],[0,0,1],4.,'coffer shadow',4.435-1.55)
        ray('unobstructed head height under canopy',[x,-4.7,1.73],[0,1,0],4.44)
    for x in (-5.20,-1.9,2.75,5.72):
        front('pale garden fascia leads the darker coffer ceiling',x,4.47,-4.4,'cut artificial stone')
        origin=[x,-6.,4.47]
        recessed=scene.ray(origin,[0,1,0],6.,lambda name:name=='coffer shadow')
        assert recessed and abs(recessed['distance_m']-1.70)<.01,(x,recessed)
        rows.append(dict(feature='separate inner skin depth behind fascia',origin_m=origin,direction=[0,1,0],maximum_distance_m=6.,material_filter='coffer shadow',first_hit=recessed))
    for x in (-2.80,.56,2.80):
        ray('pale soffit outside the coffer',[x,-2.18,1.55],[0,0,1],4.,'cut artificial stone',4.235-1.55)
    for pt in ((0,-5.1),(16.12,1.5),(-16.12,1.6),(0,5.25)):
        ray('outside the limited garden front',[*pt,59.],[0,0,-1],59.)
    return rows

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
