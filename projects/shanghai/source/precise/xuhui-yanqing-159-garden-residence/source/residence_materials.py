"""Exterior finishes read at 159 Yanqing Road."""
from garden_finishes import IVORY_RENDER, PEBBLEDASH, PALETTE as WALLS


def finish(rgb,roughness,metallic=0.):
    def linear(s):
        v=s/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return {'color':[linear(v) for v in rgb],'roughness':roughness,'metallic':metallic}


GREEN='159 | dark green painted shutter'
LIGHT='159 | pale steel joinery'
IRON='159 | charcoal rainwater iron'
GLASS='159 | dark steel-window glass'
SHADE='159 | depth of unobserved opening'
SILL='159 | weathered cement sill'
PLINTH='159 | warm grey plinth'
LEAD='159 | brown sheet-metal edging'
CLAY='159 | brown-grey roof tile'
PALETTE={**WALLS,GREEN:finish((57,74,63),.71),LIGHT:finish((181,183,163),.75),
         IRON:finish((56,56,49),.56,.18),GLASS:finish((66,81,78),.28,.12),
         SHADE:finish((47,44,39),.92),SILL:finish((166,158,139),.9),
         PLINTH:finish((161,153,132),.91),LEAD:finish((91,77,68),.67,.2),
         CLAY:finish((119,98,84),.92)}
