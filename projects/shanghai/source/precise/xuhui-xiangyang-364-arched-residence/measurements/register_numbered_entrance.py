"""Register the two street photographs to the surviving wall. Inputs are recorded panorama views."""
import json, math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
M=Path(__file__).resolve().parent
def load(name):
    return json.loads((M/'numbered-entrance-inputs.json').read_bytes())['projections'][name]
def camera(name):
    s=load(name)
    a,p=map(math.radians,[s['az']+2.73,s['pitch']])
    right=[-math.sin(a),-math.cos(a),0];forward=[math.cos(a)*math.cos(p),-math.sin(a)*math.cos(p),math.sin(p)]
    down=np.cross(right,forward)  # local (u,d,z) is right handed, right cross forward points up
    down=-down
    co=np.array([right,down,forward]); f=s['width']/2/math.tan(math.radians(s['hfov']/2))
    K=np.array([[f,0,s['width']/2],[0,f,s['height']/2],[0,0,1.]])
    return K,co
def rot_uv(uv,n1,n2):
    k,r=camera(n1);K,R=camera(n2)
    q=K@R@r.T@np.linalg.solve(k,[*uv,1.]);return q[:2]/q[2]
def project(P,q):
    p=P@np.r_[q,1.];return p[:2]/p[2]
def cut(P,uv,d=0):
    # Recover wall coordinates on a plane at specified setback.
    X=P[:,[0,2,3]].copy();X[:,2]+=P[:,1]*d
    v=np.linalg.solve(X,np.r_[uv,1.]);return np.array([v[0]/v[2],d,v[1]/v[2]])
# Use the nominal panorama device elevation and allow for the street-to-walk rise.
k,r=camera('south-2015')
eye=np.array([0.,0.,2.19]);ray=r.T@np.linalg.solve(k,[678,899,1.]);eye[:2]=-ray[:2]*(-eye[2]/ray[2])
P=k@np.c_[r,-r@eye]
# Four upper windows and eight other anchors use both original wide rectilinear photographs.
pairs={
'western second left round arch crown':((445,232),(220,195)),
'western second left inner sill left':((410,365),(175,326)),
'western second left inner sill right':((476,365),(241,331)),
'center second opening top left':((644,223),(427,193)),
'center second opening top right':((745,221),(535,199)),
'center second opening bottom left':((645,369),(420,339)),
'center second opening bottom right':((746,367),(526,346)),
'upper middle belt left':((641,140),(429,110)),
'upper middle belt right':((747,140),(540,116)),
'arch crown outer':((696,442),(459,421)),
'left aperture foot':((638,607),(391,588)),

'left light upper right':((622,494),(387,473))}
uv1=np.array([rot_uv(v[0],'exterior-10-1504','south-2015') for v in pairs.values()])
uv2=np.array([rot_uv(v[1],'exterior-10-2002','north-2020') for v in pairs.values()])
close_controls = {'outer crown visible in both photographs': [(677,357),(667,424)],
'left jamb at outer pavement': [(489,893),(519,836)], 'left jamb at spring': [(488,543),(529,566)]}
for key,(a,b) in close_controls.items():
    pairs[key]=(rot_uv(a,'south-2015','exterior-10-1504').tolist(),rot_uv(b,'north-2020','exterior-10-2002').tolist())
uv1=np.vstack([uv1,*[r[0] for r in close_controls.values()]])
uv2=np.vstack([uv2,*[r[1] for r in close_controls.values()]])
X=np.array([cut(P,p) for p in uv1])
k2,r2=camera('north-2020')
pos2=np.array([2.9,-8.6,2.18]);x0=np.r_[Rotation.from_matrix(r2).as_rotvec(),pos2]
def make(v): 
    R=Rotation.from_rotvec(v[:3]).as_matrix();return k2@np.c_[R,-R@v[3:]]
def residual(v):
    P2=make(v);p=np.array([project(P2,x) for x in X]);return (p-uv2).ravel()
sol=least_squares(residual,x0,loss='soft_l1',f_scale=3.5,max_nfev=1000)
P2=make(sol.x)
def intersect_depth(uvA,uvB):
    a=np.linalg.svd(np.vstack([uvA[0]*P[2]-P[0],uvA[1]*P[2]-P[1],uvB[0]*P2[2]-P2[0],uvB[1]*P2[2]-P2[1]]))[-1][-1];q=a[:3]/a[3]
    return q,np.linalg.norm(project(P,q)-uvA),np.linalg.norm(project(P2,q)-uvB)
record={'axes':'u follows the street toward photo right, d points into the entrance, z is height above outer pavement.','lens_model':'rectilinear extracts from the recorded equirectangular panoramas','scale':{'device_height_metadata_m':2.32,'adopted_road_to_pavement_rise_m':0.13,'adopted_primary_eye_above_pavement_m':2.19,'along_wall_azimuth_deg':357.27,'source':'2015 station device height and local parcel street line; neither the sidewalk rise nor the jamb has a surveyed scale.'},'stations':{},'plane_ties':[]}
for name,cam in [('south-2015',P),('north-2020',P2)]:
 j=load(name);record['stations'][name]={'date':j['station']['date'],'station_id':j['station']['id'],'source':j['station']['ref']['url'],'photo_sha256':j['photo_sha256'],'image_size':[j['width'],j['height']],'original_fov':j['hfov'],'bearing':j['az'],'pitch':j['pitch'],'P_local':cam.tolist()}
for (name,pair),x,v1,v2 in zip(pairs.items(),X,uv1,uv2):
 record['plane_ties'].append({'name':name,'wide_native_pixels':list(pair),'registered_pixels':[v1.tolist(),v2.tolist()],'primary_wall_point':x.tolist(),'second_residual_pixels':float(np.linalg.norm(project(P2,x)-v2))})
record['recess_witnesses']=[]
for desc,a,b in [('left jamb foot of recessed timber door',(537,816),(627,792)),('upper left corner of recessed timber door',(538,424),(645,464))]:
    point,r1,r2=intersect_depth(a,b)
    record['recess_witnesses'].append({'feature':desc,'pixels':[a,b],'point_local_m':point.tolist(),'residual_px':[float(r1),float(r2)]})
record['station_eyes_local_m']=[eye.tolist(),sol.x[3:].tolist()]
record['median_second_view_error_px']=float(np.median([p['second_residual_pixels'] for p in record['plane_ties']]))
(M/'numbered-entrance-two-stations.json').write_text(json.dumps(record,indent=2)+'\n')
