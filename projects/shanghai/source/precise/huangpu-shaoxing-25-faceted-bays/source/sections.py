from faceted_bays import *
def test(t,names,hit):
    samples=[]
    def probe(x,z,m,label):
        r=hit(t,names,np.array([x,-3.,z]),np.array([0.,1.,0.]));assert r and r[0]in m,(x,z,label,r)
        samples.append(dict(label=label,material=r[0],point=r[1]));return -r[1][1]
    for c in INNER:
        for z in (3.022,3.294,3.569):
            for dx in (-.448,-.201,.117,.439):
                assert probe(c+dx,z,[REVEAL],'Actual recessed dark slot in centre spandrel')<-.130
        for z in (3.155,3.428):
            for dx in (-.419,.182,.441):assert abs(probe(c+dx,z,[WALL],'Front surface separating consecutive slots'))<.001
    for c in (*OUTER,*INNER):
        for lo,hi in FLOORS:
            for dx in (-.479,-.334,.104,.468):
                for f in (.17,.44,.65,.87):probe(c+dx,lo+(hi-lo)*f,[GLASS,SKY],'Individual lights on recessed or projecting window face')
    for c in OUTER:
        for dx in (-.86,-.415,0,.463,.819):
            assert probe(c+dx,6.715,[FASCIA],'Strongly projecting roof profile of one wing')>1.0
    for dx in (-.97,-.48,0,.46,.94):
        assert probe(dx,6.204,[FASCIA],'Central roof fascia set back from both corners')<.30
    return samples
