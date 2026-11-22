from perforated_steeple import *
def test(t,m,hit):
    rows=[]
    def check(x,z,mat,label):
        a=hit(t,m,np.array([x,-1.,z]),np.array([0.,1.,0.]))
        assert (a[0]if a else None)==mat,(x,z,mat,a)
        rows.append(dict(label=label,material=a[0] if a else None,point=a[1] if a else None))
    for z in (.21,.39,.56,.73,.9):
        opening=.57*(1-(z-.136)/(.964));outer=.845*(1-(z-.136)/(1.58-.136));edge=1.19*(1-(z-.14)/(4.13-.14))
        for s in [-1,1]:
            for k in (.16,.52,.82):check(s*k*opening,z,None,'Open sky through the narrower back arch')
            for k in (.22,.75):check(s*(opening+k*(outer-opening)),z,OCHRE,'Splayed or inset rear reveal')
            for k in (.28,.72):check(s*(outer+k*(edge-outer)),z,PALE,'Pale outer leg')
    for p in glyphs():
        xy=p.representative_point();check(xy.x,xy.y,DARK,'Inscription centre stroke')
    for z in (3.01,3.22,3.41,3.65):
        for x in (-.065,.025,.072):check(x,z,PALE,'Solid tapered upper panel')
    for z in (4.32,4.53,4.71,4.91):check(0,z,METAL,'Upright beyond apex')
    for x in (-.28,-.18,.18,.28):check(x,4.808,METAL,'Single cross arm')
    return rows
