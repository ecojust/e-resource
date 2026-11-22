import numpy as np
from math import pi
from chapel_gable import *

def test(tri,names,hit):
    checked=[]
    def ray(label,x,z,expected):
        origin=np.array([x,-3.,z]); direction=np.array([0.,1.,0.])
        first=hit(tri,names,origin,direction); material=first[0] if first else None
        assert material in expected,(label,x,z,material,expected)
        checked.append(dict(label=label,origin=origin.tolist(),direction=direction.tolist(),material=material,point=first[1] if first else None))
    for i in range(24):
        angle=i*pi/12
        for rad,shift,mat,where in [(.70,.057,OLIVE,'Outer pane'),(.31,.087,TEAL,'Inner pane'),(.66,0,CAME,'Radial came'),(.965,.06,STONE,'Pale annulus'),(.833,.055,CAME,'Recessed glazing rebate')]:
            ray(where,*polar(rad,angle+shift),[mat])
    ray('Central roundel',0,CENTRE,[AMBER])
    for side in (-1,1):
        for i in range(14):
            mid=side*SPAN*(i+.5)/14; shoulder=top(mid)-.375
            ray('Arcade recess',mid,shoulder+.019,[WALL])
            ray('Arch head',mid,shoulder+.128,[SOFFIT])
            ray('Raking lip',mid,top(mid)-.055,[STONE])
            ray('Coping',mid,top(mid)+.014,[CAP])
        ray('Cut extent',side*(SPAN+.067),.3,[None])
    return checked
