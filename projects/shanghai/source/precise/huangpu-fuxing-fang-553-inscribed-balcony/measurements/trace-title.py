"""Trace the painted panel from the 2015 freely licensed photograph, using the four inner moulding corners."""
from pathlib import Path
from PIL import Image, ImageFilter
import sys,json,hashlib,numpy as np
from shapely.geometry import box,mapping
from shapely import affinity
from shapely.ops import unary_union
orig=Path(sys.argv[1]);out=Path(sys.argv[2]);digest=hashlib.sha256(orig.read_bytes()).hexdigest()
assert digest=='e4433fd2cd315f27841e9b3c71f95a291b3dae7206943a949aec5dd0ee2bc642'
# These inner panel corners are in the full 3264 × 4912 source photo.
photo_points=[(1919,2547),(2124,2559),(2125,2654),(1919,2644)]
width,height=305,141;target=[(0,0),(width,0),(width,height),(0,height)]
A=[];B=[]
for (x,y),(u,v)in zip(target,photo_points):
 A.extend(([x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]));B.extend([u,v])
coef=np.linalg.solve(np.asarray(A,dtype=float),B)
im=Image.open(orig).convert('RGB').transform((width,height),Image.Transform.PERSPECTIVE,coef,resample=Image.Resampling.BICUBIC)
r, g, b = np.array(im, dtype='int16').transpose(2, 0, 1)
# Paint is both redder and darker than the stone between adjacent brush strokes.
# Combining these two independent differences excludes the red fringe at stroke gaps.
chroma = np.minimum(r-g, r-b+2).clip(0, 255).astype('uint8')
luma = .24*r + .61*g + .15*b
def neighbourhood(values):
 return np.asarray(Image.fromarray(values.astype('uint8')).filter(ImageFilter.GaussianBlur(1.5)), dtype='float32')
red = (chroma > 30) & (chroma + 3*(chroma-neighbourhood(chroma)) + 4*(neighbourhood(luma)-luma) > 54)
parts={}
for char,(a,c) in zip('復興坊',[(25,107),(107,186),(186,278)]):
 polygons=[]
 for j,row in enumerate(red):
  if not 21<j<125:continue
  edges=np.flatnonzero(np.diff(np.r_[False,row[a:c],False]))
  for start,stop in zip(edges[::2],edges[1::2]):polygons.append(box(start+a,-j-1,stop+a,-j))
 union=unary_union(polygons);sub=list(union.geoms) if union.geom_type=='MultiPolygon'else[union]
 union=unary_union([p for p in sub if p.area>3]).buffer(.28).buffer(-.28).simplify(.47,preserve_topology=True)
 face=affinity.scale(affinity.translate(union,xoff=-width/2,yoff=height/2),xfact=1.52/width,yfact=.74/height,origin=(0,0))
 parts[char]=mapping(face)
out.write_text(json.dumps(dict(register='復興坊',photo=digest,author='Livelikerw',photo_date='2015-01-27',license='CC BY-SA 4.0',url='https://commons.wikimedia.org/wiki/File:Fu-Xing_Fang_Shanghai.JPG',corners=photo_points,units='metres about front inscription panel centre',letters=parts),ensure_ascii=False,separators=(',',':'))+'\n')
