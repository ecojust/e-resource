from portal import *
def test(t,names,hit):
    rows=[]
    def ray(o,d,want,label):
        r=hit(t,names,np.array(o,float),np.array(d,float))
        if want:
            assert r and r[0] in want,(o,label,r,want)
            rows.append(dict(label=label,point=r[1],material=r[0]));return np.array(r[1])
        assert r is None,(o,r);rows.append(dict(label=label,point=None,material=None))
    for i in range(13):
        a=(i+.5)*pi/13
        for step in (.04,.12,.215,.30):
            if i==6:continue
            x,z=curve(a,step);p=ray([x,-2,z],[0,1,0],[ASHLAR,WARM],'Radiating portal stone')
            assert abs(p[1]+.103)<.0011
    for s in (-1,1):
        for j in range(5):
            for d in (.045,.130,.262):
                p=ray([s*(R+d),-2,(j+.48)*SPRING/5],[0,1,0],[ASHLAR,WARM],'Jamb block');assert abs(p[1]+.101)<.0011
    for x in np.linspace(-.95,.95,11):
        for z in (.32,1.15,1.79,2.30,2.57):ray([x,-2,z],[0,1,0],[],'Open passage')
    for z in np.linspace(3.47,3.96,17):
        p=ray([.036,-1,z],[0,1,0],[STONE],'Volute front profile');assert p[1]<-.113
    for x in np.linspace(1.524,1.83,7):
        for z in (2.52,2.59):p=ray([x,-2,z],[0,1,0],[PLAQUE],'Number 131 enamel plaque');assert abs(p[1]+.098)<.0011
    for x in np.linspace(-1.8,1.8,11):
        p=ray([x,-1,4.196],[0,1,0],[STONE],'Lintel above voussoirs');assert abs(p[1]+.234)<.0011
    return rows
