from plaque_gate import *
def test(tri,names,hit):
    res=[]
    def sample(x,z,mat,what):
        a=hit(tri,names,np.array([x,-.65,z]),np.array([0,1.,0.]));assert a and a[0]==mat,(x,z,mat,a)
        res.append(dict(label=what,material=mat,point=a[1]))
    for sign in [-1,1]:
        x=1.95*sign
        for k,p in letters(x):
            for g in getattr(p,'geoms',[p]):
                if g.area<.00027:continue
                q=g.representative_point();sample(q.x,q.y,GOLD,'Raised character '+k)
        for z in np.linspace(.24,1.77,13):sample(x-.197,z,PLAQUE,'Dark semicontinuous background around the name')
        for z in [.132,.327,.582,.914,1.217,1.503,1.856]:sample(x+.273,z,BRICK,'Exposed red masonry edge')
        for u in [.163,.363,.563,.763,.963,1.163,1.363,1.563]:
            sample(sign*u,crown(u)-.022,RIB,'Curved top of each gate leaf')
            sample(sign*u,1.477,RIB,'Iron rail under upper panels')
    return res
