"""OFL Thai bank lettering with frozen HarfBuzz mark positioning.

No runtime network/HarfBuzz dependency. Geometry uses the shipped subset and
frozen layout, including the below vowel U. Typeface is an approximation.
"""
from pathlib import Path
import hashlib,json
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon
from shapely import affinity,make_valid,set_precision
from shapely.ops import unary_union
from sign_lettering import OutlinePen
HERE=Path(__file__).resolve().parent

def add_thai_bank_sign(facade,u,z,width,height,low,high):
    evidence=json.loads((HERE/'thai-sign-layout.json').read_text())
    path=HERE/'fonts'/evidence['font'];assert hashlib.sha256(path.read_bytes()).hexdigest()==evidence['font_sha256']
    face=TTFont(path);glyphs=face.getGlyphSet();x=y=0;shapes=[]
    for item in evidence['glyph_layout']:
        pen=OutlinePen(glyphs);glyphs[item['glyph']].draw(pen);shape=Polygon()
        for points in pen.contours:
            contour=make_valid(Polygon(points))
            if contour.geom_type=='GeometryCollection':contour=unary_union([p for p in contour.geoms if p.geom_type in ('Polygon','MultiPolygon')])
            shape=shape.symmetric_difference(contour)
        if not shape.is_empty:shapes.append(affinity.translate(shape,xoff=x+item['x_offset'],yoff=y+item['y_offset']))
        x+=item['x_advance'];y+=item['y_advance']
    face.close();bounds=unary_union(shapes).bounds;cx=(bounds[0]+bounds[2])/2;cy=(bounds[1]+bounds[3])/2
    for i,p in enumerate(shapes):
        p=affinity.scale(affinity.translate(p,xoff=-cx,yoff=-cy),width/(bounds[2]-bounds[0]),height/(bounds[3]-bounds[1]),origin=(0,0))
        p=p.buffer(.0005,quad_segs=2).buffer(-.0005,quad_segs=2);p=set_precision(p,.00005).simplify(.00005,preserve_topology=True)
        facade.prism(affinity.translate(p,xoff=u,yoff=z),low,high,'sign gold',f'bank-Thai-sign/{i}')
    return {'text':evidence['text'],'font_sha256':evidence['font_sha256'],'font_license':'SIL OFL 1.1','layout_sha256':hashlib.sha256((HERE/'thai-sign-layout.json').read_bytes()).hexdigest(),'width_m':width,'height_m':height,'typeface_is_photo_traced':False,'mark_positioning':'frozen HarfBuzz layout, glyph outlines regenerated from the licensed font'}
