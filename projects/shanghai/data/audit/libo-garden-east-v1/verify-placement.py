"""Check the west/central red-roofed section of 343 and retain its eastern flat roof."""
import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import LineString, MultiLineString, Point, box, mapping, shape

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, sha, write

model='xuhui-libo-garden-east-house'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro',required=True,type=Path)
parser.add_argument('--vector',required=True,type=Path)
parser.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out',type=Path,default=audit)
args=parser.parse_args()
review_path=project/'source/precise'/model/'footprint-review.json'
review,manifest,vector=read(review_path),read(args.manifest),read(args.vector)
group,=review['near_tiles']
assert manifest['id']==model and len(group['feature_local_ids'])==8
assert vector['sha256']=='ef9df460f908f294d516f8753ac4366603662b592d4fb5bd2c214df51e6cf5e0'
with tempfile.TemporaryDirectory()as directory:
    tmp=Path(directory)
    for row in review['frozen_bindings']:
        suffix=row['repository_path'].split(review['frozen_macro']+'/')[1]
        (tmp/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    site=PlacementMeshes(project,tmp,review)
    assets,bounds,profile,ground=site.decode_model(args.manifest)
    actual=site.decode_group(group,343)
    # Three roof imagery editions and the February/March 2023 opening
    # photographs preserve a separate dark flat-roofed east extension.
    mask=box(-14.03,-13.46,12.34,10.87)
    assert mask.covers(profile)
    collision=ground.buffer(.028,join_style='mitre').simplify(.055,preserve_topology=True)
    assert ground.difference(collision).area<.060
    neighbors={k:{'intersection_m2':g.intersection(mask).area,'distance_m':g.distance(mask)}for k,g in site.footprints.items()if k!=343}
    assert all(v['intersection_m2']==0 and v['distance_m']>.30 for v in neighbors.values())
    road=LineString(site.to_xy(np.asarray(review['street']['coords'])))
    assert road.distance(mask)>5 and road.distance(collision)>5
    original=site.footprints[343]
    source_geometry={}
    seams={}
    for role,(tris,peers,assignment) in actual.items():
        raw=site.project_faces(tris);others=site.project_faces(peers)
        east=raw.difference(mask);cut=raw.intersection(mask)
        seam=geo.line_merge(raw.intersection(mask.boundary));assert seam.geom_type=='LineString' and 14<seam.length<20
        assert 180<east.area<265 and cut.area>410 and others.distance(mask)>.45,(role,east.area,cut.area)
        assert east.intersection(box(13.,-5.5,24.5,9.8)).area>173
        seams[role]=seam
        source_geometry[role]={'source_area_m2':raw.area,'garden_wing_removed_m2':cut.area,
                               'eastern_flat_roof_retained_m2':east.area,'section_xy':mapping(seam),
                               'other_owners_distance_m':others.distance(mask),'old_height_m':float(tris[:,:,2].max()),
                               'assignment':assignment}
    assert seams['near'].hausdorff_distance(seams['far'])<.11
    # The cap endpoints are clipped back slightly along the *straight* east
    # boundary common to both real mesh LODs. Reproject to a WGS84 line on
    # the submitted edge to avoid float drift from independently reprojecting.
    miny=max(v.bounds[1]for v in seams.values())+.012
    maxy=min(v.bounds[3]for v in seams.values())-.012
    cap=LineString([(12.34,miny),(12.34,maxy)])
    rw=site.wgs(mask);edge=LineString(np.asarray(site.to_wgs(np.array([[12.34,-13.46],[12.34,10.87]]))))
    points=[]
    for pos in site.to_wgs(np.array(cap.coords)):
        points.append(edge.interpolate(edge.project(Point(pos))).coords[0])
    sec=mapping(MultiLineString([points]))
    assert shape(rw).boundary.buffer(1e-9).covers(shape(sec))
    vectors=[]
    for f in vector['nearby_features']:
        raw_feature=geo.transform(shape(f['geometry']),site.to_xy)
        components=list(raw_feature.geoms)if hasattr(raw_feature,'geoms')else[raw_feature]
        # Native tile parts share boundaries and occasionally overlap. Its
        # polygon set represents their union, as in the production clipper.
        feature=geo.union_all([geo.make_valid(v)for v in components]);cut=feature.intersection(mask)
        if cut.area>.001:
            vectors.append({'id':f['id'],'area_cut_m2':cut.area,'total_area_m2':feature.area,
                            'retained_m2':feature.difference(mask).area,'properties':f['properties'],
                            'affected_components':sum(g.intersection(mask).area>.001 for g in components)})
    assert len(vectors)==1 and vectors[0]['id']==147898520 and vectors[0]['affected_components']==1
    probes=[]
    for name,x,y,collide,native in [
        ('garden central room',0,0,True,False),('five-openings terrace',.4,-9.9,True,False),
        ('south-east projecting wing',8,-8.85,True,False),('western circular return',-11.88,.24,True,False),
        ('northern room',1.52,7.92,True,False),('open lawn',.4,-15.40,False,False),
        ('between east house and street-side office',-16.,-1.8,False,False),('street-side office 652',-23,-13,False,False),
        ('retained dark eastern roof',18.02,2.14,False,True)]:
        g=Point(x,y);assert bool(collision.covers(g))==collide,(name,collision.covers(g))
        retained=original.covers(g)and not mask.covers(g);assert retained==native,(name,retained)
        probes.append(dict(label=name,xy=[x,y],point=site.to_wgs(np.array([[x,y]]))[0].tolist(),
                           model_collision=collide,under_mask=mask.covers(g),retained_owner343_ground=native))
    o=review['owner'];ready=read(args.macro/'READY.json')
    contract={'id':model,**review['author_frame']['anchor'],'heading':review['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':343},
              'source_feature_ids':{'building':[o['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':rw,'collision_geometry':site.wgs(collision),
              'source_section_caps':{'geometry':sec,'base_m':0,'roof_m':source_geometry['far']['old_height_m'],
                  'far_sha256':sha(args.macro/'far.glb'),'height_reference':[ready['origin_longitude'],ready['origin_latitude']]},
              'overviewBearing':0,'overviewPitch':56,'overviewZoom':20.0,'maxDistance':680,
              'lod_switch_in_m':620,'lod_switch_out_m':820,'partial_model':True,'model_scope':manifest['model_scope_zh'],
              'placement':{'status':'estimated','note':'按2023年花园开放航片、三版影像和现场照片定位343的红瓦、半圆返回和南平台；保留343东端黑色平顶、吴兴路沿街办公楼652与衡山路300弄两排。'},
              'navigation':{'listed':False,'status':'从园中浏览半露木山墙、五个落地开间、西侧半圆窗与红瓦。'}}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(contract[k],k,collision=k=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=model,assets=assets,source_sha256=sha(review_path),
          script_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),contract_sha256=sha(args.out/'final-placement-contract.json'),
          mask_area_m2=mask.area,collision_area_m2=collision.area,ground_profile_m2=ground.area,full_projection_m2=profile.area,
          source_records=source_geometry,group=group,retained_section_length_m=cap.length,near_far_cap_diff_m=seams['far'].hausdorff_distance(seams['near']),
          adjacent_sources={k:neighbors[int(k)]for k in review['neighboring_buildings']},
          road_distance_m=road.distance(mask),fallback_tile_count=vector['total_tile_buildings'],fallback_affected=vectors,ground_points=probes))
    print(source_geometry,vectors,'road',road.distance(mask),flush=True)
