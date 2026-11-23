"""Check the photographed closed Lane 198 gate against both original geometry levels and the street map."""
from pathlib import Path
from argparse import ArgumentParser
from contextlib import ExitStack
import gzip, json, math, os, runpy, subprocess, sys
import mapbox_vector_tile
import numpy as np
import shapely as geo
from shapely.geometry import shape,Point,LineString,box
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get("SHANGHAI_PROJECT_ROOT",HERE.parents[2]))
AUDITS=PROJECT/"data/audit"
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry
section=runpy.run_path(str(AUDITS/'sino-french-school-v1/verify-placement.py'))['solid_section']
load_triangles=runpy.run_path(str(AUDITS/'postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
cam=runpy.run_path(str(AUDITS/'pure-heart-church-v1/check-overview-sightlines.py'))
city_crossings=runpy.run_path(str(AUDITS/'daxin-tobacco-northeast-tower-v1/check-physical-city-rays.py'))['crossings']
ID='huangpu-anhe-terrace-ruijin-gate'
MARKS=[('south pier address',-2.5,-.037,2.67),('blue lower address',-2.5,-.035,1.89),
       ('north coping',2.515,-.060,3.95),('south coping',-2.50,-.04,3.90),
       ('south wicket lock',-1.42,.344,2.3),('gilt upper scroll',1.0,.402,2.07),
       ('north flat rail',1.43,.399,2.85),('north lance',1.82,.421,3.00),
       ('meeting stile',.045,.399,1.23),('lower horizontal',-.62,.399,.11)]

def walk_samples():
    rows=[]
    def add(name,x,y,blocked):
        rows.append(dict(name=name,x=float(x),y=float(y),blocked=blocked))
    for x in [-1.8,-1.2,-.6,0,.6,1.2,1.8]:
        for y in [-1.75,-.35,.15,.70,1.30,1.90]:
            add('street or inside approach',x,y,False)
    for x in [-2.85,-2.50,-2.17,2.19,2.515,2.86]:
        for y in [.05,.38,.69]:add('foot of observed pier',x,y,True)
    for x in [-1.97,-1.63,-1.15,-.65,-.08,.08,.65,1.15,1.63,1.97]:
        add('closed leaf lower rail',x,.43,True)
    add('small gap between the two closed leaves',0,.43,False)
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
                    fd=os.memfd_create('anhe-neighbor-triangles');end.callback(os.close,fd)
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
    expected='36448c327185ab13a8d07e723bda4d00dec0c1d36c6831a4c6aa50de13a07893'
    raw=tile.read_bytes()
    if raw.startswith(b'\x1f\x8b'): raw=gzip.decompress(raw)
    from hashlib import sha256
    assert sha256(raw).hexdigest()==expected
    layer=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
    def local(c):
        x=(13719+c[:,0]/layer['extent'])/2**14;y=(6695+c[:,1]/layer['extent'])/2**14
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
    args.add_argument('--out',type=Path,default=HERE)
    args.add_argument('--source',type=Path,default=PROJECT/'source/precise'/ID/'footprint-review.json')
    arg=args.parse_args()
    ref=read(arg.source);site=PlacementMeshes(PROJECT,arg.work,ref)
    manifest=read(arg.manifest);assert manifest['id']==ID
    sections=[];envelopes=[];model_bindings=[];bounds=[]
    for role,path in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
        receipt=manifest['assets'][role];delivery=arg.manifest.parent/receipt['file'];assert sha(delivery)==receipt['sha256']
        tri,_,_,decoded=load_triangles(arg.manifest.parent/path)
        assert len(tri)==receipt['triangles']
        envelopes.append(geo.convex_hull(geo.multipoints(tri[:,:,:2].reshape(-1,2))))
        gltf=tri[:,:,[0,2,1]]*np.array([1,1,-1]);bounds.append([gltf.min((0,1)).tolist(),gltf.max((0,1)).tolist()]);model_bindings.append(dict(role=role,delivery_sha256=sha(delivery),decoded_sha256=decoded['sha256'],triangles=len(tri)))
        for h in (.100,.111,.128):
            sections.append(section(tri,h))
    collision=geo.union_all(sections,grid_size=.00001).simplify(.001,preserve_topology=True)
    assert collision.is_valid
    front=box(-1.84,-1.8,1.84,.22); courtyard=box(-1.84,.68,1.84,1.94)
    corridor=geo.union_all([front,courtyard])
    envelope=geo.union_all(envelopes)
    assert not collision.intersects(corridor)
    samples=walk_samples()
    for s in samples:
        assert collision.covers(Point(s['x'],s['y']))==s['blocked'],s
        s['wgs84']=site.to_wgs(np.asarray([[s['x'],s['y']]]))[0].tolist()
    tile,parts=vector_context(arg.vector,site,envelope,corridor)
    write(arg.out/'fallback-buildings.json',tile)
    print('fallback closest',tile['neighbor_parts'][:3],flush=True)
    assert all(r['model_overlap_m2']<.00001 and r['passage_overlap_m2']<.00001 for r in tile['neighbor_parts'])
    heights={f['localId']:f['height']for f in json.loads(gzip.decompress(site.files['feature-table.json.gz'].read_bytes()))['features']}
    neighbors=[(i,geo.transform(g,lambda v:v@site.axes),heights[i])for i,g in site.footprints.items()if g.distance(Point(0,0))<145]
    bb=np.array(bounds);mapped={'raw':'raw','full':'web','lod':'lod'}
    contract=dict(id=ID,replacement_geometry=None,collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,altitude=0,scale=1,heading=ref['author_frame']['runtime_heading_deg'],bounds_glb=dict(min=bb[:,0].min(0).tolist(),max=bb[:,1].max(0).tolist()),model_geometry_sha256={mapped[r['role']]:r['delivery_sha256']for r in model_bindings},overviewBearing=-98.74,overviewPitch=40,overviewZoom=21.3,maxDistance=450,lod_switch_in_m=202,lod_switch_out_m=285,partial_model=True,model_scope=manifest['model_scope_zh'],navigation=dict(listed=False,status='瑞金二路沿街人行空间与院内通道保留。双扇按2021年照片闭合。'),placement=dict(status='estimated',note='以五幅2015、2020和2021年街景交会定门心，按2021实景复原门槛两侧实物，原建筑3023与相邻屋、街道及回退层保留。'))
    checked_geometry(contract['collision_geometry'],ID,collision=True)
    write(arg.out/'final-placement-contract.json',contract)
    targets=[(n,*map(float,np.array([x,y])@site.axes),z)for n,x,y,z in MARKS]
    def cameras(neigh):
        deg=math.pi/180*6371008.8
        return [cam['evaluate'](contract,dict(width=w,height=h,insets=dict(zip(['left','right','top','bottom'],pads))),label,neigh,site.lon,site.lat,deg*math.cos(math.radians(site.lat)),deg,targets)for label,w,h,pads in cam['VIEWS']]
    fallback=[(i,geo.transform(g,lambda v:v@site.axes),h)for i,g,h in parts]
    best=-1
    candidates=[]
    for pitch in (40,36,34,29,24,48):
        for bearing in (-98.74,-90.,-105.,-83.,-113.):
            contract.update(overviewBearing=bearing,overviewPitch=pitch)
            pair=cameras(neighbors),cameras(fallback)
            score=sum(v['clear_count']for rows in pair for v in rows)
            candidates.append(dict(bearing=bearing,pitch=pitch,unblocked=score))
            if score>best:
                best=score;pick=(bearing,pitch,*pair)
            if score==2*len(cam['VIEWS'])*len(MARKS):break
        if best==2*len(cam['VIEWS'])*len(MARKS):break
    bearing,pitch,views,fallback_views=pick
    contract.update(overviewBearing=bearing,overviewPitch=pitch)
    write(arg.out/'final-placement-contract.json',contract)
    write(arg.out/'tested-camera-positions.json',dict(choices=candidates,selected=dict(bearing=bearing,pitch=pitch)))
    write(arg.out/'overview-sightlines.json',dict(views=views,fallback_views=fallback_views,source_sha=sha(site.files['feature-table.json.gz']),actual_camera_sha=sha(PROJECT/'src/candidate-overview-camera.js')))
    assert all(r['clear_count']==len(MARKS)for r in views+fallback_views),[(r['view'],r['clear_count'],[z for z in r['probes'] if not z['clear']])for r in views+fallback_views]
    native=original_meshes(site,ref,envelope,corridor,samples,views)
    fallback_best=tile['neighbor_parts'][0]
    write(arg.out/'placement-geometry.json',dict(passed=True,id=ID,manifest_sha256=sha(arg.manifest),contract_sha256=sha(arg.out/'final-placement-contract.json'),models=model_bindings,collision_components=len(geo.get_parts(collision)),collision_area_m2=collision.area,physical_collision_slice_heights_m=[.100,.111,.128],ground_samples=samples,clear_street_approach_xy_m=list(front.exterior.coords),clear_inner_approach_xy_m=list(courtyard.exterior.coords),clear_approach_width_m=3.68,closed_gate=True,passage_to_collision_clearance_m=collision.distance(corridor),original_city=native,neighbor_footprints=[dict(id=i,model_clearance_m=site.footprints[i].distance(envelope),walk_clearance_m=site.footprints[i].distance(corridor))for i in ref['closest_neighbors']],source_removed=0,fallback_review_sha256=sha(arg.out/'fallback-buildings.json'),fallback_nearest=fallback_best,source_ordinary_owner=None))
    print('original meshes',[(r['role'],r['original_triangles'],r['minimum_model_distance_m'])for r in native],'walking',len(samples),flush=True)
if __name__=='__main__':main()
