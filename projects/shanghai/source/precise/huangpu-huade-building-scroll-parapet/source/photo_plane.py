"""Photo coordinates for the paired fretted parapet at 620 Middle Sichuan Road."""
import numpy as np

CROP = (253, 2350, 1271, 2946)
# Two terminal square uprights. Nominal railing height is 0.91 m; a single
# street photograph gives their proportions but does not provide a surveyed scale.
PLANE_CONTROLS = [(-1.82, 0, 246, 238), (1.82, 0, 805, 508),
                  (1.82, .91, 796, 332), (-1.82, .91, 245, 48)]
TRACE_CONTROLS=PLANE_CONTROLS
PLANE_CONTROLS=[(-1.348,0,325.4944,274.52),(.286,0,583.4621,403.6855),(.286,.91,577.458,222.8111),(-1.348,.91,323.2050,82.3837)]
def registration(controls):
    rows,values=[],[]
    for x,z,u,v in controls:
        rows.extend(([x,z,1,0,0,0,-x*u,-z*u],[0,0,0,x,z,1,-x*v,-z*v]))
        values.extend((u,v))
    h=np.append(np.linalg.solve(rows,values),1).reshape(3,3)
    # Two directions on the visible undersides fix the receding slab edges.
    # X follows the frontage. Positive Y goes back under the terrace.
    d=np.array([-141.0,72.4,.015])
    return h,d
H,D=registration(PLANE_CONTROLS)
TRACE_H,_=registration(TRACE_CONTROLS)
def position(u,v,y=0):
    h=H.copy()
    h[:,2]+=D*y
    q=np.linalg.solve(h,[u,v,1])
    return np.array([q[0]/q[2],y,q[1]/q[2]])
def level(u,v,z=0):
    h=np.column_stack((H[:,0],D,H[:,2]+z*H[:,1]))
    q=np.linalg.solve(h,[u,v,1])
    return np.array([q[0]/q[2],q[1]/q[2],z])
def pixel(point):
    x,y,z=point
    q=H@np.array([x,z,1])+D*y
    return q[:2]/q[2]

def source_pixel(u,v):
    q=TRACE_H@np.array([u/445-1.97,1-v/445,1.0])
    return q[:2]/q[2]

def trace(u,v,y=0):
    return position(*source_pixel(u,v),y)[[0,2]]
