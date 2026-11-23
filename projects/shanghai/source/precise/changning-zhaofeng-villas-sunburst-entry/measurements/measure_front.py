"""Rectify the Changning district photograph, and trace the four metal characters from its measured face."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box
from shapely.ops import unary_union
HERE=Path(__file__).absolute().parent
# Coordinates in the 1000 by 701 inspection copy of the 1080 by 757 source.
# These four points are on the front arrises of the two horizontal strips. The
# initial wall uses an explicitly provisional width until the street stations are registered.
REFERENCE=[[483,262],[765,238],[780,350],[489,370]]
FACE=[[-1.10,2.35],[1.10,2.35],[1.10,1.52],[-1.10,1.52]]
def homography(a,b):
 rows=[]
 for (x,y),(u,v) in zip(a,b):
  rows.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
 _,_,vt=np.linalg.svd(rows);h=vt[-1].reshape(3,3);return h/h[2,2]
def point(h,uv):
 q=h@[*uv,1];return [round(float(k/q[2]),6)for k in q[:2]]
def trace(image,h):
 tones=np.asarray(image.convert('L'));glyphs=[]
 for word,(x0,y0,x1,y1) in zip('兆豐別墅',[(497,278,553,327),(566,264,627,325),(636,251,694,319),(704,246,764,312)]):
  # Threshold within four separate letter boxes. Connected components smaller than
  # a cast stroke are discarded. No photograph is mapped onto the model.
  patches=[]
  for y,line in enumerate(tones[y0:y1,x0:x1]<94):
   limits=np.flatnonzero(np.diff(np.r_[False,line,False]))
   for left,right in limits.reshape(-1,2):patches.append(box(x0+int(left),y0+y,x0+int(right),y0+y+1))
  ink=unary_union(patches);pieces=list(ink.geoms)if ink.geom_type=='MultiPolygon'else[ink];loops=[]
  for p in pieces:
   if p.area<3:continue
   p=p.simplify(.78,preserve_topology=True)
   loops.append([[point(h,q)for q in list(r.coords)[:-1]]for r in [p.exterior,*p.interiors]])
  glyphs.append(dict(character=word,loops=loops))
 return glyphs
def main():
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('photo',type=Path);cli.add_argument('output',type=Path)
 a=cli.parse_args();original=a.photo.read_bytes();h=homography(REFERENCE,FACE)
 with Image.open(a.photo)as photo:
  assert photo.size==(1080,757);frame=photo.resize((1000,701),Image.Resampling.LANCZOS);glyphs=trace(frame,h)
 sources={'title':'2021年5月长宁区公布的入口东墙近照','page':'https://www.shcn.gov.cn/col6991/20210506/871962.html','image':'https://cn.storage.shmedia.tech/9822b8b1f7a44038af885e39f3eb36d1.jpeg','bytes':len(original),'sha256':hashlib.sha256(original).hexdigest()}
 a.output.write_text(json.dumps(dict(source=sources,inspection_pixels=[1000,701],front_arrises_px=REFERENCE,conditional_front_xz=FACE,image_to_initial_xz=h.tolist(),scale_basis='初稿暂按两条腰线宽2.20米、间距0.83米放样，尚待两处街景站对定。',glyphs=glyphs),ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':main()
