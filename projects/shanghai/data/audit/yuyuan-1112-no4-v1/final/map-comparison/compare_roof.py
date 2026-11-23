"""Compare the completed four-corner roof planes with the four independently mapped site polygons."""
from pathlib import Path
import hashlib,json,math,runpy,sys
import numpy as np
from shapely.geometry import Polygon,shape,mapping
from shapely.ops import transform,unary_union
import argparse
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('shanghai_project',type=Path)
cli.add_argument('model',type=Path)
cli.add_argument('output',type=Path)
args=cli.parse_args()
s=args.shanghai_project.absolute()/'source/precise/changning-yuyuan-1112-no4'
sys.path.insert(0,str(s/'source'))
import street_control as control
helper=runpy.run_path(str(s.parents[2]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
p=args.model;T,ids,names,_=helper(p)
f=control.CONTROL;angle=control.P['east_baseline_azimuth_from_east_radians']
axis=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
reference=np.array(control.final_xyz([5.53,-3.30,4.25])[:2]);offset=np.array(f['control_points']['waist_west_outer_corner_top'][:2])-axis@reference
lon,lat=f['origin_WGS84'];sx=111319.49*math.cos(math.radians(lat));sy=110874
polys=[]
for tri,i in zip(T,ids):
 if names[i]!='weathered red roof tile':continue
 pol=Polygon(tri[:,:2]@axis.T+offset)
 if pol.area>1e-6:polys.append(pol)
roof=unary_union(polys)
def metric(x,y,z=None):return ((np.asarray(x)-lon)*sx,(np.asarray(y)-lat)*sy)
def wgs(x,y,z=None):return (np.asarray(x)/sx+lon,np.asarray(y)/sy+lat)
geo=json.loads((s/'measurements/ordinary-owners-and-register.geojson').read_bytes())
out=[]
for v in geo['features']:
 key=v['properties'].get('localId','registered-boundary')
 poly=transform(metric,shape(v['geometry']));intersection=poly.intersection(roof)
 out.append(dict(owner=key,source_area_m2=poly.area,roof_area_m2=roof.area,overlap_m2=intersection.area,source_area_outside_roof_m2=poly.difference(roof).area,roof_area_outside_source_m2=roof.difference(poly).area,minimum_distance_m=roof.distance(poly)))
geo['features'].append(dict(type='Feature',properties=dict(kind='roof projection',source_model_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),geometry=mapping(transform(wgs,roof.simplify(.01,preserve_topology=True)))))
outdir=args.output;outdir.mkdir(exist_ok=True)
(outdir/'roof-and-three-owners.geojson').write_text(json.dumps(geo,ensure_ascii=False,indent=2)+'\n')
(outdir/'measured-roof-overlap.json').write_text(json.dumps(dict(local_origin_wgs84=[lon,lat],axis_xy=axis.tolist(),offset_xy=offset.tolist(),mesh_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),control_station_file='forward-wing-constrained.json',comparison=out,limits='Roof eaves and gross footprint include different plan limits. This is a check on the effect of replacing the city source, not a cadastral survey.'),ensure_ascii=False,indent=2)+'\n')
print([(r['owner'],round(r['roof_area_m2'],2),round(r['source_area_m2'],2),round(r['overlap_m2'],2),round(r['minimum_distance_m'],2))for r in out])
