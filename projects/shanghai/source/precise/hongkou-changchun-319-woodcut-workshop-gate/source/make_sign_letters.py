"""Create normalized solid letter outlines from an OFL font; no photograph is sampled."""
from pathlib import Path
import argparse,json
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely import Polygon,GeometryCollection,constrained_delaunay_triangles
class Lines(BasePen):
    def __init__(self,glyphs):
        super().__init__(glyphs);self.polys=[];self.line=[]
    def _moveTo(self,p):self.line=[p]
    def _lineTo(self,p):self.line.append(p)
    def _curveToOne(self,c1,c2,end):
        p0=np.asarray(self.line[-1]);a,b,c=map(np.asarray,(c1,c2,end))
        q=np.linspace(0,1,7)[1:,None];self.line.extend((1-q)**3*p0+3*(1-q)**2*q*a+3*(1-q)*q*q*b+q**3*c)
    def _qCurveToOne(self,c,end):
        p0=np.asarray(self.line[-1]);a,b=map(np.asarray,(c,end));q=np.linspace(0,1,5)[1:,None]
        self.line.extend((1-q)**2*p0+2*(1-q)*q*a+q*q*b)
    def _closePath(self):
        if len(self.line)>2:self.polys.append(Polygon(self.line).buffer(0))
    _endPath=_closePath
def export(font_path,out):
 font=TTFont(font_path,fontNumber=3);g=font.getGlyphSet();cmap=font.getBestCmap();result={}
 for c in sorted(set('木刻講習會优秀历史建筑木刻讲习所旧址HERITAGE ARCHITECTURE')):
  if c==' ':continue
  p=Lines(g);g[cmap[ord(c)]].draw(p);geom=GeometryCollection()
  for s in p.polys:geom=geom.symmetric_difference(s)
  geom=geom.simplify(3.0,preserve_topology=True)
  tris=list(constrained_delaunay_triangles(geom).geoms);xmin,ymin,xmax,ymax=geom.bounds
  vertices=[];idx={};faces=[]
  for tri in tris:
   f=[]
   for x,y in list(tri.exterior.coords)[:3]:
    key=(round((x-xmin)/(xmax-xmin),5),round((y-ymin)/(ymax-ymin),5))
    if key not in idx:idx[key]=len(vertices);vertices.append(key)
    f.append(idx[key])
   if len(set(f))==3:
    a,b,d=np.array([vertices[i] for i in f]);orientation=(b[0]-a[0])*(d[1]-a[1])-(b[1]-a[1])*(d[0]-a[0])
    if abs(orientation)>1e-12:faces.append(f if orientation>0 else f[::-1])
  result[c]={'v':vertices,'f':faces}
 out.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('font',type=Path);a.add_argument('output',type=Path);args=a.parse_args();export(args.font,args.output)
