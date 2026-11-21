"""Ray-check the garland's carved field, twin sashes, recess and arched crown."""
from pathlib import Path
import os,runpy
from math import cos,sin,pi
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def front(name,x,z,materials,y0,y1):
        origin=[x,-.55,z];v=reader.ray(origin,[0,1,0],1.5)
        passed=bool(v and v['material']in materials and y0<=v['distance_m']-.55<=y1)
        rows.append(dict(part=name,origin=origin,material=materials,y_bounds=[y0,y1],hit=v,passed=passed))
    for x in [-.42,-.18,.18,.42]:
        for z in [1.122,1.49,1.89,2.28]:front('Sixteen glass lights',x,z,['smoky daylight glass','shaded daylight glass'],.145,.166)
    for x in [-.2885,.2885]:
        for z in [1.1,1.45,2.12,2.34]:front('Slender sash glazing bars',x,z,['dark window steel'],.094,.11)
    for z in [1.03,1.68,2.22]:front('Meeting stiles',0,z,['dark window steel'],.067,.08)
    for x in [-.58,-.3,0,.36,.58]:
        front('Full-width projected sill',x,.838,['pale cast stone'],-.12,-.09)
        front('Pale lintel under tympanum',x,2.65,['pale cast stone'],-.06,-.04)
        front('Stone arch bed',x,2.78,['worn limestone edge'],-.12,-.10)
    for x in [-.41,-.29,-.15,0,.15,.29,.41]:front('Carved festoon',x,.155+.218*(x/.455)**2,['carved floral stone','worn limestone edge'],-.14,-.086)
    for s in [-1,1]:
        front('Pendant ribbon tip',s*.455+.025,.228,['carved floral stone','worn limestone edge'],-.14,-.09)
        front('Apron ground beside rosette',s*.20,.424,['recessed apron field'],-.078,-.060)
        front('Springing end on square bracket',s*.672,2.42,['pale cast stone'],-.055,-.035)
    front('Apron floral boss',0,.374,['worn limestone edge'],-.133,-.118)
    for a in [.19*pi,.34*pi,.5*pi,.66*pi,.81*pi]:
        front('Segmental hood stone',.652*cos(a),2.807+.444*sin(a),['pale cast stone'],-.073,-.056)
    for x in [-.303,.303]:front('Recess beside volutes',x,3.041,['recessed apron field'],-.043,-.028)
    for x in [-.055,.055]:front('Lyre-like central casting',x,2.968,['worn limestone edge','pale cast stone'],-.075,-.043)
    front('Brick boundary mortar',-.802,.014,['grey pointing'],-.001,.001)
    for x in [-.82,.81]:
        for z in [.35,.67,1.09,1.48,2.0,2.67,3.04]:
            front('Retained local brick courses',x,z,['umber facing brick','red facing brick','violet brown brick','grey pointing'],-.008,.002)
    return dict(passed=all(x['passed']for x in rows),samples=rows)
