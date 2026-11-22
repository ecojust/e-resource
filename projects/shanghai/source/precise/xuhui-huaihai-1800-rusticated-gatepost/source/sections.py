from granite_post import *
def test(tri,names,hit):
    rows=[]
    def ck(x,z,m,label):
        r=hit(tri,names,np.array([x,-.58,z]),np.array([0,1,0.]));assert r and r[0]==m,(x,z,m,r);rows.append(dict(label=label,material=m,point=r[1]))
    for idx,(z,t) in enumerate(COURSES):
        for xx in [-.339,-.20,-.08,.077,.19,.341]:
            for hh in [.22,.57,.82]:
                zz=z+(t-z)*hh
                if abs(xx)<.319 and .963<zz<1.277:continue
                ck(xx,zz,GRANITE,'Picked granite on a separate course')
    for x in [-.29,-.18,.09,.258]:
        for z in [.286,.654,1.283]:ck(x,z,MORTAR,'Shadowed horizontal bed')
    for x in [-.348,.352]:ck(x,.983,MORTAR,'Bed joint continuing outside the address plate')
    for char,p in letters():
        for a in getattr(p,'geoms',[p]):
            if a.area<.000051:continue
            pt=a.representative_point();ck(pt.x,pt.y,TYPE,'Visible street and address character '+char)
    for z in [1.504,1.525,1.547]:ck(0,z,LUG,'Faceted lug under the open coping')
    return rows
