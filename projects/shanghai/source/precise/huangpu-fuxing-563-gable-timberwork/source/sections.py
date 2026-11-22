from garden_gable import *
def test(t,names,hit):
    seen=[]
    def take(x,z,m,label):
        r=hit(t,names,np.array([x,-3.,z]),np.array([0.,1.,0.]));assert r and r[0] in m,(x,z,m,r)
        seen.append(dict(label=label,point=r[1],material=r[0]));return -r[1][1]
    for dx in (-.368,-.244,.217,.343):
        for z in (2.547,2.664,2.781,2.902,3.041,3.171,3.287):take(C+dx,z,[PANE,SHADE],'Two separately glazed window leaves')
    for z in (2.532,2.651,2.78,3.015,3.160,3.291):take(C-.008,z,[CASING],'Pale central window bar')
    for x in (-1.63,-1.19,-.742,.747,1.225,1.635):
        for z in (3.024,3.11,3.192):take(x,z,[BEAM],'Dark stud in ochre infill')
    for x in (-2.55,-2.19,-1.76,-1.34,-.84,.69,1.184,1.535,1.883,2.37):
        assert take(x,elevation(x)+.012,[EDGE],'Inclined outer verge over deep soffit')>.33
    for x in (-.390,-.215,.151,.334,.537):
        for j in range(8):assert take(C+x,1.664+j*.097+.029,[LOUVRE],'Sloping individual blind slat')>.49
    for x in (-2.22,-1.81,1.56,2.31):
        for z in (.42,.91,1.37,1.83,2.13):take(x,z,[WALL],'Roughcast field below the timber course')
    return seen
