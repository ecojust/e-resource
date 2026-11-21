"""Cast independent rays into the material spans, open-work grilles and tilting sash."""
import math
import numpy as np
from window_bay import WALL,LATTICE,FRAME,GLASS,DARK,HOLD,TILE,EAVES
def test(tri,names,hit):
    result=[]
    def front(label,x,z,expected):
        o=np.array([x,-2.0,z]);v=np.array([0.,1.,0.])
        found=hit(tri,names,o,v)
        actual=found[0] if found else None
        assert actual==expected,(label,x,z,actual,expected)
        result.append(dict(label=label,material=actual,point=found[1] if found else None))
    for x in [-1.205,1.205]:
        for z in [.76,2.66]:
            for dx,dz in ((0,0),(.218,.22),(.336,.11),(-.338,-.31),(0,.255)):
                front('Cast lattice solids',x+dx,z+dz,LATTICE)
            for dx,dz in ((.278,.10),(-.278,.18),(.07,.335),(.26,-.16)):
                front('See through grille',x+dx,z+dz,None)
    for x in (-.369,.369):
        for z in (.62,1.13,1.55,1.93,2.39):front('Fixed narrow sidelight',x,z,GLASS)
    for x in (-.28,.28):
        for z in (.62,1.22,1.55,2.02,2.43):front('Continuous side stile',x,z,FRAME)
    for z in (.818,1.395,1.708,2.271):
        for x in (-.367,0,.367):front('Full-width cross rail',x,z,FRAME)
    for z in (.65,1.52,2.40):front('Fixed central pane',.08,z,GLASS)
    for z in (1.20,2.12):front('Tilted central pane',.07,z,GLASS)
    for z in (.86,1.75):front('Aperture beneath tilted sash',.055,z,DARK)
    for z in (.29,2.78):front('Patterned cement header and sill',.115,z,HOLD)
    for x,z in ((-.61,1.02),(.61,2.32),(-1.70,.50),(1.67,2.4),(-1.02,1.75)):
        front('Cream plaster',x,z,WALL)
    front('Dark tile lip',.096,3.37,EAVES)
    front('Projected roof tile',.06,3.402,TILE)
    return result
