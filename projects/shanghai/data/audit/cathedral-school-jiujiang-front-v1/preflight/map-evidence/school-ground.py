"""Measure the three delivered doors and register only the central Jiujiang Road façade."""
import gzip, hashlib, json, math, runpy, sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box, mapping, shape

work = Path(__file__).resolve().parent
pilot = Path(sys.argv[1]) if len(sys.argv)>1 else work.parent/'pilot'
project = Path('/workspace/e-resource/projects/shanghai')
read = lambda p: json.loads(p.read_bytes())
sign = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def put(name, contents):
    (work/name).write_text(json.dumps(contents,ensure_ascii=False,indent=1)+'\n')
review = read(work/'original-review.json')
conversion = read(work/'frame-conversion.json')
manifest = read(pilot/'manifest.json')
model = manifest['id']
source = project/'source/precise'/model/'source'
d = read(source/'dimensions.json')
door = d['door']
gables = [d['west_gable'],d['east_gable']]
left, right = gables[0]-d.get('west_data',{}).get('width',d['gable_width'])/2, gables[1]+d.get('east_data',{}).get('width',d['gable_width'])/2
side_doors = [gables[0]-1.92,gables[1]+1.92]
frame = review['author_frame'].copy()
lon,lat=conversion['osm_west']
frame.update(anchor={'lng':lon,'lat':lat},runtime_heading_deg=frame['runtime_heading_deg']-conversion['angle_osm_axis_relative_to_raw_degrees'],x_axis='OSM 292718777@4 north wall, western end to eastern end',source_west=conversion['osm_west'],source_east=conversion['osm_east'],coordinate_conversion='frame-conversion.json')
h=math.radians(frame['runtime_heading_deg']); c,s=math.cos(h),math.sin(h)
k=6371008.8*math.cos(math.radians(lat));north=math.asinh(math.tan(math.radians(lat)))
def ll(q):
    x,y=q.T
    return np.column_stack((lon+np.degrees((x*c+y*s)/k),np.degrees(np.arctan(np.sinh(north+(-x*s+y*c)/k)))))
def xy(q):
    lng,latitude=q.T;e=np.radians(lng-lon)*k;n=(np.arcsinh(np.tan(np.radians(latitude)))-north)*k
    return np.column_stack((e*c-n*s,e*s+n*c))
world=lambda g:mapping(shapely.transform(g,ll))
source_row=next(o for o in review['owners'] if o['local_id']==1810)
native=shapely.transform(shape(source_row['geometry_wgs84']),xy)
vector_rows = read(work/'map-visible-components.json') if (work/'map-visible-components.json').exists() else []
selected = read(work/'vector-and-osm-owners.json') if vector_rows else None
if selected:
    vec=next(r for r in selected['native_to_vector'] if r['native_id']==1810)
    vector=shapely.transform(shape(next(r['geometry'] for r in vector_rows if r['id']==vec['mvt_feature_id'] and r['component']==vec['component'])),xy)
else: vector=native
sys.path.insert(0,str(project/'tools'))
from build_candidate_city_integrations import checked_geometry
Scene=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def sections(tris,z):
    triangles=tris[(tris[:,:,2].min(1)<z)&(tris[:,:,2].max(1)>z)]
    segments=[]
    for t in triangles:
        points=[]
        for a,b in zip(t,np.roll(t,-1,axis=0)):
            if (a[2]<z)!=(b[2]<z):points.append(a[:2]+(z-a[2])/(b[2]-a[2])*(b[:2]-a[:2]))
        if len(points)==2 and np.linalg.norm(points[0]-points[1])>1e-7:segments.append(LineString(points))
    return shapely.union_all(segments,grid_size=1e-6)

lod_footprints={};profile_metrics={};tri_rays={};scenes={}
for role,file,decoded in [('raw','raw.glb','raw.glb'),('full','full.glb','decoded-full.glb'),('lod','lod.glb','decoded-lod.glb')]:
    asset=manifest['assets'][role];assert sign(pilot/file)==asset['sha256'];scene=Scene(pilot/decoded);scenes[role]=scene
    assert len(scene.tri)==asset['triangles']
    # At pedestrian height the deepest opaque timber face controls access. Include the near-floor
    # plinth and raised joints (the walkable stone thresholds are below both sections).
    sections_z=[.2317,1.0713];lines=shapely.union_all([sections(scene.tri,z) for z in sections_z],grid_size=1e-6)
    coords=shapely.get_coordinates(lines);line_bounds=lines.bounds
    x0,x1=line_bounds[0]+.00001,line_bounds[2]-.00001
    assert abs(x0-left)<.03 and abs(x1-right)<.03,(x0,x1,left,right)
    xs=set(np.linspace(x0,x1,121));eps=.000025
    for x in coords[:,0]:
        for a in (x-eps,x+eps):xs.add(min(x1,max(x0,a)))
    front=[]
    for x in sorted(xs):
        cross=shapely.get_coordinates(lines.intersection(LineString([(x,line_bounds[1]-1),(x,line_bounds[3]+1)])))
        assert len(cross),(role,x);front.append([x,float(cross[:,1].max())])
    front[0][0]=left;front[-1][0]=right
    rays=[]
    for name,x in [('west square door',side_doors[0]),('pointed door',door),('east square door',side_doors[1])]:
        for dx in [-.28,0,.28]:
            for z in [.33,1.07,1.77]:
                hit=scene.ray([x+dx,line_bounds[3]+1.5,z],[0,-1,0],6)
                assert hit and any(t in hit['material'] for t in ['door','entry','wood','timber','iron','metal']), (name,hit)
                rays.append({'feature':name,'x':x+dx,'z':z,**hit})
    tri_rays[role]=rays
    lod_footprints[role]=front
    profile_metrics[role]=dict(signed_sha256=sign(pilot/file),decoded_sha256=sign(pilot/decoded),triangles=len(scene.tri),sections=sections_z,front_y=[min(a[1] for a in front),max(a[1] for a in front)],rays=rays)
# The mask ends just behind the deepest opaque entrance. The existing wing and its roof continue
# beyond this line. Test all three sources and account for small differences in compressed coordinates.
lo=min(v['front_y'][0] for v in profile_metrics.values());hi=max(v['front_y'][1] for v in profile_metrics.values());front_y=max(hi+.12,1.5)
back=min(lo-.18,-.37);mask=box(left,back,right,front_y)
polygons={k:Polygon(v+[(right,back-.003),(left,back-.003)]) for k,v in lod_footprints.items()}
for g in polygons.values():assert g.is_valid
collision=shapely.union_all(list(polygons.values()),grid_size=1e-6).simplify(.0012,preserve_topology=True)
assert collision.geom_type=='Polygon' and collision.is_valid
remaining=native.difference(mask);assert not remaining.is_empty
local=lambda y,x:Point(float(x),float(y))
cases=[]
def sample(x,y,expected,label):
    q=local(y,x);after=[remaining.covers(q) or polygons[role].covers(q) for role in polygons];phys=remaining.covers(q) or collision.covers(q)
    assert all(v==expected for v in after) and phys==expected,(x,y,expected,after,phys)
    cases.append(dict(label=label,x=float(x),y=float(y),control_blocked=native.covers(q),control_vector_blocked=vector.covers(q),original_cut=mask.covers(q),after_full=phys,after_lod=phys,after_vector=vector.difference(mask).covers(q) or collision.covers(q)))
for j,(name,x) in enumerate([('west square door',side_doors[0]),('pointed door',door),('east square door',side_doors[1])]):
    for dx in [-.28,0,.28]:
        hits=[next(v for v in rows if v['feature']==name and v['x']==x+dx and v['z']==1.07)['point_enu_m'][1] for rows in tri_rays.values()]
        sample(x+dx,max(hits)+.11,False,name+' outer recess');sample(x+dx,min(hits)-.12,True,name+' opaque leaf');sample(x+dx,front_y+.18,False,name+' street approach')
for x in [left+.4,gables[0]-.20,(gables[0]+gables[1])*.5-4.0,door+2.35,gables[1]+.22,right-.4]:
    front=float(scenes['raw'].ray([x,front_y+1,1.07],[0,-1,0],6)['point_enu_m'][1]);sample(x,front+.23,False,'pavement outside masonry');sample(x,front-.16,True,'masonry');sample(x,back-.35,True,'retained interior')
for x in [2,12,left-1.4,right+1.4,62,70]:
    sample(x,2,False,'unchanged pavement');sample(x,-2.7,True,'unchanged wing')
for x in [gables[0],door,gables[1]]:sample(x,-5.8,True,'unchanged rear body')
geom=world(collision);checked_geometry(geom,'school entrance collision',collision=True)
placement=dict(id=model,lng=lon,lat=lat,heading=frame['runtime_heading_deg'],scale=1,altitude=0,author_frame=frame,owner=dict(macro_id=review['frozen_macro'],feature_local_id=1810),source_feature_ids=dict(building=[review['owner']['source_key'].split(':')[-1]],building_part=[]),replacement_geometry=world(mask),collision_geometry=geom,bounds_glb=dict(zip(['min','max'],manifest['assets']['full']['bounds_gltf_m'])),model_geometry_sha256={role:profile_metrics[k]['signed_sha256'] for role,k in [('raw','raw'),('web','full'),('lod','lod')]})
put('ground-placement-fragment.json',placement);put('ground-cases.json',dict(ground=cases));put('school-author-frame.json',frame)
put('measured-entrance-ground.json',dict(ground_sections=profile_metrics,native_original_area_m2=native.area,remaining_m2=remaining.area,removed_m2=native.intersection(mask).area,source_usable_fraction=remaining.area/native.area,collision_area_m2=collision.area,collision_vertices=len(collision.exterior.coords),mask_xy_m=list(mask.bounds),native_manifest_sha256=sign(pilot/'manifest.json'),dimensions_sha256=sign(source/'dimensions.json'),tested_points=len(cases),raw_lod_area_difference=polygons['raw'].symmetric_difference(polygons['lod']).area));print([(k,v['front_y']) for k,v in profile_metrics.items()], 'tested',len(cases),'remaining',remaining.area/native.area,flush=True)
