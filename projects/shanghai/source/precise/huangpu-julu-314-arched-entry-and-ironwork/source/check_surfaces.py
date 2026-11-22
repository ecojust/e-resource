"""Check the real gate leaves and curl hits, open space below the white arch and the stepped pier heads."""
from pathlib import Path
from math import sin,cos,pi
import os,runpy
from gable import IRON,BACK,STUCCO,CAP,TRIM,HALF,arch_point,scroll_points
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def watch(part,x,z,material):
        origin=[x,-1.,z];hit=reader.ray(origin,[0,1,0],1.55)
        ok=bool(hit and hit['material']==material) if material else hit is None
        samples.append(dict(part=part,origin=origin,direction=[0,1,0],expected_material=material,hit=hit,passed=ok))
    for x in (-.61,.61):
        for sx in (-1,1):
            for z,sz in ((.141,1),(1.98,-1)):
                # Evaluate the photographed spiral's cubic centreline at interior
                # parameters. Fine and distant chords use different tessellation.
                controls=(((0,0),(.015,.19),(.35,.34),(.367,.56)),
                          ((.367,.56),(.388,.81),(.128,.826),(.147,.674)),
                          ((.147,.674),(.151,.607),(.245,.604),(.257,.680)))
                for curve in controls:
                    for t in (.161,.387,.643,.871):
                        weights=((1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3)
                        xx=x+sx*sum(weight*vertex[0] for weight,vertex in zip(weights,curve))
                        zz=z+sz*sum(weight*vertex[1] for weight,vertex in zip(weights,curve))
                        watch('Centreline of photographed iron stem and spiral',xx,zz,IRON)
        for xx in [-.46,-.14,.14,.46]:
            watch('Red sheet behind open iron scrolls',x+xx,.102,BACK)
        for xx in [-.584,.584]:watch('Rectangular iron stile',x+xx,.95,IRON)
    for i in range(1,16):
        t=pi*i/16;x,z=arch_point(t);_,top=arch_point(t,True)
        watch('Arched head',x,(z+top)/2,STUCCO)
        watch('Open tympanum',x,z-.065,None)
    for x in [-(HALF+.252),HALF+.252]:
        for z,mat in [(.31,STUCCO),(1.9,STUCCO),(2.45,TRIM),(2.505,CAP),(3.5,STUCCO),(3.95,CAP),(4.07,CAP)]:
            watch('Pier bed, cornice and crown',x,z,mat)
    return dict(passed=all(s['passed'] for s in samples),samples=samples)
