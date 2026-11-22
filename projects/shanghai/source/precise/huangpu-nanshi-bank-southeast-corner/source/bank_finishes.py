"""Materials as seen on the 2015 front photograph and the 2021 street surveys."""
def finish(rgb,roughness=.79,metallic=0.):
    srgb=[v/255 for v in rgb]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in srgb]
    return dict(color=linear,roughness=roughness,metallic=metallic)
WALL='Buff rendered masonry'
LIMESTONE='Pale upper render'
DEEP='Warm recessed stone'
PALE='Light weathered cornice'
JOINT='Shadow within rustication'
OCHRE='Muted ochre moulding'
GOLD='Gilt character face'
GOLD_EDGE='Warm bronze relief edge'
DARK_GOLD='Relief shadow'
IRON='Aged black balcony iron'
GLASS='Recessed green-grey glazing'
FRAME='Dark timber sash'
RED='Red street enclosure, January 2021'
PLINTH='Grey street plinth'
TOP='Weathered pavilion roof'
BLACK='Dark enamel monogram field'
PALETTE={WALL:finish((200,185,155)),LIMESTONE:finish((220,209,183)),DEEP:finish((151,133,105)),PALE:finish((225,213,185)),JOINT:finish((163,150,124)),OCHRE:finish((158,119,65),.73),GOLD:finish((231,182,66),.37,.39),GOLD_EDGE:finish((166,116,38),.41,.45),DARK_GOLD:finish((107,78,42),.58,.20),IRON:finish((52,50,45),.55,.46),GLASS:finish((65,77,73),.28,.22),FRAME:finish((68,63,49),.64),RED:finish((136,56,49),.89),PLINTH:finish((104,102,92)),TOP:finish((188,177,146)),BLACK:finish((47,44,43),.40,.2)}
