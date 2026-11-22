from lane_gate import *
def test(tri,names,hit):
    seen=[]
    def ck(x,z,m,label):
        r=hit(tri,names,np.array([x,-.6,z]),np.array([0,1,0.]));assert r and r[0]==m,(x,z,m,r);seen.append(dict(label=label,material=m,point=r[1]))
    for x in np.linspace(-.86,.09,16):
        for dz in [0,.218]:ck(x,wave(x)-dz,IRON,'Upper and lower waved iron straps')
    for x in np.linspace(-.805,-.146,8):
        for z in [.146,.331,.625,.81,1.05,1.234]:ck(x,z,IRON,'Vertical rail')
    for ch,p in letters():
        for component in getattr(p,'geoms',[p]):
            if component.area<.00005:continue
            pt=component.representative_point();ck(pt.x,pt.y,WHITE,'Visible enamel character '+ch)
    for x in [-.69,-.43,-.17]:ck(x,wave(x)-.111,HIGHLIGHT,'Lozenge enclosed within top ring')
    for x in [.327,.797,.952]:
        for z in [.28,.84,1.23,1.73]:ck(x,z,PIER,'Street pier around tablet')
    return seen
