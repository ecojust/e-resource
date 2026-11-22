import numpy as np
from math import sin,cos,pi
from red_corner import *

def test(tri,names,hit):
    rows=[]
    def ray(label,s,z,expected):
        theta=np.clip(s,-HALF,HALF)/R
        eye=np.array(pos(s,z,1.15));d=np.array([-sin(theta),cos(theta),0.])
        m=hit(tri,names,eye,d)
        assert (m[0] if m else None) in expected,(label,s,z,m[0] if m else None,expected)
        rows.append(dict(label=label,origin=eye.tolist(),direction=d.tolist(),material=m[0] if m else None,point=m[1] if m else None))
    positions=list(np.linspace(-1.02,1.60,13))
    for s in positions:
        ray('Cement plinth',s,.27,[BASE])
        ray('Red curved masonry',s,2.64,[BRICK])
        ray('First belt moulding',s,2.77,[STONE])
        ray('First belt face',s,3.20,[STONE])
        ray('First top lip',s,3.50,[CAP])
        ray('Upper curved brickwork',s,4.97,[BRICK])
        ray('Upper curved brickwork',s,6.78,[BRICK])
        ray('Upper band soffit',s,6.865,[SHADE])
        ray('Upper band face',s,7.40,[STONE])
        ray('Upper band coping',s,7.68,[CAP])
    for i,(l,r,lo,hi) in enumerate(WINDOWS):
        for h in (.15,.36,.51,.82):
            for v in (.23,.72):ray('Glazing '+str(i),l+(r-l)*v,lo+(hi-lo)*h,[GLASS])
    for s in np.linspace(WINDOWS[0][0]+.012,WINDOWS[0][1]-.006,9):
        ray('Narrow window soldier head',s,WINDOWS[0][3]+.08,[HEADER]);ray('Narrow window sill',s,WINDOWS[0][2]-.069,[HEADER])
    n=np.array([-.707106781,-.707106781,0.])
    for s in (-2.66,-2.56,-2.20,-2.09):
        for z in (9.07,9.28):
            centre=np.array(roof_point(s,z,0));eye=centre+1.2*n
            m=hit(tri,names,eye,-n);assert m and m[0]==GLASS,(s,z,m)
            rows.append(dict(label='Upper slot behind angular parapet',origin=eye.tolist(),direction=(-n).tolist(),material=m[0],point=m[1]))
    return rows
