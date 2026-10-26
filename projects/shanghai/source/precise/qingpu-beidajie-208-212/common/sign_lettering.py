"""Extrude licensed font outlines into real facade lettering.

The small OFL font subset travels with the source package. Typeface and depth
are approximations; callers must provide photograph-confirmed sign wording.
"""
from pathlib import Path
import hashlib
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon
from shapely import affinity, make_valid, set_precision

FONT = Path(__file__).parent / 'fonts' / 'BundSignSubset.otf'


class OutlinePen(BasePen):
    def __init__(self, glyph_set, steps=12):
        super().__init__(glyph_set)
        self.contours=[]; self.current=[]; self.steps=steps

    def _moveTo(self, p):
        self.current=[tuple(p)]

    def _lineTo(self, p):
        self.current.append(tuple(p))

    def _curveToOne(self, p1, p2, p3):
        p0=np.array(self.current[-1]);p1=np.array(p1);p2=np.array(p2);p3=np.array(p3)
        for t in np.linspace(0,1,self.steps+1)[1:]:
            self.current.append(tuple((1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3))

    def _qCurveToOne(self, p1, p2):
        p0=np.array(self.current[-1]);p1=np.array(p1);p2=np.array(p2)
        for t in np.linspace(0,1,self.steps+1)[1:]:
            self.current.append(tuple((1-t)**2*p0+2*(1-t)*t*p1+t*t*p2))

    def _closePath(self):
        if len(self.current)>=3:self.contours.append(self.current)
        self.current=[]

    def _endPath(self):
        self._closePath()


def lettering_shapes(text, width, height, *, font=FONT):
    """Return separate closed glyph polygons, centered on (0,0)."""
    if width<=0 or height<=0:raise ValueError('Positive sign dimensions required')
    face=TTFont(font);cmap=face.getBestCmap();glyphs=face.getGlyphSet();advance=0;shapes=[]
    for char in text:
        if ord(char) not in cmap:raise ValueError(f'Missing licensed glyph {char!r}')
        name=cmap[ord(char)];pen=OutlinePen(glyphs);glyphs[name].draw(pen);shape=Polygon()
        for points in pen.contours:
            contour=Polygon(points)
            # Font outlines can touch themselves at a stroke junction. Split
            # those exact intersections without smoothing/offsetting the font.
            if not contour.is_valid:contour=make_valid(contour)
            if contour.geom_type=='GeometryCollection':
                from shapely.ops import unary_union
                contour=unary_union([p for p in contour.geoms if p.geom_type in ('Polygon','MultiPolygon')])
            shape=shape.symmetric_difference(contour)
        if not shape.is_empty:shapes.append((char,affinity.translate(shape,xoff=advance)))
        advance+=face['hmtx'].metrics[name][0]
    face.close()
    if not shapes:raise ValueError('Sign has no visible glyphs')
    lowx=min(p.bounds[0] for _,p in shapes);lowy=min(p.bounds[1] for _,p in shapes)
    highx=max(p.bounds[2] for _,p in shapes);highy=max(p.bounds[3] for _,p in shapes)
    sx=width/(highx-lowx);sy=height/(highy-lowy)
    result=[]
    for char,p in shapes:
        p=affinity.scale(affinity.translate(p,xoff=-(lowx+highx)/2,yoff=-(lowy+highy)/2),sx,sy,origin=(0,0))
        # Resolve kissing stroke junctions into printable solids. The 0.5 mm
        # outline tolerance is far below the approximate sign dimensions.
        p=p.buffer(.0005,quad_segs=2).buffer(-.0005,quad_segs=2)
        p=set_precision(p,.00005).simplify(.00005,preserve_topology=True)
        result.append((char,p))
    return result


def add_facade_lettering(facade,text,u,z,width,height,low,high,material,*,label='photograph-sign',font=FONT):
    count=0
    for char,shape in lettering_shapes(text,width,height,font=font):
        facade.prism(affinity.translate(shape,xoff=u,yoff=z),low,high,material,f'{label}/{count}-{char}')
        count+=1
    return {'text':text,'glyph_count':count,'width_m':width,'height_m':height,
            'font_sha256':hashlib.sha256(Path(font).read_bytes()).hexdigest(),
            'typeface_is_photo_traced':False,'font_license':'SIL OFL 1.1'}
