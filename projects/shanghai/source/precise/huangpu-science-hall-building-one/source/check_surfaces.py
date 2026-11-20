"""Test the five roof pavilions, segmental windows, clock, open terrace, wooden joinery and garden landings."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from math import sin,cos,pi,hypot
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-science-hall-building-one'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    import numpy as np
    def ray(label,o,v,mat,d,tolerance=.037):
        h=scene.ray(o,v,90)
        passed=(h is None)if mat is None else h is not None and h['material']==mat and abs(h['distance_m']-d)<tolerance
        rows.append(dict(label=label,origin=o,direction=v,expected_material=mat,expected_distance=d,actual=h,passed=passed))
    def front(label,x,z,mat,y):
        ray(label,[x,-3,z],[0,1,0],mat,None if y is None else y+3)
    glass='warm garden glazing';wood='dark brown timber';stone='ivory render'
    fields=[(-51.05,-42.90,'end'),(-42.90,-29.34,'range'),(-29.34,-19.93,'inner'),(-19.93,-6.06,'range'),(-6.06,6.06,'clock'),(6.06,19.93,'range'),(19.93,29.34,'inner'),(29.34,42.90,'range'),(42.90,51.05,'end')]
    for left,right,kind in fields:
        mid=(left+right)/2;length=right-left
        if kind=='range':
            for offset in [-length/3,0,length/3]:
                front('rounded upper French window',mid+offset+.27,7.54,glass,8.348)
                front('upper timber meeting stile',mid+offset,7.54,wood,8.216)
                front('broad ground glazing below gallery',mid+offset+.42,2.43,glass,8.418)
            front('dormer glass',mid,12.61,glass,8.269)
        elif kind=='clock':
            for offset in [-3.72,0,3.72]:
                front('three clock pavilion upper lights',mid+offset+.28,8.14,glass,7.228)
                front('three recessed garden door lights',mid+offset+.25,2.15,glass,7.618)
        else:
            wall=7.14 if kind=='inner'else 7.18
            for offset in [-.27*length,0,.27*length]:
                front('three glazing sections below single arc',mid+offset+.18,8.12,glass,wall+.278)
            front('timber door bottom panel',mid+.31,.49,wood,8.234)
            if kind=='end':
                front('circular attic vent',mid,12.76,glass,6.738)
    front('clock centre beyond terrace',.27,13.75,'cream clock face',6.48)
    front('upper left recessed pediment panel',-.83,15.23,wood,6.527)
    front('clock rim',.802,13.65,stone,6.401)
    front('clock crown cornice',.0,15.98,stone,6.36)
    for x in [-5.65,5.65]:
        front('separate square portico columns',x,2.23,stone,.105)
    for y,top in [(-.91,.095),(-.58,.19),(-.22,.29)]:
        ray('broad terrace stairs',[.23,y,3],[0,0,-1],'garden stair stone',3-top)
    for x in [-46.97,-24.635,0,24.635,46.97]:
        front('dark overhanging pavilion beam',x,11.30,wood,5.47)
    for left,right,kind in fields:
        x=(left+right)/2
        if kind=='range':
            y=6.84+(14.27-6.84)*.365;roof_z=11.36+(13.69-11.36)*.365;x+=2.12
        elif kind=='inner':
            y=5.48+(12.06-5.48)*.455;roof_z=11.50+(15.18-11.50)*.455;x+=1.05
        else:
            top=16.89 if kind=='clock'else 15.35
            y=6.78+(9.56-6.78)*.52;roof_z=12.42+(top-12.42)*.52;x+=1.03
        ray('clay tiled southern pitch of '+kind,[x,y,21],[0,0,-1],'red French clay tile',21-roof_z)
    front('upper open terrace handrail',2.12,6.38,stone,.045)
    ray('chimney shaft meets the garden roof just above the clay pitch',[-12.54,13.02,13.76],[0,1,0],'grey pebble dash',.425)
    ray('single pale chimney cap',[-12.51,13.82,22.0],[0,0,-1],stone,22.0-17.22)
    for x,y in [(-57,7),(57,7),(0,-3),(12,20)]:
        ray('garden, end additions or unmodeled rear remain empty',[x,y,22],[0,0,-1],None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(q['passed']for q in rows))

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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
