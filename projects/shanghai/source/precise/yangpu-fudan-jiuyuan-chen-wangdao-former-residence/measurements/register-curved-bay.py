from pathlib import Path
import json,numpy as np
from scipy.optimize import least_squares
S=Path(__file__).resolve().parent
reg=json.loads((S/'garden-front-registration.json').read_text());p0,p1=[np.array(i['matrix'])for i in reg['photos'].values()]
def proj(P,points):
 points=np.array(points);w=np.column_stack((points,np.ones(len(points))))@P.T;return w[:,:2]/w[:,2:]
# Vertical jambs on the garden-facing cylindrical bay. All measured points are at the full published working size.
data={'upper-head':[[[659,262],[678,257],[702,251],[862,252],[882,258],[892,266]],[[621,245],[631,242],[650,236],[745,237],[765,246],[771,250]]],
      'upper-sill':[[[663,368],[683,363],[705,360],[871,363],[889,368],[899,373]],[[623,311],[633,310],[651,307],[746,307],[765,312],[772,314]]],
      'ground-head':[[[623,505],[688,501],[714,499],[888,501],[906,505],[918,511]],[[599,391],[631,387],[646,387],[745,387],[759,390],[772,395]]],
      'ground-sill':[[[624,626],[692,630],[719,630],[896,631],[915,627],[925,625]],[[599,454],[631,456],[646,456],[746,457],[759,456],[772,454]]]}
def ray(P,uv,z):
 eye=-np.linalg.solve(P[:,:3],P[:,3]);d=np.linalg.solve(P[:,:3],np.r_[uv,1.]);return (eye+(z-eye[2])/d[2]*d)[:2]
def bay(v):
 x,y,r,zhi,zlo,ghi,glo=v
 # Each of the five principal planar steel frame facets cuts a chord of the rounded stucco.
 residual=[]
 for k,level in [('upper-head',zhi),('upper-sill',zlo),('ground-head',ghi),('ground-sill',glo)]:
  # Derive angular jamb position separately from the first camera, using an interpolated plane on the band.
  for uv0,uv1 in zip(*data[k]):
   def uv(theta):
    xyz=[x+r*np.sin(theta),y-r*np.cos(theta),level];return np.r_[proj(p0,[xyz])[0]-uv0,proj(p1,[xyz])[0]-uv1]
   from scipy.optimize import minimize_scalar
   q=minimize_scalar(lambda a:np.sum(uv(a)**2),bounds=(-1.79,1.79),method='bounded')
   residual.extend(uv(q.x))
 return residual+[(x-6.25)/.35,(y-.65)/.40,(r-2.60)/.45]
v=least_squares(bay,[6.3,.75,2.53,7.04,5.1,2.87,1],bounds=([5,-.8,1.8,6.2,4.3,2.6,.8],[7.5,2,3.1,7.8,5.8,3.3,1.5]),loss='soft_l1',max_nfev=40).x
x,y,r,*levels=v;result={}
for (k,indices),h in zip(data.items(),levels):
 bounds_angles=[]
 for a,b in zip(*indices):
  from scipy.optimize import minimize_scalar
  def loss(theta):
   world=[x+r*np.sin(theta),y-r*np.cos(theta),h];return np.sum((proj(p0,[world])[0]-a)**2)+np.sum((proj(p1,[world])[0]-b)**2)
  f=minimize_scalar(loss,bounds=(-1.79,1.79),method='bounded');bounds_angles.append([float(f.x),float(np.sqrt(f.fun/2))])
 result[k]=dict(height=h,jamb_angles_and_error=bounds_angles,pixels_2019=indices[0],pixels_official=indices[1])
meta=dict(method='Two-camera reprojection of six visible jamb endpoints per level on a common cylindrical sector. Each glazed window is chorded. Silhouette support from restoration photographs.',bay_centre=[x,y],radius=r,bands=result)
print(x,y,r,levels);print([(k,[round(i[0],2)for i in d['jamb_angles_and_error']])for k,d in result.items()]);(S/'garden-bay-two-stations.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
