"""Trace the gilded name as three separate planar shapes. No photograph enters the model."""
from pathlib import Path
from PIL import Image
from shapely.geometry import box,mapping
from shapely.affinity import scale,translate
from shapely.ops import unary_union
import json,numpy as np,hashlib
from argparse import ArgumentParser
from io import BytesIO
p=Path(__file__).resolve().parent
parser=ArgumentParser(description=__doc__);parser.add_argument('--original-photo',type=Path,required=True);parser.add_argument('--out',type=Path,default=p.parent/'source/named-letter-shapes.json');args=parser.parse_args()
raw=args.original_photo.read_bytes();assert hashlib.sha256(raw).hexdigest()==json.loads((p/'travel-4.json').read_bytes())['source_sha256']
copy=BytesIO();Image.open(BytesIO(raw)).convert('RGB').save(copy,'JPEG',quality=88);assert hashlib.sha256(copy.getvalue()).hexdigest()=='9428150a5190a92e9d639cf0980d12e06ff21accf7cf5158cf902341c74374e0'
im=np.array(Image.open(BytesIO(copy.getvalue())).convert('RGB')).astype(int)
red,green,blue=im.transpose(2,0,1);mask=(red>125)&(red-green>4)&(green-blue>9)&(red-blue>27)
out={}
for text,lo,hi,desired_w,desired_h in [('梅',95,165,.23,.237),('兰',188,258,.205,.192),('坊',302,385,.225,.235)]:
 x0,x1=215,285;shapes=[]
 for y in range(lo,hi):
  bits=mask[y,x0:x1];xs=np.flatnonzero(np.diff(np.r_[False,bits,False]))
  for xa,xb in zip(xs[::2],xs[1::2]):shapes.append(box(x0+xa,-y-1,x0+xb,-y))
 poly=unary_union(shapes);parts=[part for part in poly.geoms if part.area>7]if poly.geom_type=='MultiPolygon'else[poly];poly=unary_union(parts).buffer(.48).buffer(-.48).simplify(.58,preserve_topology=True)
 l,b,r,t=poly.bounds;shape=scale(translate(poly,-(l+r)/2,-(t+b)/2),xfact=desired_w/(r-l),yfact=desired_h/(t-b),origin=(0,0));out[text]=dict(pixel_bounds=[l,-t,r,-b],source_region=[x0,lo,x1,hi],geometry=mapping(shape))
dest=args.out;dest.write_text(json.dumps(dict(source='陆梁液，2024-10-21（原帖连同摄影权属见reference-review.json）',source_sha256=json.loads((p/'travel-4.json').read_bytes())['source_sha256'],note='原标识边缘按影像阈值追轮廓，归一到2020双站确定的深度平面；断开的笔画分组保留。',letters=out),ensure_ascii=False,separators=(',',':'))+'\n')
print({k:v['pixel_bounds']for k,v in out.items()})
