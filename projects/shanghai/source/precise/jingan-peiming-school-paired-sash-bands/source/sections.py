"""Read the upper and lower lights, spandrels, bed joints and projecting sill on both GLBs."""
from paired_sashes import *

def test(tri,materials,hit):
    rows=[]
    def probe(x,z,mat,label):
        r=hit(tri,materials,np.array([x,-2,z]),np.array([0.,1.,0.]))
        assert r and r[0]==mat,(x,z,mat,r)
        rows.append(dict(label=label,material=mat,point=r[1]))
        return r[1][1]
    for centre in CENTRES:
        for lo,hi,material in LIGHTS:
            for dx in (-.28,-.21,-.13,-.075,.073,.128,.218,.286):
                for f in (.18,.48,.81):probe(centre+dx,lo+f*(hi-lo),material,'Paired casement glass')
            for f in (.18,.51,.83):probe(centre,lo+f*(hi-lo),WOOD,'Timber meeting stile')
            for dx in (-.28,0,.28):probe(centre+dx,lo-.019,EDGE,'Stone sill in front of the glass')
        for dx in (-.28,0,.28):
            for z in (2.025,2.266,2.62):probe(centre+dx,z,PANEL,'Inset floor panel between two windows')
        for hand in (-1,1):
            for z in (.50,1.32,2.16,3.33,4.29):probe(centre+.492*hand,z,EDGE,'Continuous vertical margin')
    for k in range(1,16):
        row=-.18+.301*k
        for x in (-1.69,.0,1.70):
            assert abs(probe(x,row+.14,WALL,'Face of grey render')-0)<.001
            assert abs(probe(x,row-.006,WALL,'Recessed bed joint')-.028)<.001
    return rows
