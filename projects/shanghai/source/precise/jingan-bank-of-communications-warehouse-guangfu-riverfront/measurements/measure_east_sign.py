"""Record illuminated Chinese strokes in native plate 19 and size the documented secondary inscription."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from shapely import make_valid
import argparse
import cv2
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("plate19", type=Path, help="Original, uncropped 711 × 533 east-wall photograph")
parser.add_argument("output", type=Path)
args=parser.parse_args()
S=Path(__file__).resolve().parents[1]
outpath=args.output
j=json.loads((S/'measurements/east-return-sign-registration.json').read_bytes());g=j['metric_sample_grid'];L=g['bbox_s0_z0_s1_z1'];pp=g['pixels_per_m'];ww,hh=g['resolution']
xx,yy=np.meshgrid(L[0]+(np.arange(ww)+.5)/pp,L[3]-(np.arange(hh)+.5)/pp)
coords=np.stack([xx,yy,xx*0+1],axis=2)@np.array(j['front19_plane_to_image']).T
photo=np.asarray(Image.open(args.plate19).convert('RGB'));v=cv2.remap(photo,(coords[:,:,:2]/coords[:,:,2:]).astype('f'),None,cv2.INTER_CUBIC).astype(float)
r,gr,b=v.transpose(2,0,1)
def world(u,v):return [round(L[0]+u/pp,5),round(L[3]-v/pp,5)]
def ranges(box):
 a,b,c,d=box;return [*world(a,d),*world(c,b)]
top=[('BAIspace',[9,8,365,127]),('百',[377,9,449,113]),('空',[452,8,526,111]),('间',[530,11,605,113])]
lower=[('光',[12,144,92,238]),('二',[96,155,183,232]),('仓',[188,136,276,238]),('库',[278,140,373,240])]
out={'top':[dict(text=n,bbox_s0_z0_s1_z1=ranges(box))for n,box in top],'bottom':[]}
for char,box in lower:
 x0,y0,x1,y1=box;mask=(r-b>37)&(gr-b>19)&(r>151)
 if char=='库':mask|=(b>151)&(b-r>11)&(gr>115)
 cut=cv2.morphologyEx(mask[y0:y1,x0:x1].astype('uint8'),cv2.MORPH_OPEN,np.ones((3,3),'uint8'))
 cs,tree=cv2.findContours(cut,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE);polys=[]
 def contour(i):return [world(x0+x,y0+y)for x,y in cv2.approxPolyDP(cs[i],1.0,True).reshape(-1,2)]
 for i,c in enumerate(cs):
  if tree[0,i,3]>=0 or cv2.contourArea(c)<13:continue
  a=contour(i);holes=[];k=tree[0,i,2]
  while k>=0:
   h=contour(k)
   if len(h)>2 and cv2.contourArea(cs[k])>10:holes.append(h)
   k=tree[0,k,0]
  if len(a)<3:continue
  geo=make_valid(Polygon(a,holes))
  for part in ([geo]if geo.geom_type=='Polygon' else getattr(geo,'geoms',[])):
   if part.geom_type=='Polygon'and part.area>.0006:polys.append([np.asarray(part.exterior.coords)[:-1].tolist(),*[np.asarray(h.coords)[:-1].tolist()for h in part.interiors]])
 out['bottom'].append(dict(text=char,method='Visible illuminated strokes of plate 19',polygons=polys))
# Original stroke centre-lines for the unambiguous small Latin text and numerals.
paths={'E':[[(.90,.96),(.1,.96),(.1,.04),(.90,.04)],[(.1,.52),(.74,.52)]],'S':[[(.88,.86),(.69,.96),(.37,.95),(.16,.81),(.14,.65),(.27,.55),(.71,.46),(.87,.34),(.89,.22),(.73,.08),(.44,.04),(.12,.14)]],'T':[[(.06,.96),(.94,.96)],[(.5,.96),(.5,.04)]],'1':[[(.18,.76),(.53,.96),(.53,.04)],[(.2,.04),(.83,.04)]],'9':[[(.23,.08),(.51,.04),(.75,.18),(.85,.42),(.86,.74),(.74,.89),(.51,.96),(.30,.91),(.16,.77),(.15,.6),(.27,.47),(.47,.44),(.69,.49),(.84,.60)]],'3':[[(.10,.86),(.31,.96),(.63,.94),(.82,.83),(.84,.68),(.71,.57),(.48,.51),(.73,.46),(.87,.35),(.86,.21),(.70,.08),(.46,.04),(.12,.13)]]}
for word,box in [('EST',[382,160,465,228]),('1933',[480,160,605,228])]:
 x0,z0,x1,z1=ranges(box);spacing=(x1-x0)/len(word)
 for i,c in enumerate(word):
  geom=unary_union([LineString(path).buffer(.062,cap_style='square',join_style='round',quad_segs=3)for path in paths[c]])
  def pt(p):return [round(x0+spacing*(i+.03+p[0]*.92),5),round(z0+p[1]*(z1-z0),5)]
  polys=[[[pt(v)for v in np.asarray(sh.exterior.coords)[:-1]],*[[pt(v)for v in np.asarray(h.coords)[:-1]]for h in sh.interiors]]for sh in ([geom]if geom.geom_type=='Polygon'else geom.geoms)]
  out['bottom'].append(dict(text=c,method='Original stroke construction within measured character bounds',polygons=polys))
out['reading']='BAIspace 百空间 / 光二仓库 EST 1933';outpath.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
print(len(outpath.read_bytes()),[(a['text'],len(a['polygons']))for a in out['bottom']])
