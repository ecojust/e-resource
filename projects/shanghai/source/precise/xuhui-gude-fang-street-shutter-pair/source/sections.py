from open_shutters import *
def test(tri,names,hit):
    out=[]
    def ck(x,z,m,text):
        r=hit(tri,names,np.array([x,-.63,z]),np.array([0,1,0.]));assert r and r[0]==m,(x,z,m,r);out.append(dict(label=text,material=m,point=r[1]))
    for i,x in enumerate(CENTRES):
        for sign in [-1,1]:
            c=x+sign*.372;groups=13 if i==0 else 31;step=(1.767-.365-.097)/groups
            for k in range(0,groups,2):ck(c,.365+.046+k*step+(.026 if i==0 else .012),RED if i==0 else BROWN,'Individual sloping blade')
            if i==0:
                for k in range(13):ck(c,.365+.046+k*step+.009,WHITE,'Pale rail between sets of closely paired red blades')
            for z in [.461,.841,1.133,1.463]:ck(c+.106,z,WHITE if i==0 else BROWN,'Shutter frame border')
            for z in [.52,1.53]:ck(c-sign*.106,z,HINGE,'Two fixings on the open shutter leaf')
        for xx in [-.151,-.065,.017]:
            for z in [.468,.751,1.118,1.477,1.68]:ck(x+xx,z,GLASS,'Recessed glass')
        for xx in [-.21,0,.19]:ck(x+xx,.324,SILL,'Stone sill')
    return out
