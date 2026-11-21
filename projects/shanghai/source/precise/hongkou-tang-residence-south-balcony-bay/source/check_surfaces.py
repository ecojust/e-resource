"""Test the first material struck by rays sent towards the author's actual geometry."""
from pathlib import Path
import os,runpy
from tang_porch import STONE,MOLDING,IRON,WOOD,GLASS,HALF_BAY,balcony_front
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def probe(part,x,z,expected,near=None,far=None):
        hit=reader.ray([x,-2.,z],[0,1,0],3.5)
        passed=hit is None if expected is None else bool(hit and hit['material']==expected and near<=hit['distance_m']-2<=far)
        samples.append(dict(part=part,origin=[x,-2.,z],expected=expected,hit=hit,passed=passed))
    for x in (-HALF_BAY,HALF_BAY):
        for z in (.13,.215):probe('Square plinth',x,z,MOLDING,-.87,-.83)
        for z in (.275,.37,.515,.79,1.21,1.8,2.35,2.97,4.27,4.79,5.31,5.85,5.998):
            probe('Stone shaft and profile',x,z,STONE,-.84,-.639)
        for z in (6.07,6.18,6.30,6.37):probe('Capital or its inner stone bell',x,z,STONE,-.86,-.625)
        probe('Abacus square',x,6.442,STONE,-.80,-.74)
    for x in (-.53,0,.53):
        front=balcony_front(x)
        for z,depth,mat in [(3.25,.008,MOLDING),(3.29,.065,STONE),(3.348,.012,MOLDING),(3.397,.080,STONE)]:
            probe('Layer of curved balcony edge',x,z,mat,front-depth-.012,front-depth+.012)
        for z in (3.475,3.555,3.997,4.051):probe('Curved iron rail',x,z,IRON,front-.05,front+.03)
    for x in (-.825,.825):
        for z in (.61,1.29,2.32,4.39,5.56):probe('Timber upright',x,z,WOOD,.65,.75)
    for x in (-.42,.42):
        probe('Door lower wood panel',x,.65,WOOD,.66,.74)
        for z in (1.19,1.97,2.56,4.48,5.25,5.85):probe('Recessed glazing',x,z,GLASS,.72,.80)
    for z in (1.15,2.37,4.29,5.67):probe('Wall between the separate openings',0,z,'recessed red brown surround',.77,.83)
    for z,mat in [(6.60,STONE),(6.715,STONE),(6.804,MOLDING),(6.867,STONE)]:
        for x in (-.6,0,.6):probe('Upper entablature',x,z,mat,-.83,-.65)
    return dict(passed=all(r['passed']for r in samples),samples=samples)
