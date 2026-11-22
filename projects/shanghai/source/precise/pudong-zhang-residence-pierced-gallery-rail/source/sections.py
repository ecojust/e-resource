from gallery_rail import *
def test(t,names,hit):
    checks=[]
    def probe(x,z,want,label):
        a=hit(t,names,np.array([x,-.55,z]),np.array([0.,1,0]))
        assert (a[0] if a else None)==want,(x,z,want,a)
        checks.append(dict(label=label,material=a[0] if a else None,point=a[1] if a else None))
    for c in CENTRES:
        for side in (-1,1):
            for z in (.22,.47,.71,.98,1.15):
                probe(c+side*W/2,z,RIM,'Vertical edge of a single panel')
            for z in (.26,.46,.77,1.13):
                probe(c+side*.225,z,None,'Daylight between neighbouring panels')
            for z in (.40,.49):
                probe(c+side*.245*W,BASE+H*z,RED,'Slender upright within panel')
        for z in (.545,.716,.863,.328,.088):
            probe(c,BASE+H*z,RED,'Bud at centre of reflected branches')
        for z in (.19,.43,.61,.93):
            probe(c+.008,BASE+H*z,None,'Opening between mirrored stems')
    for x in np.linspace(-.93,.93,17):
        for z in (.042,1.439):probe(x,z,RAIL,'Continuous framing rail')
    return checks
