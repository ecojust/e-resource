"""Check surface material and distance at identifiable points on both window levels."""
from pathlib import Path
import runpy,os
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def test(name,x,z,y,mat):
        origin=[float(x),-1.5,float(z)];r=reader.ray(origin,[0,1,0],3.)
        samples.append(dict(part=name,origin=origin,material=mat,hit=r,passed=bool(r and r['material']==mat and abs(r['distance_m']-1.5-y)<.004)))
    for x in [C-.26,C,C+.26]:
        for z in [.37,1.2,2.62,3.76,4.14]:test('Pale pilaster',x,z,-.127,LIME)
    for z in [4.02,4.32,4.53,4.73,4.91]:
        for x in [X-.44,X+.44]:test('Recessed glass',x,z,.286,PANE)
        test('Sash stile',X,z,.198,SASH)
    for x in [X-.42,X+.42]:test('Window transom',x,4.62,.182,SASH)
    for x in [X-.07,X+.07]:
        for z in [1.84,2.11,2.26]:test('Hanging central stone',x,z,-.24,LIME)
        for z in [5.226,5.50,5.7]:test('Keystone over arch',x,z,-.212,LIME)
    for dx in [-.62,-.35,.35,.62]:test('Triangular moulding',X+dx,2.469-abs(dx)*.437,-.19,LIME)
    for k in range(12):
        x=X-.737+k*1.474/11
        if k in (4,7):
            test('Front scroll crossing a picket',x,3.535,-.193,RAIL)
            test('Exposed picket above the scroll',x,3.62,-.179,RAIL)
        else:test('Iron picket',x,3.535,-.179,RAIL)
    for x in [X-.5,X+.55,X+.72]:
        for z in [3.015,3.669,3.718]:test('Guard rail',x,z,-.191,RAIL)
    for a in np.linspace(0,2*pi,9,endpoint=False):test('Petal',C+.18*cos(a),5.11+.272*sin(a),-.202,PETAL)
    for z in [5.02,5.11,5.24]:test('Open oval field',C,z,-.127,LIME)
    for i,z in enumerate([4.60,4.52,4.445,4.382]):test('Pendant bead',C,z,-.195+i*.012,PETAL)
    for x in [-1.4,-.8,-.22,.42,.75,1.32]:test('Top coping',x,6.38,-.288,LIME)
    return dict(samples=samples,passed=all(x['passed']for x in samples))
