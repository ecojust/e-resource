"""Register the Xinzha Road gate while keeping both houses and the central passage in the original city."""
from pathlib import Path
from argparse import ArgumentParser
from contextlib import ExitStack
import gzip, json, math, os, runpy, subprocess, sys
import mapbox_vector_tile
import numpy as np
import shapely as geo
from shapely.geometry import shape,Point,LineString,box
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry
section=runpy.run_path(str(HERE.parent/'sino-french-school-v1/verify-placement.py'))['solid_section']
load_triangles=runpy.run_path(str(HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
cam=runpy.run_path(str(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py'))
city_crossings=runpy.run_path(str(HERE.parent/'daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
ID='jingan-qinyuan-lane-entrance'
MARKS=[('south arch crest',0,-.015,4.18),('suspended wood oval',.04,.203,3.29),('west square iron post',-1.97,-.040,1.24),('east square iron post',1.97,-.040,1.24),('threshold opening',-.45,.60,.82),('east open leaf rail',1.25,1.12,1.39),('red facing brick',-3.33,-.013,.80),('historic building plaque',-3.943,-.06,1.93),('green address plaque',-3.316,-.041,2.0),('Ruan Lingyu memorial',-2.595,-.087,2.)]

def walk_samples():
    rows=[]
    def add(name,x,y,blocked):rows.append(dict(name=name,x=float(x),y=float(y),blocked=blocked))
    for y in [-2,-.4,0,.25,.55,.9,1.45,1.85,2.2,3.6,5.1,8.4]:
        for x in [-1.15,-.55,.05,.39]:add('street through inner lane',x,y,False)
    for x in [-4.3,-3.9,-3.2,-2.33]:add('west plaque wall',x,.1,True)
    for x in [-1.97,1.97]:
        for y in [.03,.25,.46]:add('iron post footing',x,y,True)
    for t in np.linspace(.03,.97,7):
        x=1.75-.96946*t; y=.35+1.49283*t
        add('opened east gate leaf',x,y,True)
        add('clear behind open gate',x+.21,y+.19,False)
        if t>.22:add('walkable beside open gate',x-.20,y-.12,False)
    return rows

def original_meshes(site,ref,model,corridor,checklist,views):
    records=[]
    for group in ref['near_tiles']:
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        site.link('baseline-far.glb',site.files['far.glb']);site.link('macro-READY.json',site.files['READY.json'])
        ids=group['feature_local_ids'];write(site.work/'context-features.json',[{'localId':i}for i in ids])
        with ExitStack()as end:
            for role in ('near','far'):
                for suffix in ('owners.u32','triangles.f64'):
                    file=site.work/f'baseline-{role}-{suffix}'
                    fd=os.memfd_create('qinyuan-neighbor-triangles');end.callback(os.close,fd)
                    assert not file.exists() and not file.is_symlink()
                    file.symlink_to(f'/proc/{os.getpid()}/fd/{fd}');end.callback(file.unlink)
            subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
            for role in ('near','far'):
                tri=np.fromfile(site.work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
                tri[:,:,:2]=tri[:,:,:2]@site.axes.T
                floors=geo.convex_hull(geo.multipoints(tri[:,:,:2]))
                model_min=float(geo.distance(floors,model).min());walk_min=float(geo.distance(floors,corridor).min())
                assert min(model_min,walk_min)>.10,(role,model_min,walk_min)
                hits=[]
                for view in views:
                    e,n,z=view['camera_enu'];eye=np.r_[np.array([e,n])@site.axes.T,z]
                    for name,x,y,z in MARKS:
                        idx,_=city_crossings(eye,np.array([x,y,z]),tri)
                        assert not len(idx),(role,view['view'],name)
                        hits.append(dict(view=view['view'],name=name,original_triangle_intersections=len(idx)))
                records.append(dict(group=group['id'],ids=ids,role=role,original_triangles=len(tri),minimum_model_distance_m=model_min,minimum_walk_corridor_distance_m=walk_min,removed_original_triangles=0,camera_checks=hits))
    return records

def vector_context(tile,site,envelope,corridor):
    expected='21ae0cc5b91bfb8c85d320d3d0295804e5af8d04fcca02fb316f3e5ef80449e2'
    assert sha(tile)==expected
    layer=mapbox_vector_tile.decode(tile.read_bytes(),default_options={'y_coord_down':True})['building']
    def local(c):
        x=(13719+c[:,0]/layer['extent'])/2**14;y=(6694+c[:,1]/layer['extent'])/2**14
        return site.to_xy(np.column_stack((x*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*y)))))))
    rows=[];total=0;neigh=[]
    for f in layer['features']:
        poly=geo.transform(shape(f['geometry']),local);parts=geo.get_parts(poly);total+=len(parts)
        for i,a in enumerate(parts):
            rg=envelope.distance(a);rw=corridor.distance(a)
            if min(rg,rw)<150:
                neigh.append((f['id'],a,float(f['properties'].get('render_height')or f['properties'].get('height') or 12)))
                rows.append(dict(id=f['id'],component=i,model_clearance_m=rg,walk_corridor_clearance_m=rw,model_overlap_m2=a.intersection(envelope).area,passage_overlap_m2=a.intersection(corridor).area))
    rows.sort(key=lambda r:r['model_clearance_m'])
    return dict(tile_sha256=expected,original_building_features=len(layer['features']),original_polygon_parts=total,neighbor_parts=rows),neigh

def main():
    args=ArgumentParser(description=__doc__)
    for f in ('manifest','work','vector'):args.add_argument('--'+f,type=Path,required=True)
    args.add_argument('--out',type=Path,default=HERE);arg=args.parse_args()
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json');site=PlacementMeshes(PROJECT,arg.work,ref)
    manifest=read(arg.manifest);assert manifest['id']==ID
    sections=[];envelopes=[];model_bindings=[];bounds=[]
    for role,path in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
        receipt=manifest['assets'][role];delivery=arg.manifest.parent/receipt['file'];assert sha(delivery)==receipt['sha256']
        tri,_,_,decoded=load_triangles(arg.manifest.parent/path)
        assert len(tri)==receipt['triangles']
        envelopes.append(geo.convex_hull(geo.multipoints(tri[:,:,:2].reshape(-1,2))))
        bounds.append(receipt['bounds_gltf_m']);model_bindings.append(dict(role=role,delivery_sha256=sha(delivery),decoded_sha256=decoded['sha256'],triangles=len(tri)))
        for h in (.06,.09,.102):
            sections.append(section(tri,h))
    collision=geo.union_all(sections,grid_size=.00001).simplify(.001,preserve_topology=True)
    assert collision.is_valid
    corridor=box(-1.43,-2,.14,8.4)
    envelope=geo.union_all(envelopes)
    assert not collision.intersects(corridor)
    samples=walk_samples()
    for s in samples:
        assert collision.covers(Point(s['x'],s['y']))==s['blocked'],s
    tile,parts=vector_context(arg.vector,site,envelope,corridor)
    write(arg.out/'fallback-buildings.json',tile)
    print('fallback closest',tile['neighbor_parts'][:3],flush=True)
    assert all(r['model_overlap_m2']<.00001 and r['passage_overlap_m2']<.00001 for r in tile['neighbor_parts'])
    heights={f['localId']:f['height']for f in json.loads(gzip.decompress(site.files['feature-table.json.gz'].read_bytes()))['features']}
    neighbors=[(i,geo.transform(g,lambda v:v@site.axes),heights[i])for i,g in site.footprints.items()if g.distance(Point(0,0))<145]
    bb=np.array(bounds);mapped={'raw':'raw','full':'web','lod':'lod'}
    contract=dict(id=ID,replacement_geometry=None,collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,altitude=0,scale=1,heading=ref['author_frame']['runtime_heading_deg'],bounds_glb=dict(min=bb[:,0].min(0).tolist(),max=bb[:,1].max(0).tolist()),model_geometry_sha256={mapped[r['role']]:r['delivery_sha256']for r in model_bindings},overviewBearing=-15.12,overviewPitch=37,overviewZoom=21.5,maxDistance=440,lod_switch_in_m=202,lod_switch_out_m=285,partial_model=True,model_scope=manifest['model_scope_zh'],navigation=dict(listed=False,status='从新闸路经拱门中央沿原弄道进入，开启的东侧铁门维持固定的斜向位置。'),placement=dict(status='estimated',note='以三站街景交会定位新闸路1124弄铁门与三牌所在的局部墙段。原城相邻两房及回退底图完整保留。'))
    checked_geometry(contract['collision_geometry'],ID,collision=True)
    write(arg.out/'final-placement-contract.json',contract)
    targets=[(n,*map(float,np.array([x,y])@site.axes),z)for n,x,y,z in MARKS]
    def cameras(neigh):
        deg=math.pi/180*6371008.8
        return [cam['evaluate'](contract,dict(width=w,height=h,insets=dict(zip(['left','right','top','bottom'],pads))),label,neigh,site.lon,site.lat,deg*math.cos(math.radians(site.lat)),deg,targets)for label,w,h,pads in cam['VIEWS']]
    views=cameras(neighbors)
    fallback_views=cameras([(i,geo.transform(g,lambda v:v@site.axes),h)for i,g,h in parts])
    write(arg.out/'overview-sightlines.json',dict(views=views,fallback_views=fallback_views,source_sha=sha(site.files['feature-table.json.gz']),actual_camera_sha=sha(PROJECT/'src/candidate-overview-camera.js')))
    assert all(r['clear_count']==len(MARKS)for r in views+fallback_views),[(r['view'],r['clear_count'],[z for z in r['probes'] if not z['clear']])for r in views+fallback_views]
    native=original_meshes(site,ref,envelope,corridor,samples,views)
    fallback_best=tile['neighbor_parts'][0]
    write(arg.out/'placement-geometry.json',dict(passed=True,id=ID,manifest_sha256=sha(arg.manifest),contract_sha256=sha(arg.out/'final-placement-contract.json'),models=model_bindings,collision_components=len(geo.get_parts(collision)),collision_area_m2=collision.area,physical_collision_slice_heights_m=[.06,.09,.102],ground_samples=samples,continuous_clear_corridor_xy_m=list(corridor.exterior.coords),verified_width_m=1.57,verified_length_m=10.4,passage_to_collision_clearance_m=collision.distance(corridor),original_city=native,neighbor_footprints=[dict(id=i,model_clearance_m=site.footprints[i].distance(envelope),walk_clearance_m=site.footprints[i].distance(corridor))for i in ref['closest_neighbors']],source_removed=0,fallback_review_sha256=sha(arg.out/'fallback-buildings.json'),fallback_nearest=fallback_best,source_ordinary_owner=None))
    print('original meshes',[(r['role'],r['original_triangles'],r['minimum_model_distance_m'])for r in native],'walking',len(samples),flush=True)
if __name__=='__main__':main()
