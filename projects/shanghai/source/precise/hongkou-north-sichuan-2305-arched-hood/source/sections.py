import numpy as np
from console import *
def test(t,m,hit):
    rows=[]
    def shot(x,z,mat,label):
        r=hit(t,m,np.array([x,-1.12,z]),np.array([0.,1.,0.]));assert r and r[0]==mat,(x,z,label,r)
        rows.append(dict(label=label,material=r[0],point=r[1]))
    for theta in np.linspace(.19,pi-.19,23):
        for radius in (.91,.985):shot(radius*cos(theta),.50+radius*sin(theta),TRIM,'Arch band at two radii')
    for x in (-1.53,1.53,-1.44,1.44):
        for z in (.26,.75,1.,1.3,1.6,2.36):shot(x,z,WALL,'Grey roughcast beside the doorway')
    for x in np.linspace(-1,1,9):
        for z,mat in [(1.979,TRIM),(2.03,EDGE),(2.067,TRIM),(2.125,EDGE),(2.217,EDGE)]:shot(x,z,mat,'Stepped moulding on canopy')
    for x in (-1.177,1.177):
        for z in (1.04,1.22,1.41,1.62,1.78):shot(x,z,BODY,'Bracket from narrow foot to upper scroll')
    return rows
