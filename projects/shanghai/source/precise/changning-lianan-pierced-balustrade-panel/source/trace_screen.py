"""Rectify the published photograph and trace five unambiguously dark openings."""
from pathlib import Path
from hashlib import sha256
from itertools import groupby
import json,sys,numpy as np
from PIL import Image
from shapely.geometry import box
from shapely.ops import unary_union
from scipy.ndimage import label
r=Path(__file__).resolve().parent;raw=Path(sys.argv[1])
assert sha256(raw.read_bytes()).hexdigest()==json.loads((r.parent/'reference-photo-digest.json').read_bytes())['photo_sha256']
world=[[182,354],[213,346],[213,368],[182,381]];flat=[(0,0),(159,0),(159,105),(0,105)];matrix=[];v=[]
for (u,w),(x,y)in zip(flat,world):
 matrix.extend([[u,w,1,0,0,0,-u*x,-w*x],[0,0,0,u,w,1,-u*y,-w*y]]);v.extend([x,y])
im=Image.open(raw).transform((160,106),Image.Transform.PERSPECTIVE,tuple(np.linalg.solve(matrix,v)),Image.Resampling.BICUBIC).convert('L')
mask=np.array(im)<134;mask[:21]=0;mask[102:]=0;mask[:,:51]=0;mask[:,143:]=0
fields,total=label(mask);probes=[('Left upper leaf',67,44),('Right upper leaf',129,49),('Long central eye',99,63),('Left lower leaf',67,80),('Right lower leaf',128,85)]
polys={};pixels={};bounds=[]
def to_model(x,y):return [round((x-50)*.0068-.32,6),round((103-y)*.0068,6)]
for name,x,y in probes:
 val=fields[y,x];assert val
 yy,xx=np.where(fields==val);bars=[]
 for ky,series in groupby(zip(yy,xx),lambda a:a[0]):
  vals=[int(pt[1]) for pt in series]
  for _,run in groupby(enumerate(vals),lambda t:t[1]-t[0]):
   row=[q[1]for q in run];bars.append(box(row[0],int(ky),row[-1]+1,int(ky)+1))
 shape=unary_union(bars).buffer(.8).buffer(-.8).simplify(.85,preserve_topology=True);assert shape.is_valid
 polys[name]=[to_model(a,b)for a,b in list(shape.exterior.coords)[:-1]];pixels[name]=dict(original_control=[x,y],dark_pixels=len(xx),rectified_bounds=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())])
 assert all(len(value)>=6 for value in polys.values())
out=dict(photo_four_corners_px=world,rectified_view_px=[160,106],crop_bounds_xyxy=[50,21,144,103],trace_method='Five separate connected dark areas selected on the rectified image at luminance below 134. Original edge is subpixel and approximated.',column_scale_m_per_rectified_px=.0068,contributing_controls=pixels,outline_metres=polys)
(r/'pierced-pattern.json').write_text(json.dumps(out,indent=2)+'\n')
