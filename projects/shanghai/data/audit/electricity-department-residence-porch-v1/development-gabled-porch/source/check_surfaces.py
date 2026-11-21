"""Check front-facing masonry, timber, glazing and iron against the authored facade sections."""
import numpy as np
from porch import BRICK,WOOD,STONE,GLASS,WHITE,DARK,SHADE

def check_triangles(triangles,materials,distant):
    # Local sections through the model check recesses, projections and individual materials.
    tests = [('porch leaf',0,1.36,DARK,1.05),('post',1.29,1.42,WOOD,-1.438),
             ('post shoe',-1.29,.18,STONE,-1.465),('porch pendant',0,4.20,WOOD,-1.606),
             ('attic slot',3.04,7.11,SHADE,.15),('lower pane',3.15,2.12,GLASS,.135),
             ('upper sash',3.04,4.8,WHITE,.045),('basket upper rail',3.04,4.33,WHITE,-.275),
             ('brick shoulder',4.08,5.02,BRICK,0),('gable pendant',3.04,8.55,WOOD,-.244),
             ('porch rear masonry',-.92,1.55,BRICK,.75),('small pane',-2.18,1.45,GLASS,.885)]
    for x in [-1.29,1.29]:
        for z in [.104,.22,.59,1.8,2.45]:
            item=(STONE,-1.485) if z<.13 else ((STONE,-1.465) if z<.29 else (WOOD,-1.438))
            tests.append(('post section',x,z,*item))
    for x in [2.40,3.23,3.56]:
        tests.append(('basket horizontal rail',x,3.99,WHITE,-.175))
    v1=triangles[:,1]-triangles[:,0];v2=triangles[:,2]-triangles[:,0]
    direction=np.array([0.,1.,0.]);normal=np.cross(direction,v2)
    det=np.einsum('ij,ij->i',v1,normal);inv=np.zeros_like(det);base=np.abs(det)>1e-10;inv[base]=1/det[base]
    rays=[]
    for name,x,z,expected,depth in tests:
        start=np.array([float(x),-4.,float(z)]);s=start-triangles[:,0];u=inv*np.einsum('ij,ij->i',s,normal)
        q=np.cross(s,v1);v=inv*q[:,1];distance=inv*np.einsum('ij,ij->i',v2,q)
        hits=np.flatnonzero(base&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(distance>1e-8))
        assert len(hits),(name,x,z)
        i=hits[np.argmin(distance[hits])];y=float(start[1]+distance[i])
        assert materials[i]==expected and abs(depth-y)<.010,(name,x,z,materials[i],expected,y,depth)
        rays.append(dict(feature=name,x_m=x,z_m=z,first_material=str(materials[i]),first_y_m=round(y,5),expected_y_m=depth))
    return dict(triangles=len(triangles),far=distant,rays=rays)
