from spandrel import *
def test(t,names,hit):
    rows=[]
    def probe(x,z,allowed,label):
        q=hit(t,names,np.array([x,-2.,z]),np.array([0,1.,0.]))
        assert q and q[0] in allowed,(x,z,label,q,allowed)
        rows.append(dict(label=label,material=q[0],point=q[1]));return -q[1][1]
    for c in CENTERS:
        for sc in (1.,.68,.49):
            for fraction in (.525,.564,.614):
                for signx in (-1,1):
                    for signz in (-1,1):
                        dx=1.24*sc*fraction;h=.49*sc*(1.-fraction)
                        # The raised crest is pale grey in both roles; its height records fine bevel geometry.
                        p=probe(c+signx*dx,Z+signz*h,[LINES,TRIM],'Long diagonal of raised lozenge')
                        assert .086<=p<.112
        for sign in (-1,1):
            assert probe(c,Z+sign*.49*.49,[LINES],'Full apex of the central diamond')>.08
            assert probe(c+sign*1.24*.49,Z,[LINES],'Full lateral vertex of central diamond')>.08
        for dx in (-.11,.04,.16):
            for du in (-.068,.055):assert abs(probe(c+dx,Z+du,[FIELD],'Unbroken low centre of spandrel')-.049)<.001
        for z in (.639,1.086,1.60,3.26,3.60,3.949):
            for dx in (-.67,.16,.51):probe(c+dx,z,[SKY,PANE,WINDOW],'Four lights under continuous transom')
        for x in np.linspace(c-.77,c+.77,9):
            for z in (Z-H-.009,Z+H+.011):assert abs(probe(x,z,[TRIM],'Continuous panel edge')-.115)<.0011
    for x in (-2.39,0.,2.39):
        for d in (-.067,.067):
            for z in (4.20,4.32,4.42,4.51):assert probe(x+d,z,[TRIM],'Curved bracket below upper cornice')>.09
    return rows
