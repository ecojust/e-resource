from swag import *
def test(tri,m,hit):
    rows=[]
    def probe(x,z,mat,label):
        r=hit(tri,m,np.array([x,-1.,z]),np.array([0.,1.,0.]))
        assert r and r[0] in mat,(label,x,z,r,mat)
        rows.append(dict(label=label,material=r[0],point=r[1]))
    for x in np.linspace(-1.29,1.29,21):
        for z in(.042,.103,1.098,1.158):probe(x,z,[MOULD],'Parapet coping and bed mould')
    for x in np.linspace(-.71,.71,25):probe(x,base(x),[FOL,FRUIT],'Continuous raised festoon')
    for x in(-.64,-.43,-.2,0,.19,.45,.64):
        for z in (.15,.927):probe(x,z,[GROUND],'Recessed unadorned plaster field')
    for x in (-1.14,1.14):
        for z in (.31,.42,.57):probe(x,z,[MOULD],'Long tongue on flanking upright')
        for dz in(-.038,.038):probe(x+dz,.781,[MOULD],'Short twin flutes')
    return rows
