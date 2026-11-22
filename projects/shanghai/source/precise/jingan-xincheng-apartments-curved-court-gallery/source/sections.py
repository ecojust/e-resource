"""Measure the projecting edge, steel guard and clear corridor against the actual triangles."""
from court_gallery import *
def test(tri,materials,hit):
    reads=[]
    def sample(label,o,d,material):
        row=hit(tri,materials,np.asarray(o),np.asarray(d))
        assert (row and row[0])==material,(label,o,material,row)
        reads.append(dict(label=label,material=material,point=row[1] if row else None))
    for x in np.linspace(-2.7,2.7,27):
        y=curb(x)
        sample('Turn of the ochre slab nose',[x,-2.2,-.085],[0,1.,0],EDGE)
        sample('Open underside of the landing',[x,y+.135,-.45],[0,0,1.],SOFFIT)
        sample('Walkable upper deck immediately inside the edge',[x,y+.235,.07],[0,0,-1.],DECK)
        sample('Upper steel handrail follows slab turn',[x,-2.25,1.033],[0,1.,0],IRON)
    for x in np.linspace(-2.82,2.82,10):
        sample('Guardrail post',[x,-2.3,.514],[0,1.,0],POST)
    for x in (-.5,-.32,0,.22,.4):
        sample('Stair enclosure behind the gallery',[x,-.32,1.46],[0,1.,0],WALL)
    for x in(-2.48,-2.21,2.40,2.67):
        sample('Open court visible above the handrail',[x,-1.9,1.34],[0,1.,0],None)
    return reads
