from applied_ribbons import *
def test(t,names,hit):
    samples=[]
    def take(x,z,allowed,label):
        v=hit(t,names,np.array([x,-2.,z]),np.array([0.,1.,0.]));assert v and v[0]in allowed,(x,z,v,allowed)
        samples.append(dict(label=label,material=v[0],point=v[1]));return -v[1][1]
    for x in np.linspace(-2.11,2.11,8):
        for z in [2.78,2.93,3.19,3.43,3.56]:assert take(x,z,[BATTEN],'Vertical strip in upper frieze')>.046
    for x in (-1.87,-1.72,-1.44,-.96,-.69):
        for z in (1.39,1.64,1.91,2.12,2.43):assert take(x,z,[PANE],'Recessed window glass left of central panel')<-.15
    for x in (-1.53,-1.22,-.92,-.731,.706,1.085,1.43,1.70):
        for z in (.42,.58,.71):assert abs(take(x,z,[WALL],'Ochre infill retained behind the white moulding'))<.001
    for side in (-1,1):
        for q in (.15,.28,.51,.74,.86):
            x,z=bez(q,(0.,3.664),(.064,3.32),(.323,3.224),(.584,3.05));take(side*x,z,[BATTEN],'Curved crown of central leaf')
    for x in (-1.62,-.74,-.2,.36,.96,1.76):take(x,1.105,[RAIL],'Continuous sill ledge')
    return samples
