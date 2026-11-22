"""Test the first surfaces of the street fabric, open office casements, steel grille and dormers."""
from pathlib import Path
import sys,json,runpy
import numpy as np
HERE=Path(__file__).absolute().parent
SRC=HERE.parents[2]/'source/precise/huangpu-marconi-beijing-east-131-front/source'
sys.path.insert(0,str(SRC))
from marconi_street_fabric import MATERIAL,WOOD,RED,GREY,BLUE,IRON,METAL,ROOF,PLASTER,GLASS,board
from marconi_photo_plane import CALIBRATION
from broad_office_sashes import layout
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
def probes():
 cases=[]
 def sight(name,origin,target,materials,tolerance):
  distance=np.linalg.norm(target-origin)
  cases.append(dict(name=name,origin=np.asarray(origin).tolist(),direction=((target-origin)/distance).tolist(),length=float(distance+tolerance+.05),allowed=materials,range_m=[float(distance-tolerance),float(distance+tolerance)]))
 P=np.array(CALIBRATION['camera_matrices']['2017_front']);eye=-np.linalg.solve(P[:,:3],P[:,3])
 # Fixed material samples from the rectification of the 2017 street photograph.
 for name,us,vs,front,materials,tol in [
    ('Visible grey brick beside upper bay',[298,305,315,323],[241,252,268,285,311],-.11,[MATERIAL],.20),
    ('Grey brick below high arch',[438,446,464,504,516],[509,515,520],0,[MATERIAL],.20),
    ('Red stripe across wide pier',[298,303,310,318],[474,476],-.131,[RED],.22),
    ('Red stripe in narrow main wall',[378,386,395,400],[475,478],-.027,[RED],.22),
    ('Tinted office panes, central broad bay',[108,137,172,187,225,248],[455,505,525],.74,[BLUE,WOOD],.60)]:
  for u in us:
   for v in vs:sight(f'{name} ({u},{v})',eye,board(u,v,front),materials,tol)
 # Rays across the digitally reconstructed leaf planes resolve three lights and two rails on each real leaf.
 for row in layout():
  dx,dy=row['direction'];x,y=row['hinge'];lo,hi=row['z'];w=row['width']
  for j,t in enumerate([1/6,1/3,1/2,2/3,5/6]):
   c=np.array([x+dx*w*.5,y+dy*w*.5,lo+(hi-lo)*t]);n=np.array([-dy,dx,0])
   sight(f"Broad bay {row['bay']} leaf {row['leaf']} sample {j+1}",c+.10*n,c,[GLASS] if j%2==0 else[WOOD],.047)
 # Free space in front of the photographed ground-level shop glazing.
 for x in np.arange(-15.55,-3.,.54):
  z=5.55;c=np.array([x,-.17,z]);sight(f'Lower street grille upright {x:.2f}',c+[0,-.7,0],c,[IRON],.035)
 return cases
if __name__=='__main__':
 rows={k:inspect(Path(v),probes()) for k,v in zip(('raw','full','lod'),sys.argv[1:4])}
 Path(sys.argv[4]).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 for k,d in rows.items(): print(k,len(d['cases']),[(v['name'],(v['first_hit']or{}).get('material'))for v in d['cases']if not v['passed']])
 sys.exit(int(any(not v['passed']for v in rows.values())))
