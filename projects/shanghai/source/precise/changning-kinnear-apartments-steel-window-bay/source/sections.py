"""Trace the authored row, glazing bar, rebate, sill and brick positions in the delivered mesh."""
import numpy as np
from street_window import *

def test(tri,names,hit):
    rows=[]
    def probe(label,x,z,expected):
        origin=np.array([x,-2.0,z]);direction=np.array([0.,1.,0.]);q=hit(tri,names,origin,direction)
        actual=q[0] if q else None
        assert actual==expected,(label,x,z,actual,expected)
        rows.append(dict(label=label,material=actual,point=q[1] if q else None))
    for row in range(5):
        z=(TRANSOM+HEAD)/2 if row==4 else BASE+(row+.5)*(TRANSOM-BASE)/4
        for i in range(12):
            probe('Individual glazed light',OPEN_LEFT+(i+.5)*COLUMN,z,GLASS[(row//2+i//3)%3])
    for i in range(1,12):
        for z in (1.07,1.78):probe('Main and fine vertical steel bars',OPEN_LEFT+i*COLUMN,z,STEEL)
    for n in range(1,4):
        for i in range(4):probe('Horizontal sash bar',OPEN_LEFT+(3*i+1.5)*COLUMN,BASE+n*(TRANSOM-BASE)/4,STEEL)
    for i in range(4):probe('Transom hand junction',OPEN_LEFT+(3*i+.5)*COLUMN,TRANSOM,STEEL)
    for k in range(14):
        # The head moulding overlaps the upper half of the fourteenth course.
        z=SILL+(k+(.28 if k==13 else .50))*BRICK_H
        q=hit(tri,names,np.array([-1.21,-2.,z]),np.array([0.,1.,0.]));assert q[0] in BRICK
        probe('Fourteen courses',-1.21,z,q[0])
    for k in (3,6,8,12):probe('Recessed mortar',-1.21,SILL+k*BRICK_H,MORTAR)
    for z in (SILL,HEAD):
        for dz,mat in [(-.04,STONE),(-.015,GROOVE),(.009,GROOVE),(.025,STONE)]:probe('Stepped hood or sill',.08,z+dz,mat)
    for x,z in [(-1.1,.2),(.8,2.12),(1.27,1.30)]:probe('Spandrel and reveal',x,z,PLASTER)
    return rows
