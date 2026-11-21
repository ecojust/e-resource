"""Metre-scaled brick coordinates following Ningbo Road and the southeast chamfer."""
from math import hypot
BRICK = 'Strand cream and red diaper brick'
LENGTH = 20.8106033132
END = (23.9604657269, 3.2993118421)
CHAMFER = hypot(END[0]-LENGTH, END[1])
def brick_uv(label, vertex):
    x,y,z = vertex
    along = x
    if 'Chamfer' in label:
        along = LENGTH + ((x-LENGTH)*(END[0]-LENGTH)+y*END[1])/CHAMFER
    return ((along+.5)/27., (z+.20)/25.)
