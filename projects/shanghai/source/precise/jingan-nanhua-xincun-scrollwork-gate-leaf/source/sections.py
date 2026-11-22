"""Trace the openwork rather than relying on the silhouette of an opaque textured plate."""
from iron_leaf import *
def test(tri,materials,hit):
    checks=[]
    def probe(x,z,expected,why):
        row=hit(tri,materials,np.array([x,-1.6,z]),np.array([0.,1.,0.]))
        assert (row and row[0])==expected,(why,x,z,expected,row)
        checks.append(dict(label=why,material=expected,point=row[1]if row else None))
    for x in np.linspace(-.778,.778,11):
        if abs(x)<.02: continue
        for z in(.135,.185,.85,1.025,1.155):probe(x,z,PICKET,'Separate upright')
        probe(x,profile(x)+.066,PEAK,'Forged spear')
    for x in(-.84,-.73,-.57,-.25,-.06,.15,.37,.51,.74):
        for z in (.012,.092,.967,profile(x)-.001):probe(x,z,FRAME,'Continuous structural rail')
    for x in(-.69,-.53,-.20,.085,.215,.70):
        for z in(.19,.27,.84,1.095):probe(x,z,None,'Open space between uprights')
    for x in(-.429,.429):
        probe(x,.765,SCROLL,'Central diamond peak')
        probe(x+.095,.594,SCROLL,'Central diamond tip')
    for x in(-.865,0,.865):
        for z in(.092,.967):probe(x,z,PIN,'Iron rail fixing')
    return checks
