"""The two signs legible in the April 2020 street photographs."""
from pathlib import Path
from shapely import set_precision
from shapely.affinity import translate
from sign_lettering import lettering_shapes
from bank_fronts import GOLD,RED

FONT=Path(__file__).with_name('hengli-signs.otf')

def letter_signs(faces,lod):
    face=faces['Tianjin']
    for i,symbol in enumerate('汉庭连锁酒店'):
        item=lettering_shapes(symbol,.55,.64,font=FONT)[0][1]
        glyph=set_precision(translate(item.simplify(.006 if lod else .002),xoff=face.length/2-1.12,yoff=17.25-i*.870),.0004)
        face.prism(glyph,.205,.238,RED,'Red hotel sign letters')
    for _,item in lettering_shapes('南京东路幼儿园',1.60,.191,font=FONT):
        glyph=set_precision(translate(item.simplify(.0025 if lod else .0008),yoff=3.27),.00025)
        faces['Chamfer'].prism(glyph,-.135,-.127,GOLD,'Kindergarten door lettering')
