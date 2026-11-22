from carved_sashes import *
def test(t,names,hit):
    rows=[]
    def sample(x,z,expected,feature):
        result=hit(t,names,np.array([x,-.45,z]),np.array([0.,1.,0.]));assert (result[0] if result else None)==expected,(x,z,expected,result)
        rows.append(dict(label=feature,material=expected,point=result[1] if result else None))
    for c in CENTRES:
        for z in (.60,.76,.93,1.44,1.61,1.76):
            for s in (-.10,.10):sample(c+s,z,PANE,'Glazing between shaped corners')
        for z in (.445,1.07,1.278,1.907):sample(c,z-.004 if z in (.445,1.278)else z+.004,BAR,'Flat octagonal rim')
        for z in (.56,.90,1.16,1.53,1.85):
            for side in (-1,1):sample(c+side*.223,z,POST,'Vertical wooden stile')
        for z in (1.126,1.199):sample(c+.034,z,BAR,'One of the two rails crossing the joint')
        sample(c+.06,1.164,MORTISE,'Small recess in the middle of the grille')
    for x in np.linspace(-1.07,1.07,15):sample(x,.202,SILL,'Pierced rail drop')
    for x in np.linspace(-1.07,1.07,15)[:-1]:sample(x+.072,.201,None,'Clear opening in lower rail')
    return rows
