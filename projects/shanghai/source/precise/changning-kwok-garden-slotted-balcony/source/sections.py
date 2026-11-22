from math import pi
import numpy as np
from garden_balcony import *

def test(tri,names,hit):
    rows=[]
    def probe(label,x,z,expected,origin_y=-2):
        eye=np.array([x,origin_y,z]);direction=np.array([0.,1.,0.]);q=hit(tri,names,eye,direction)
        mat=q[0] if q else None
        assert mat in expected,(label,x,z,mat,expected)
        rows.append(dict(label=label,origin=eye.tolist(),direction=direction.tolist(),material=mat,point=q[1] if q else None))
    for i,x in enumerate(SLOTS):
        probe('Board cheek beside slot '+str(i),x+.035,.465,[TIMBER])
        probe('Board lower sill '+str(i),x,.281,[TIMBER])
        # Observe the slot and drilling from behind the front surface as well as the first hit.
        pt=hit(tri,names,np.array([x,-2.,.49]),np.array([0.,1.,0.]))
        assert pt and pt[1][1]>1.0,(x,pt)
        rows.append(dict(label='Open slot '+str(i),origin=[x,-2.,.49],direction=[0.,1.,0.],material=pt[0],point=pt[1]))
        if i%4!=2:
            pt=hit(tri,names,np.array([x,-2.,.722]),np.array([0.,1.,0.]))
            assert pt and pt[1][1]>1.,(x,pt)
            rows.append(dict(label='Open upper drilling '+str(i),origin=[x,-2.,.722],direction=[0.,1.,0.],material=pt[0],point=pt[1]))
    for i,x in enumerate(JOISTS):probe('Joist end '+str(i),x,-.063,[GRAIN])
    for z in (.89,1.022,1.163):
        for x in (-2.62,-1.52,-.51,.63,1.93,2.67):probe('Thin upper rail',x,z,[METAL])
    for x in (-.702,-.55,.39,.57):
        for z in (1.36,1.62):probe('Upper glazing',x,z,[GLASS],.30)
    for x in np.linspace(-1.75,1.75,13):probe('Clipped roof verge',x,2.57,[TIMBER])
    return rows
