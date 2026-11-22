"""Outline the four independently positioned gilt characters using Noto Serif CJK SC."""
from pathlib import Path
from fontTools.ttLib import TTCollection
from fontTools.pens.basePen import BasePen
import numpy as np,json
from shapely.geometry import Polygon,GeometryCollection,mapping
class Outline(BasePen):
 def __init__(self,glyphs):super().__init__(glyphs);self.rings=[]
 def _moveTo(self,p):self.rings.append([p])
 def _lineTo(self,p):self.rings[-1].append(p)
 def _curveToOne(self,a,b,c):
  p=np.asarray(self.rings[-1][-1]);a,b,c=map(np.asarray,(a,b,c))
  for t in np.linspace(0,1,9)[1:]:self.rings[-1].append(tuple((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*c))
 def _qCurveToOne(self,a,b):
  p=np.asarray(self.rings[-1][-1]);a,b=map(np.asarray,(a,b))
  for t in np.linspace(0,1,7)[1:]:self.rings[-1].append(tuple((1-t)**2*p+2*t*(1-t)*a+t*t*b))
 def _closePath(self):pass
 def _endPath(self):pass
fonts=TTCollection('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',lazy=True)
font=next(f for f in fonts.fonts if 'SC' in (f['name'].getDebugName(1) or ''));g=font.getGlyphSet();cm=font.getBestCmap()
shapes={}
for ch in '园花业宏':
 pen=Outline(g);g[cm[ord(ch)]].draw(pen);result=GeometryCollection()
 for ring in pen.rings:
  if len(ring)>2:result=result.symmetric_difference(Polygon(ring).buffer(0))
 shapes[ch]=mapping(result.simplify(1.2,preserve_topology=True))
Path(__file__).with_name('gilt-outlines.json').write_text(json.dumps(shapes,ensure_ascii=False,separators=(',',':')))
