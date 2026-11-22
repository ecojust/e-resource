from gate_panels import *
def test(t,names,hit):
    rows=[]
    def r(x,z,m,l):
        a=hit(t,names,np.array([x,-.75,z]),np.array([0.,1,0]));assert (a[0] if a else None)==m,(x,z,m,a)
        rows.append(dict(label=l,material=a[0] if a else None,point=a[1] if a else None))
    for i,(x0,x1,z0,z1) in enumerate(OPEN):
        for x in np.linspace(x0+.062,x1-.062,5):
            for z in np.linspace(z0+.060,z1-.06,3):r(x,z,FIELD,'Inside grey field '+str(i+1))
        for z in np.linspace(z0+.062,z1-.062,5):
            for x in (x0+.022,x1-.022):r(x,z,FINE,'Two moulded sides of grey field')
    for x in np.linspace(-.57,.57,13):
        r(x,.085,None,'Open doorway under stone bearer')
        r(x,.294,STONE,'Lower trapezoidal beam')
        r(x,1.325,FRAME,'Projecting band between panel levels')
    for x in (-.97,-.43,.43,.97):
        for z in (.61,.83,1.14):r(x,z,LIME,'Unbroken plaster wall between grey reliefs')
    return rows
