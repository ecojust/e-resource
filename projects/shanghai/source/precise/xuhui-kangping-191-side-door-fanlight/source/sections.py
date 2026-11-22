from arched_transom import *
def test(tri,names,hit):
    result=[]
    def ray(x,z,m,label):
        h=hit(tri,names,np.array([x,-.70,z]),np.array([0,1.,0]));assert h and h[0]==m,(x,z,m,h)
        result.append(dict(label=label,material=m,point=h[1]))
    def polar(deg,r,m,label):
        a=math.radians(deg);x=r*math.cos(a);z=LEVEL+r*math.sin(a)
        if bottom(x)-.054<z<bottom(x)+.018:
            ray(x,z,HEAD,'Raised centre of the door head in front of the fanlight')
        else:
            ray(x,z,m,label)
    for degrees in ANGLES:
        for radius in [.216,.284,.336,.468,.533,.607,.663]:polar(degrees,radius,SPOKE,'First surface of radial glazing bar')
    for degrees in [11,32,43,66,77,102,114,138,147,171]:
        for radius in [.207,.318,.475,.655]:polar(degrees,radius,GLASS,'Glazing in the clear segment')
        for radius in [.133,.397]:
            if radius==.133 and degrees in (11,171):
                polar(degrees,radius,HEAD,'Shaped head obscures the lowest end of the inner arc')
            else:
                polar(degrees,radius,RING,'The two concentric curved bars')
        polar(degrees,.771,RIM,'Heavy outer rim')
    for x in [-.624,-.448,-.305,-.150,0,.22,.36,.518,.682]:ray(x,bottom(x)-.017,HEAD,'Upswept wooden head')
    for side in [-1,1]:
        for z in [.112,.212,.425,.794,1.105,1.225]:ray(.972*side,z,STUCCO,'Cream wall')
    return result
