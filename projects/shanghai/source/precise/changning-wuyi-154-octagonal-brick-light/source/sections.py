from octagonal_eye import *
def test(t,m,hit):
    rows=[]
    def p(x,z,material,note):
        v=hit(t,m,np.array([x,-.98,z]),np.array([0.,1.,0.]))
        assert v and v[0]==material,(x,z,material,v)
        rows.append(dict(label=note,material=material,point=v[1]))
    mid=octagon(.63)
    for j in range(8):
        for n in range(6):
            f=(n+.5)/6;u,z=mid[j]*(1-f)+mid[(j+1)%8]*f
            p(u,z,VAR if(n+j)%8==0 else BRICK,'Individual soldier closing octagonal aperture')
    for x in(-.32,-.16,0,.15,.33):
        for z in(.84,.99,1.29,1.42):p(x,z,DARK,'Dark field behind octagonal reveal')
        p(x,CZ-.008,BAR,'Single crossbar')
    for x in (-1.13,-.93,.89,1.11):
        for z in(.17,.52,.78,1.15,1.70,1.89,2.39):p(x,z,WALL,'Brickwork outside the opening')
    return rows
