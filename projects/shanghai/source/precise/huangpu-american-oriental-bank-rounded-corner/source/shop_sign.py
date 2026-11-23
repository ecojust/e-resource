"""Model the three legible painted characters and the surviving strokes of the second."""
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.affinity import scale, translate
from street_finish import TIMBER, GOLD, JOINT, TRIM
# The coordinates follow the visible broad strokes of the small sign, not a typeface.
OLD=[[(.11,.76),(.85,.76)],[(.25,.94),(.33,.84)],[(.49,.93),(.49,.55)],[(.03,.55),(.88,.55)],[(.78,.87),(.62,.66),(.37,.45),(.04,.31)],[(.32,.39),(.32,.16),(.39,.10),(.73,.10),(.82,.14),(.84,.23)],[(.37,.29),(.72,.43)]]
MIDDLE=[[(.28,.78),(.35,.89),(.48,.88)],[(.22,.61),(.48,.79),(.64,.80),(.72,.75)],[(.66,.73),(.55,.59),(.34,.43),(.22,.42)],[(.49,.51),(.66,.57),(.77,.62)],[(.76,.50),(.72,.35),(.54,.22),(.42,.18),(.21,.16),(.09,.23)]]
FRAGRANT=[[(.16,.83),(.45,.86),(.76,.94)],[(.09,.69),(.91,.69)],[(.48,.85),(.48,.45)],[(.42,.67),(.26,.50),(.07,.42)],[(.56,.63),(.76,.48),(.91,.45)],[(.23,.42),(.77,.42),(.77,.09),(.23,.09),(.23,.42)],[(.27,.26),(.73,.26)]]

def sign(face,z,width,lod):
    height=width*.39
    face.box(0,z,width,height,.108,.108,TIMBER,'weathered orange board')
    for side in (-1,1):
        face.box(side*width*.45,z,width*.012,height*.74,.012,.169,GOLD,'board fastenings')
    glyph_width=width*.206
    for i,lines in enumerate([OLD,MIDDLE,OLD,FRAGRANT]):
        shape=unary_union([LineString(path).buffer(.047,quad_segs=2) for path in lines])
        shape=translate(scale(shape,xfact=glyph_width,yfact=height*.65,origin=(0,0)),xoff=width*(-.46+i*.232),yoff=z-height*.31)
        if not lod:face.prism(shape.buffer(.012,quad_segs=2),.164,.173,TRIM,'pale lettering edges')
        face.prism(shape,.172,.187,JOINT,'surviving sign strokes')

def side_shop_sign(face,z,width,lod):
    from pathlib import Path
    from sign_lettering import lettering_shapes
    from shapely import set_precision
    from shapely.affinity import translate
    from street_finish import STEEL
    face.box(0,z,width,.48,.14,.15,STEEL,'black Ningbo shop sign')
    face.box(-width*.40,z,.18,.18,.022,.231,TIMBER,'small shop emblem')
    for glyph,shape in lettering_shapes('老鸿兴',width*.64,.31,font=Path(__file__).with_name('shop-letters.otf')):
        # The small glyphs are simplified below a millimetre before extrusion.
        outline=set_precision(translate(shape.simplify(.0018 if lod else .0007),xoff=width*.08,yoff=z),.0004)
        face.prism(outline,.224,.239,TRIM,'Ningbo shop lettering')
