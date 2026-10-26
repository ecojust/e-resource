#!/usr/bin/env python3
"""Optional source preparation; raw generation uses the committed outline JSON.

Reads the explicitly licensed Noto Sans CJK SC Bold glyph outlines and creates
only the museum sign's characters. No font installation or model generation.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from fontTools.ttLib import TTCollection
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon,mapping

HERE=Path(__file__).resolve().parent

class FlatPen(BasePen):
 def __init__(self,gs,em):super().__init__(gs);self.em=em;self.contours=[];self.current=[]
 def _moveTo(self,p):self.current=[np.asarray(p,float)]
 def _lineTo(self,p):self.current.append(np.asarray(p,float))
 def _curveToOne(self,a,b,c):
  p=self.current[-1];a=np.asarray(a);b=np.asarray(b);c=np.asarray(c)
  self.current.extend((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*c for t in np.linspace(0,1,13)[1:])
 def _qCurveToOne(self,a,b):
  p=self.current[-1];a=np.asarray(a);b=np.asarray(b)
  self.current.extend((1-t)**2*p+2*(1-t)*t*a+t*t*b for t in np.linspace(0,1,13)[1:])
 def _closePath(self):
  if len(self.current)>=3:self.contours.append([(float(x/self.em),float(y/self.em)) for x,y in self.current])
  self.current=[]
 def _endPath(self):self._closePath()

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'))
 a=ap.parse_args();f=TTCollection(a.font,lazy=True).fonts[2]
 assert f['name'].getDebugName(1)=='Noto Sans CJK SC'
 em=f['head'].unitsPerEm;gs=f.getGlyphSet();cmap=f.getBestCmap();glyphs={}
 for char in sorted(set('上海汽车博物馆SHANGHAI AUTO MUSEUM')):
  name=cmap[ord(char)];pen=FlatPen(gs,em);gs[name].draw(pen);geom=Polygon()
  for contour in pen.contours:
   q=Polygon(contour)
   if not q.is_valid:raise ValueError('Glyph contour invalid '+char)
   geom=geom.symmetric_difference(q)
  glyphs[char]={'advance_em':f['hmtx'].metrics[name][0]/em,'outline':mapping(geom.simplify(.0005,preserve_topology=True))}
 out={'schema':'museum-sign-vector-outlines-v1','display_name':'Museum Sign Outlines','source_family':f['name'].getDebugName(1),'source_style':f['name'].getDebugName(2),'source_font_sha256':hashlib.sha256(a.font.read_bytes()).hexdigest(),'copyright':f['name'].getDebugName(0),'license':'SIL Open Font License1.1','license_url':'https://openfontlicense.org/open-font-license-official-text/','source_url':'https://github.com/notofonts/noto-cjk','outline_transform':'Only requestedcharacters; emnormalized, quadratic/cubic segments flattened at12steps; not the museum proprietary typeface.','glyphs':glyphs}
 (HERE/'references'/'museum-sign-outlines.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
 print(json.dumps({'characters':len(glyphs),'bytes':(HERE/'references'/'museum-sign-outlines.json').stat().st_size,'model_generated':False}))

if __name__=='__main__':main()
