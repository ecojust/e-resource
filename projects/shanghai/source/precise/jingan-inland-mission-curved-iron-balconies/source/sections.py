"""Independent frontal hits test both balcony edges, ironwork, piers and both forms of window."""
from curved_balconies import *
def test(tri,materials,hit):
    rows=[]
    def sample(x,z,material,label):
        q=hit(tri,materials,np.array([x,-2.0,z]),np.array([0.,1.,0.]))
        assert q and q[0]==material,(x,z,material,q)
        rows.append(dict(label=label,material=material,point=q[1]))
        return q[1][1]
    for base in DECKS:
        for x in (-1.53,-1.17,-.64,-.245,0,.234,.64,1.17,1.53):
            depth=sample(x,base-.03,RIM,'Curved outer face of upper moulding')
            assert abs(depth-(rail_y(x)-.067))<.012
            sample(x,base-.103,RIM,'Lower moulded edge')
            sample(x,base-.159,SHADE,'Recessed underside')
            sample(x,base+.757,IRON,'Continuous top handrail')
        for x in (-1.68,-.508,-.312,.312,.508,1.68):
            for dz in (.091,.25,.565):sample(x,base+dz,IRON,'Main railing uprights')
        for x in (-.215,-.117,0,.117,.215):
            z=.059+(x+.31)*(.666-.059)/.62
            sample(x,base+z,IRON,'Diagonal through the central circular ornament')
    for cx in CENTRES:
        for dx in (-.48,-.30,.16,.428):
            for z in (1.37,1.715,2.04):sample(cx+dx,z,GLASS,'Lower rectangular windows')
        for dx in (-.46,-.31,.082,.52):
            for z in (4.02,4.43,4.744):sample(cx+dx,z,SKY,'Upper arched windows')
        for z in (4.73,4.878,5.02):sample(cx,z,DARK,'Bar in the middle of the lunette')
    for x in (-1.86,1.86):
        for z in (.485,1.112,1.767,2.433):sample(x,z,RIM,'Flanking pier')
    return rows
