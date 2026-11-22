"""Planar coordinates for the rendered panel and the grain of the hanging timber sign."""
WOOD='Weathered oval timber'
PANEL='Grey rendered plaque panel'

def texture_coordinates(material,position,label=None):
    x,y,z=position
    if material==WOOD:
        return (x+.74)/1.58,(z-3.075)/.43
    if material==PANEL:
        return (x+4.49)/2.39,(z-1.56)/.77
    raise ValueError(material)
