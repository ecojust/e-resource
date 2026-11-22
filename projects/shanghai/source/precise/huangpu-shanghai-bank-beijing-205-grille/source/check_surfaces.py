"""Check the actual open slots on either side of each set of folded narrow bars."""
from pathlib import Path
import os,runpy
from gable import BANDS,CENTRES,GREEN,FRAME,GLASS,WOOD,STONE,TRIM
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def check_ray(part,x,z,valid):
        o=[x,-.76,z];hit=reader.ray(o,[0,1,0],1.35)
        samples.append(dict(part=part,origin=o,direction=[0,1,0],hit=hit,expected_materials=valid,passed=(hit['material'] in valid) if hit else (valid==[])))
    for lo,hi in BANDS:
        for x in CENTRES:
            for off in (-.078,-.038,.038,.078):
                check_ray('folded iron upright',x+off,(lo+hi)/2,[GREEN,FRAME])
            for off in (0,.058):
                check_ray('open space between folded bars',x+off,(lo+hi)/2,[])
            check_ray('return across one end of rectangle',x,hi-.014 if lo<1 else lo+.014,[GREEN])
    for x in (-.56,-.31,.12,.49):check_ray('middle plate',x,1.08,[GREEN])
    for i in range(8):
        x=-.704+i*1.408/8
        check_ray('transom bar',x,3.26,[WOOD]);check_ray('dark glass between two vertical bars',x+.083,3.26,[GLASS])
    for x in (-.866,.866):
        for z,mat in [(.2,TRIM),(.435,TRIM),(.9,STONE),(2.54,STONE)]:check_ray('outer jamb and moulded base',x,z,[mat])
    return dict(passed=all(s['passed'] for s in samples),samples=samples)
