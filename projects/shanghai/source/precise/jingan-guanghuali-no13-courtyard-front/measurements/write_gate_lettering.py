"""Draw the legible address as plain strokes normalized to the photographed green plate."""
from pathlib import Path
import json
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.affinity import affine_transform
# A ten-unit square for each character. Points are given as x/y decimal digits.
STROKES={
'巨':['11 81','12 18 88','13 72 75 15','16 76'],
'鹿':['41 52','13 83','13 17 08','24 74 76 26','43 46','63 66','27 29 49','27 47','67 59 79 89','68 87'],
'路':['12 42 45 15 12','25 28','16 18 48','36 46','62 52','62 82 75 57','52 84','56 86 89 59 56'],
'七':['15 84','41 48 59 78 88'],
'八':['42 35 17','61 65 88'],
'六':['41 52','13 83','45 27','65 88'],
'弄':['21 81','52 55','32 72','25 85','36 39','66 69','17 87']}
def line(points,size):
    return LineString(points).buffer(size,cap_style=2,join_style=2)
def contours(shape):
    shapes=[shape] if shape.geom_type=='Polygon' else shape.geoms
    def ring(r):return [[round(x,6),round(y,6)]for x,y in r.coords]
    return [dict(shell=ring(s.exterior),holes=[ring(h) for h in s.interiors]) for s in shapes]
def draw():
    letters={}
    forms={'1': [[(.305,.30),(.361,.197),(.403,.191),(.403,.616)],[(.332,.618),(.46,.618)]],
        '3': [[(.532,.255),(.541,.212),(.572,.182),(.609,.185),(.637,.210),(.651,.25),(.650,.331),(.640,.366),(.600,.396),(.634,.418),(.655,.454),(.657,.537),(.642,.589),(.611,.620),(.567,.626),(.536,.603),(.521,.559)]]}
    for char,paths in forms.items():
        letters[char]=contours(unary_union([line(p,.021 if char=='1' else .022) for p in paths]))
    for i,(char,paths) in enumerate(STROKES.items()):
        strokes=[line([(int(p[0]),int(p[1]))for p in row.split()],.46)for row in paths]
        shape=affine_transform(unary_union(strokes),[.013,0,0,.013,.070+i*.125,.753])
        letters[char]=contours(shape)
    return dict(inscription='13 巨鹿路七八六弄',method='Original stroke outlines. The two photographed plates establish the characters and arrangement. Mounting edges are estimated.',letters=letters)
if __name__=='__main__':
    Path(__file__).with_name('number-plate-letters.json').write_text(json.dumps(draw(),ensure_ascii=False,indent=1)+'\n')
