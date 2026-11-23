"""Generate the numerically transcribed inscription. The modern typesetting is independent of the inscription's original calligraphy."""
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from pathlib import Path
import argparse
import json
class Outline(BasePen):
    def __init__(self,glyphset):super().__init__(glyphset);self.contours=[]
    def _moveTo(self,p):self.contours.append([list(p)])
    def _lineTo(self,p):self.contours[-1].append(list(p))
    def _curveToOne(self,a,b,c):
        p=self.contours[-1][-1]
        for j in range(1,6):
            t=j/5;z=1-t;self._lineTo([round(z**3*p[i]+3*z*z*t*a[i]+3*z*t*t*b[i]+t**3*c[i],2)for i in (0,1)])
    def _qCurveToOne(self,a,b):
        p=self.contours[-1][-1]
        for j in range(1,5):
            t=j/4;self._lineTo([round((1-t)**2*p[i]+2*(1-t)*t*a[i]+t*t*b[i],2)for i in (0,1)])
    def _closePath(self):pass
cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('font',type=Path);cli.add_argument('output',type=Path);args=cli.parse_args()
f=TTFont(args.font,fontNumber=2);gs=f.getGlyphSet();out={}
for char in sorted(set('712弄1–168号长宁路优秀历史建筑HERITAGE ARCHITECTURE')-{' '}):
    key=f.getBestCmap()[ord(char)];pen=Outline(gs);gs[key].draw(pen);out[char]=pen.contours
args.output.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
