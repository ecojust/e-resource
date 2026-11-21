"""Cast material and clearance rays through both mesh densities and the raw file."""
from pathlib import Path
import json,os,runpy
from shapely.geometry import shape
from dade_portal import *
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def probe(label,x,height,material,front,tol=.009):
        hit=reader.ray([float(x),-.80,float(height)],[0,1,0],2.0)
        passed=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-.8-front)<=tol)
        samples.append(dict(part=label,origin=[float(x),-.80,float(height)],expected=material,hit=hit,passed=passed))
    for side in (-1,1):
        x=side*1.77
        for height in (.25,.72,1.43,1.87,2.52,3.05):
            probe('Street pier course',x,height,WALL,-.003)
        for height in (.58,1.18,1.78,2.37,2.89):
            probe('Horizontal recessed bed joint',x,height,JOINT,.007)
        probe('Pale inner vertical return',side*1.36,.71,STONE,-.025)
        probe('1545 plaque green margin',side*1.589+.208,2.042,GREEN,-.032)
        for x,z,depth in [(1.29,2.202,-.073),(1.22,2.435,-.074),(1.084,2.476,-.080)]:
            probe('Shoulder projecting edge',side*x,z,STONE,depth)
        probe('Air below projecting console',side*1.04,2.385,None,0)
    for x in (-.81,0,.84):
        for z,front in [(2.507,-.087),(2.55,-.071),(2.62,-.038),(2.699,-.046),(3.19,-.058)]:
            probe('Lintel moulding',x,z,STONE,front)
    for x in (-1.205,-.968,.975,1.204):
        probe('Weathered nameboard around text',x,2.74,PANEL,-.026)
    for x in (-.08,.51,.97):
        for z in (.08,.86,1.61,2.06):
            probe('Clear passage',x,z,None,0)
    for i in range(1,8):
        x=-1.265+i*1.029/8
        probe('Recessed iron gate picket',x,1.42,IRON,.11+(x+1.265)*.17-.012)
        probe('Void between gate bars',x+.061,1.42,None,0)
    for r in json.loads(Path(__file__).with_name('letter-contours.json').read_bytes()):
        g=shape(r['geometry']);g=max(getattr(g,'geoms',[g]),key=lambda s:s.area)
        inset=g.buffer(-.0014);pt=(inset if not inset.is_empty else g).representative_point()
        probe(r['group'],pt.x,pt.y,r['material'],r['front'],.003)
    return dict(samples=samples,passed=all(x['passed']for x in samples))
