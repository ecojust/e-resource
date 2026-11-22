"""Generate original editable outlines for the museum's readable seven-character sign."""
import argparse
import json
from pathlib import Path
import numpy as np
from fontTools.ttLib import TTCollection
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection

class Outline(BasePen):
    def __init__(self,glyphs):super().__init__(glyphs);self.loops=[];self.current=[]
    def _moveTo(self,p):self.current=[p]
    def _lineTo(self,p):self.current.append(p)
    def _curveToOne(self,p1,p2,p3):
        p0=np.array(self.current[-1]);a,b,c=map(np.array,(p1,p2,p3))
        for t in [.25,.5,.75,1.]:
            u=1.-t;self.current.append(tuple(u**3*p0+3*t*u*u*a+3*t*t*u*b+t**3*c))
    def _qCurveToOne(self,p1,p2):
        p0=np.array(self.current[-1]);a,b=map(np.array,(p1,p2))
        for t in [.25,.5,.75,1.]:
            u=1.-t;self.current.append(tuple(u*u*p0+2*u*t*a+t*t*b))
    def _closePath(self):
        if len(self.current)>2:self.loops.append(self.current)
        self.current=[]
    _endPath=_closePath

def main(font,out):
    face=next(f for f in TTCollection(font).fonts if 'SC' in (f['name'].getDebugName(1)or''))
    glyphs=face.getGlyphSet();cmap=face.getBestCmap();data=[]
    for char in '上海民政博物馆':
        pen=Outline(glyphs);glyphs[cmap[ord(char)]].draw(pen);geom=GeometryCollection()
        for ring in pen.loops:geom=geom.symmetric_difference(Polygon(ring).buffer(0))
        x0,y0,x1,y1=geom.bounds
        def norm(line):return [[round((x-x0)/(x1-x0),5),round((y1-y)/(y1-y0),5)]for x,y in line.coords]
        area=geom.simplify(2.5,preserve_topology=True)
        regions=list(area.geoms)if isinstance(area,MultiPolygon)else[area]
        data.append(dict(char=char,shapes=[[norm(poly.exterior),*[norm(h)for h in poly.interiors]]for poly in regions]))
    r=dict(inscription='上海民政博物馆',scope='The archive photograph identifies the words, letter colour and panel. These explicitly labelled typeset outlines approximate the sign rather than copying the photographed calligraphy.',font_family=face['name'].getDebugName(1),font_license='SIL Open Font License 1.1',font_source='https://github.com/notofonts/noto-cjk',outline_coordinates='Normalised by glyph; u right and v down.',glyphs=data)
    out.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('font',type=Path);parser.add_argument('output',type=Path);a=parser.parse_args();main(a.font,a.output)
