from pathlib import Path
from hashlib import sha256
import argparse,sys,runpy,json
import numpy as np
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--mesh',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--scale-xyz',type=float,nargs=3,default=(1.,1.,1.),metavar=('X','Y','Z'));opts=parser.parse_args()
scale=np.array(opts.scale_xyz,dtype=float);assert len(scale)==3 and (scale>0).all()
s=opts.source.resolve();project=s.parents[2]
sys.path.insert(0,str(s/'source'))
from street_materials import GLASS,STEEL,RED,SOLDIER,CREAM
cam=runpy.run_path(str(s/'measurements/register_street.py'))['Camera'](22.)
read=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
mesh=read(opts.mesh)
# Independent manual sampling on the common planar rectification. Corresponding
# ray origins are preserved without forcing sloping faces onto the reference wall.
picked=[
 ((128,266),(211,287),(147,423),(215,424),(145,370),(217,375),(143,535),(210,529)),
 ((327,271),(406,290),(348,432),(405,433),(345,372),(400,371),(342,528),(409,526)),
 ((672,265),(749,283),(688,423),(748,423),(695,367),(754,371),(693,529),(753,530)),
 ((929,263),(1004,290),(940,420),(1006,436),(941,374),(1001,380),(946,526),(1008,528))]
left=cam.wall((278,735))[0]-1
scale_x=1150/1559*65;scale_z=863/1170*65
results=[]
for i,marks in enumerate(picked,1):
 for k,(u,v) in enumerate(marks):
  wall=np.array([left+u/scale_x,0,18-v/scale_z])
  pixel=cam.pixel(wall);hit=mesh.ray(scale*cam.C,scale*(wall-cam.C),100)
  ideal=[GLASS,STEEL] if k<4 else [SOLDIER] if k<6 else [CREAM]
  results.append(dict(bay=i,region=('upper glazing','lower glazing','vertical brick spandrel','plaster panel')[k//2],rectified_pixel=[u,v],photo_1050=pixel.tolist(),photo_native=(pixel*[3968/1050,2976/788]).tolist(),expected=ideal,hit=hit,passed=hit is not None and hit['material']in ideal))
out=dict(asset_sha256=sha256(opts.mesh.read_bytes()).hexdigest(),camera_width_working_m=22,model_transformation_xyz=scale.tolist(),mode='fixed photograph pixels; clear glass and slender muntins grouped where the tree obscures a pane edge',samples=results,passed=sum(x['passed']for x in results),total=len(results))
opts.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(out['passed'],out['total'],[(v['bay'],v['region'],v['rectified_pixel'],v['hit']['material'] if v['hit']else None) for v in results if not v['passed']])
