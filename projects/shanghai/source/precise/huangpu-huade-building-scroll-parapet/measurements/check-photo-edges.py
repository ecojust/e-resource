"""Project the actual mesh faces onto the 2015 photograph and compare aperture edges and soffit ornament."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from scipy.optimize import linear_sum_assignment

parser=argparse.ArgumentParser(description=__doc__)
for key in ('project','source','photo','mesh','output'):
    parser.add_argument('--'+key,type=Path,required=True)
a=parser.parse_args()
sys.path.insert(0,str(a.source))
from photo_plane import H,D,position
helpers=runpy.run_path(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
load=helpers['load_triangles']
tri,materials,names,identity=load(a.mesh)
def project(t):
    p=t.reshape(-1,3)
    xyw=np.column_stack((p[:,0],p[:,2],np.ones(len(p)))) @ H.T + p[:,1,None]*D
    return (xyw[:,:2]/xyw[:,2,None]).reshape(t.shape[:-1]+(2,))
def merged(mask):
    polys=[Polygon(t) for t in project(tri[mask])]
    return unary_union([p for p in polys if p.area>1.e-6])
def pieces(geo):
    if geo.is_empty:return []
    return [geo] if geo.geom_type=='Polygon' else list(geo.geoms)

obs=json.loads(a.photo.read_bytes())
name=np.asarray(names)[materials]
mask=(np.max(abs(tri[:,:,1]),axis=1)<.0004) & (name=='Ivory washed limestone')
front=merged(mask)
front=front.buffer(.004,join_style='mitre').buffer(-.004,join_style='mitre')
apertures=[]
for tracks in obs['apertures']:
    # The opening can cross object boundaries if a lower masonry course is separate.
    # Search all vertical intervals of the plane complement near the actual reference ray.
    measurements=[]
    for r in tracks:
        x=r['x'];top,bottom=r['upper_y'],r['lower_y'];line=LineString([(x,top-27),(x,bottom+27)])
        void=line.difference(front)
        sections=[void] if void.geom_type=='LineString' else list(void.geoms)
        candidates=[(s.bounds[1],s.bounds[3])for s in sections if s.geom_type=='LineString' and s.length>.4 and s.bounds[1]>top-26.9 and s.bounds[3]<bottom+26.9]
        pair=min(candidates,key=lambda v:abs(v[0]-top)+abs(v[1]-bottom),default=None)
        measurements.append(dict(x=int(x),photo_upper=top,photo_lower=bottom,model_pair=[round(q,3)for q in pair] if pair else None,
                                 error_px=[round(abs(pair[0]-top),3),round(abs(pair[1]-bottom),3)] if pair else None))
    apertures.append(measurements)
# Flat circular faces have distinct connected components in projection.
flat=name=='Soffit roundel face'
visible_z=tri[flat,:,2].min()
discs=pieces(merged(flat & (np.max(abs(tri[:,:,2]-visible_z),axis=1)<.0004)).buffer(.02,join_style='mitre'))
discs=[d for d in discs if d.geom_type=='Polygon' and d.area>8]
normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
sides=helpers['material_appearance'](a.mesh)['materials']
double=np.array([sides[mat]['doubleSided'] for mat in names])[materials]
def visible_at(x,y):
    origin=position(x,y,-2.4); direction=position(x,y,1.4)-origin; direction/=np.linalg.norm(direction)
    kept=np.flatnonzero((normals@direction < -1.e-12) | double)
    idx,dist,point=helpers['first_hit'](tri[kept],origin,direction)
    return name[kept[idx]] if np.isfinite(dist) else None
marks=[p['shadow_crown']for group in obs['soffit_boss_crowns']for p in group]
cost=np.array([[Point(pt).distance(p.centroid) for p in discs]for pt in marks])
bosses=[]
for i,j in zip(*linear_sum_assignment(cost)):
    p=discs[j];x,y=marks[i];cx,cy=p.centroid.coords[0]
    bosses.append(dict(panel=int(i//9),index=int(i%9),observed_shadow=[x,y],flat_roundel_centre=[round(cx,3),round(cy,3)],
                       shadow_ray=visible_at(x,y),face_ray=visible_at(x,y+7),centre_minus_shadow_px=[round(cx-x,3),round(cy-y,3)],
                       distance_to_disk_px=round(p.distance(Point(x,y)),3),bounds=[round(z,3) for z in p.bounds]))
errors=[v for part in apertures for r in part if r['error_px']for v in r['error_px']]
record=dict(asset=identity['sha256'],apertures=apertures,model_roundel_count=len(discs),soffit_bosses=bosses,
            edge_count=len(errors),edge_rms=float(np.sqrt(np.mean(np.square(errors)))) if errors else None,
            edge_p95=float(np.percentile(errors,95)) if errors else None,edge_max=max(errors,default=None),
            worst_shadow_distance_to_flat_face=max((b['distance_to_disk_px']for b in bosses),default=None))
a.output.write_text(json.dumps(record,indent=2)+'\n')
print('edges',len(errors),record['edge_rms'],record['edge_p95'],record['edge_max'],'discs',len(discs),record['worst_shadow_distance_to_flat_face'])
print('rim bounds by panel',[[r['model_pair']for r in g]for g in apertures])
print('offset range',[(min(b['centre_minus_shadow_px'][k]for b in bosses),max(b['centre_minus_shadow_px'][k]for b in bosses))for k in (0,1)])

print('actual first hits',[(k,sum(b[k] in ('Soffit roundel face','Roundel turned bevel') for b in bosses)) for k in ('shadow_ray','face_ray')])
