"""Image and model registration for the western wall of the Doeda Building."""
import numpy as np

# 610 x 1033 working area. Upright full image: 2988 x 5312 px.
CROP=(1250,1430,2200,3040)
WIDTH,HEIGHT=610,1033
PLANE_CONTROLS=[(-1.85,0,88,918),(1.85,0,534,734),
                (1.85,3.10,536,181),(-1.85,3.10,49,469)]
def registration():
    a=[];b=[]
    for x,z,u,v in PLANE_CONTROLS:
        a.extend([[x,z,1,0,0,0,-x*u,-z*u],[0,0,0,x,z,1,-x*v,-z*v]]);b.extend([u,v])
    h=np.append(np.linalg.solve(a,b),1).reshape(3,3)
    origin=np.array([[(1494-1250)*WIDTH/950,(2656-1430)*HEIGHT/1610]])
    focal=31/np.hypot(36,24)*np.hypot(5312,2988)*WIDTH/950
    k=np.array([[focal,0,origin[0,0]],[0,focal,origin[0,1]],[0,0,1]])
    x,up=(np.linalg.inv(k)@h)[:,:2].T
    normal=np.cross(x,up);normal*=np.mean([np.linalg.norm(x),np.linalg.norm(up)])/np.linalg.norm(normal)
    # Model y increases into the masonry. Its vanishing direction points away.
    if normal[-1]<0:normal=-normal
    return h,k@normal
H,D=registration()
def position(u,v,y=0):
    m=H.copy();m[:,2]+=y*D;c=np.linalg.solve(m,[u,v,1])
    return np.array([c[0]/c[2],y,c[1]/c[2]])
def pixel(point):
    x,y,z=point;h=H@np.array([x,z,1])+D*y
    return h[:2]/h[2]
def upright(u,v):return [1250+950*u/WIDTH,1430+1610*v/HEIGHT]
