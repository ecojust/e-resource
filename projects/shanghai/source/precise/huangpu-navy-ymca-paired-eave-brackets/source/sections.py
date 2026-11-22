"""Verify the photographed pairs of curved brackets, the eaves, two upper windows and their separate hoods."""
import numpy as np
from top_floor import *

def test(mesh,names,hit):
    rows=[]
    def ray(o,d,allowed,label):
        result=hit(mesh,names,np.array(o,dtype=float),np.array(d,dtype=float))
        assert result and result[0] in allowed,(label,o,result,allowed)
        rows.append(dict(label=label,point=result[1],material=result[0]))
        return np.array(result[1])
    for fn,us in [(FACE,(-.87,.87)),(LEFT,(-.71,)),(RIGHT,(.71,))]:
        for u in us:
            for frac in (.12,.29,.43,.57,.70,.85,.958):
                z=2.57+.71*frac
                front=.155+.43*frac**1.91
                for dx in (-.077,.077):
                    target=np.array(fn(u+dx,z,0.));n=np.array(fn(u+dx,z,1.))-target
                    p=ray(target+1.5*n,-n,[WHITE],'Arcing paired bracket')
                    assert abs(np.linalg.norm(p-target)-front)<.012
                target=np.array(fn(u,z,0.));n=np.array(fn(u,z,1.))-target
                p=ray(target+1.5*n,-n,[WHITE],'Gap between the two plaster brackets')
                assert np.linalg.norm(p-target)<.0012
    for fn,l,r in PLANES:
        for pos in np.linspace(l+.095,r-.095,7):
            for z,proj,m in [(.11,.005,BASE),(.218,.050,DARK),(.266,.085,ACCENT),(2.435,.018,ACCENT),
                               (3.303,.665,DARK),(3.376,.715,ACCENT),(3.423,.705,DARK),(3.451,.72,ACCENT)]:
                loc=np.array(fn(pos,z,0.));n=np.array(fn(pos,z,1.))-loc
                p=ray(loc+n*1.8,-n,[m],'Chamfered continuous eave and upper-storey bands')
                assert abs(np.linalg.norm(p-loc)-proj)<.0016,(pos,z,proj,p,loc)
    for c in CENTERS:
        for x in (c-.253,c+.158):
            for z in (.811,1.15,1.548):
                p=ray((x,-2,z),(0,1,0),[SKY,PANE],'Deep upper-floor glazing')
                assert abs(p[1]-.133)<.001
        for x in (c-.362,c,c+.362):
            p=ray((x,-2.,1.229),(0,1,0),[FRAME],'Narrow dark window stile')
            assert abs(p[1]-.102)<.001
        for a in (.19,.31,.45,.55,.72,.82):
            x=c+.466*cos(a*pi)*.7;y=-.032-.392*sin(a*pi)*.7
            p=ray((x,y,2.34),(0.,0.,-1.),[FABRIC,STITCH],'Separate curved awning at each upper window')
            assert 2.04<p[2]<2.115
    for x in (-1.22,0.,1.22):
        for z in (.66,1.04,1.61):
            p=ray((x,-2,z),(0,1,0),[ACCENT],'Raised surround to white window bay')
            assert abs(p[1]+.027)<.0001
    return rows
