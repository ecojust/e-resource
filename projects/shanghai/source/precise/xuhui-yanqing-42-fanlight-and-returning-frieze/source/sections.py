from corner_frieze import *
def test(t,names,hit):
    out=[]
    def check(origin,direction,material,note):
        v=hit(t,names,np.asarray(origin),np.asarray(direction));assert v and v[0]==material,(origin,material,v)
        out.append(dict(label=note,material=material,point=v[1]))
    for theta in (13,27,56,73,108,121,157,171):
        for r in (.33,.67,.78,.88):
            angle=math.radians(theta);x=RX*r*math.cos(angle);z=SPRING+RZ*r*math.sin(angle)
            check([x,-.86,z],[0,1,0],PANE,'Glazing in separate angular sectors')
    for theta in (41,90,139):
        for r in (.305,.642,.80):
            a=math.radians(theta);check([RX*r*math.cos(a),-.82,SPRING+RZ*r*math.sin(a)],[0,1,0],SASH,'Radial bar')
    for x in np.arange(-.91,END-.12,.236):
        for z in (1.526,1.549,1.577,1.716):check([x,-.52,z],[0,1,0],RELIEF,'Front frieze motifs')
    for y in np.arange(.14,DEPTH,.236):
        for z in (1.526,1.549,1.577,1.716):check([1.66,y,z],[-1,0,0],RELIEF,'Relief motifs on return')
    for y in (.12,.28,.55,.80):
        for z in (1.192,1.237,1.276,1.342):check([1.76,y,z],[-1,0,0],STONE,'Cornice returns around corner')
    for x in (-.92,-.83,.76,.91,1.07):check([x,-.74,.449],[0,1,0],BAND,'Dark horizontal band on impost')
    return out
