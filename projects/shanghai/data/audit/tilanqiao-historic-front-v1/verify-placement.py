"""Bind the photographed street ornament to its retained frontage without removing source geometry."""
import argparse
import math
import subprocess
import sys
from pathlib import Path

import mapbox_vector_tile
import numpy as np
import shapely
from shapely.geometry import Point, shape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha

ID = 'hongkou-tilanqiao-historic-front'
def actual_distances(mesh, orientation, body):
    xy = mesh[:, :, :2] @ orientation.T
    lows, highs = xy.min(1), xy.max(1)
    xmin,ymin,xmax,ymax = body.bounds
    # Discard distant triangles only after bounding boxes establish a safe lower bound.
    keep = (highs[:,0]>=xmin-45)&(lows[:,0]<=xmax+45)&(highs[:,1]>=ymin-45)&(lows[:,1]<=ymax+45)
    exact = xy[keep]
    if not len(exact):
        return {'total_faces':len(mesh),'nearby_faces':0,'lower_bound_m':45}
    polygons = shapely.polygons(exact)
    with_area = shapely.area(polygons)>1e-9
    ds = []
    if with_area.any():
        ds.extend(shapely.distance(polygons[with_area],body).tolist())
    if (~with_area).any():
        ds.extend(shapely.distance(shapely.linestrings(exact[~with_area]),body).tolist())
    assert min(ds)>.015, min(ds)
    return {'total_faces':len(mesh),'nearby_faces':len(exact),'smallest_actual_distance_m':min(ds)}

def check_native(site,review,body):
    checks=[]
    for group in review['near_tiles']:
        site.link('baseline-far.glb',site.files['far.glb'])
        site.link('macro-READY.json',site.files['READY.json'])
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        write(site.work/'context-features.json',[{'localId':i}for i in group['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ('near','far'):
            tri=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
            checks.append({'tile':group['id'],'variant':variant,**actual_distances(tri,site.axes,body)})
    return checks

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--pbf',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--output',type=Path,default=HERE)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    path=PROJECT/'source/precise'/ID/'footprint-review.json';r=read(path)
    site=PlacementMeshes(PROJECT,a.work,r);assets,bounds,body,ground=site.decode_model(a.manifest)
    # The photographed stonework is a closed street-facing relief. Enclose the small seams
    # between modelled courses and the neutral return using its ground-level silhouette.
    collision=ground.convex_hull
    assert collision.is_valid and not collision.is_empty and shapely.area(collision)<33
    features=sorted((poly.distance(body),key)for key,poly in site.footprints.items())
    assert features[0][1]==1447 and features[0][0]>.015,features[:3]
    native=check_native(site,r,body)
    assert sha(a.pbf)==r['openmaptiles']['sha256']
    tile=mapbox_vector_tile.decode(a.pbf.read_bytes(),default_options={'y_coord_down':True})['building'];extent=tile['extent']
    def to_model(coords):
        lon=2*math.pi*(13721+coords[:,0]/extent)/16384-math.pi
        north=math.pi*(1-2*(6693+coords[:,1]/extent)/16384)
        return (np.column_stack((lon-math.radians(site.lon),north-site.loglat))*site.k)@site.axes.T
    online=sorted((shapely.transform(shape(f['geometry']),to_model).distance(body),f.get('id'))for f in tile['features'])
    assert online[0][0]>.1,online[:2]
    h=r['author_frame']['runtime_heading_deg']
    c={'id':ID,'lng':site.lon,'lat':site.lat,'heading':h,'altitude':0,'scale':1,'replacement_geometry':None,
       'source_feature_ids':{'building':[],'building_part':[]},'collision_geometry':site.wgs(collision),
       'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},
       'overviewBearing':round(h),'overviewPitch':57,'overviewZoom':19.45,'maxDistance':550,
       'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'长阳路历史街面展示。'},
       'placement':{'status':'estimated','note':'2015年临街门楼，根据照片及四期可辨的铺地、街道标线、邻楼对齐。装饰面置于保留的1447临街原体前缘，地块和现有邻楼完整保留。约2至3米级估计。'},
       'partial_model':True,'model_scope':read(a.manifest)['model_scope_zh']}
    write(a.output/'final-placement-contract.json',c)
    write(a.output/'placement-geometry.json',{'id':ID,'completed':True,'manifest_sha256':sha(a.manifest),'script_sha256':sha(Path(__file__)),
       'source_review_sha256':sha(path),'contract_sha256':sha(a.output/'final-placement-contract.json'),'model':assets,
       'all_three_variant_projection_m2':body.area,'ground_silhouette_m2':collision.area,'native_unchanged':native,
       'nearby_city_vectors':[{'local_id':i,'clearance_m':v}for v,i in features[:6]],
       'online_fallback':{'url':r['openmaptiles']['url'],'sha256':sha(a.pbf),'tested_features':len(online),'nearest_distance_m':online[0][0]},
       'original_geometry_removed_m2':0,'property_or_neighbor_selected_for_replacement':False})
    print('geometry',body.area,features[:3],online[0],flush=True)
if __name__=='__main__':main()
