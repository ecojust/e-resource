from balcony_strips import *
def test(t,names,hit):
    out=[]
    def r(x,z,allowed,label):
        a=hit(t,names,np.array([x,-.6,z]),np.array([0.,1,0]));assert (a[0] if a else None) in allowed,(x,z,allowed,a)
        out.append(dict(label=label,material=a[0] if a else None,point=a[1] if a else None))
    for c in C:
        for s in (-1,1):
            for z in (.25,.52,.91,1.22,1.40):r(c+s*.128,z,(ORN,),'Long outer raised edge')
            for z in (.24,.56,.92,1.22):r(c+s*.178,z,(None,),'Interval next to ornament panel')
            for z in (.21,.52,.95,1.15):r(c+s*.112,z,(BASE,),'Plain recessed face near outer edge')
            r(c+s*.107,1.15,(ORN,),'Upper moulding passing in front of background at the old plain-field probe')
        for z in (1.217,1.146,1.067,.977,.878):r(c,z,(ORN,),'Rounded upper relief cluster')
        for z in (.655,.437):
            r(c,z,(BASE,),'Open centre within lower angular motif')
            r(c+.055,z,(ORN,),'Rim of angular motif')
        for z in (.063,1.525):r(c,z,(BEAM,),'Continuous horizontal timber rail')
    return out
