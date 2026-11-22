from curved_canopy import *
def test(tri,names,hit):
    rows=[]
    def check(start,direction,mat,name):
        q=hit(tri,names,np.array(start),np.array(direction));assert q and q[0]==mat,(start,direction,mat,q)
        rows.append(dict(label=name,material=mat,point=q[1]))
    for x in np.linspace(-.85,.85,8):
        for y in [-.19,-.44,-.72,-1.011,-1.19]:
            check([x,y,3.4],[0,0,-1],EDGE,'Weathering on roof of entrance')
    for x in [0,.24,-.33,.44]:
        for z in [.17,.36,.63,1.1,1.21,1.35]:
            check([x,-1.6,z],[0,1,0],WOOD,'Recessed entrance behind open canopy')
    for side in [-1,1]:
        x=side*.779
        for projection,z in [(.16,2.0),(.35,2.14),(.53,2.27),(.71,2.34),(.92,2.45)]:
            check([x+side*.41,-projection,z],[-side,0,0],PEBBLE,'Body of curving console')
        check([x+side*.41,-1.096,2.402],[-side,0,0],EYE,'Round end visible in side elevation')
        for z in [.20,.41,.66,.88]:
            check([x,-.7,z],[0,1,0],PEBBLE,'Upright support beneath the curve')
    return rows
