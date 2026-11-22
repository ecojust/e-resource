"""Rectify the fence in Antigng's upright street photograph at 36 Sinan Road.

Measurement coordinates use the crop beginning at (609, 2490) on the upright
2988 by 5312 photograph, sampled at one third of that resolution. The fence
plane is Y=0. Negative Y faces the street. Dimensions are nominal.
"""
import numpy as np

CROP_ORIGIN = (609, 2490)
CROP_SCALE = 3.
# The posts, rather than the intentionally raked iron spindles, supply the
# plumb directions. Two crown centres and two dado joints determine the plane.
# The common 2.47 m vertical separation is nominal, not a measured height.
STATIONS = [(-1.48,-.18,56.,739.),(1.18,-.18,725.,858.),
            (1.18,2.29,646.,30.),(-1.48,2.29,86.,258.)]

def homography(stations):
    a,b=[],[]
    for x,z,u,v in stations:
        a.extend([(x,z,1,0,0,0,-x*u,-z*u),(0,0,0,x,z,1,-x*v,-z*v)])
        b.extend([u,v])
    return np.append(np.linalg.solve(a,b),1.).reshape(3,3)

H = homography(STATIONS)
# Positive depth follows the return of the left pier, observed at the two
# stretcher courses. Estimated depth uses the same nominal scale as the fence.
D = np.array([168.,-4.,.10])
H[:,2]+=.18*D

def position(u,v,y=0.):
    m=H.copy()
    m[:,2]+=y*D
    q=np.linalg.solve(m,[u,v,1.])
    return np.array([q[0]/q[2],y,q[1]/q[2]])

def pixel(x,y,z):
    q=H@np.array([x,z,1.])+D*y
    return q[:2]/q[2]

def original_to_crop(u,v):
    return ((u-CROP_ORIGIN[0])/CROP_SCALE, (v-CROP_ORIGIN[1])/CROP_SCALE)
