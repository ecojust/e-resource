"""Initialize the joint archival camera solve from the two directions on the portal face."""
from pathlib import Path
import json,runpy
import numpy as np

HERE=Path(__file__).absolute().parent
fit=runpy.run_path(HERE/'fit-portal.py')
dims=fit['d'];marks=fit['FACE']
uv_to_arch=fit['metric'];homography=fit['homography']
G=homography([uv_to_arch(v)for v in marks],marks)
pr=np.array([286.,200.5])  # Centre of the photographic rectangle, excluding the caption and page.
vx=G[:2,0]/G[2,0];vz=G[:2,1]/G[2,1]
f=float(np.sqrt(-np.dot(vx-pr,vz-pr)))
K=np.array([[f,0,pr[0]],[0,f,pr[1]],[0,0,1.]])
M=np.linalg.inv(K)@G
if M[2,2]<0:M=-M
unit=lambda x:x/np.linalg.norm(x)
length=(np.linalg.norm(M[:,0])+np.linalg.norm(M[:,1]))/2
Y=unit(np.cross(M[:,1],M[:,0]))*length
if Y[2]<0:Y=-Y
P=K@np.column_stack([M[:,0],Y,M[:,1],M[:,2]])
eye=-np.linalg.solve(P[:,:3],P[:,3])
