"""Check the narrow courtyard subtraction while keeping the row behind it.

The two survey extents slightly differ. The sections of wall exposed in the
native city are derived from the signed far building and restricted to the
verified WGS84 edge. The lane remains open outside the entrance.
"""
import argparse
from pathlib import Path
import sys,tempfile
import numpy as np
import shapely as geo
from shapely.geometry import LineString,MultiLineString,Point,box,shape,mapping

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry,check_source_section_caps

model='jingan-villa-no25'
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--macro',type=Path,required=True)
cli.add_argument('--vector',type=Path,required=True)
cli.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/model/'manifest.json')
cli.add_argument('--out',type=Path,default=audit)
args=cli.parse_args()
src=project/'source/precise'/model/'footprint-review.json';review=read(src);owner=review['owner'];group,=review['near_tiles'];ready=read(args.macro/'READY.json');vec=read(args.vector);manifest=read(args.manifest)
assert owner['feature_local_id']==1954 and len(group['feature_local_ids'])==6
assert vec['sha256']==review['osm_fallback_tiles'][0]['sha256'] and vec['features'][0]['id']==64634100
with tempfile.TemporaryDirectory()as tmp:
    work=Path(tmp)
    for r in review['frozen_bindings']:
        suffix=r['repository_path'].split(owner['macro_id']+'/')[1]
        (work/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh=PlacementMeshes(project,work,review)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    decoded=mesh.decode_group(group,1954)
    mask=box(-2.56,-.26,2.08,4.82)
    registered=mesh.wgs(mask);exact_wgs=shape(registered)
    assert mask.covers(profile) and profile.area<3.1
    native=mesh.footprints[1954]
    polygons=list(geo.transform(shape(vec['features'][0]['geometry']),mesh.to_xy).geoms)
    assert len(polygons)==1813
    component,=[(i,part)for i,part in enumerate(polygons)if part.intersection(native).area>400]
    index,osm=component
    assert 20.7<osm.intersection(mask).area<22 and osm.difference(mask).area>419
    assert all(part.intersection(mask).area<.0001 for i,part in enumerate(polygons)if i!=index)
    others={i:mesh.footprints[i].distance(mask)for i in group['feature_local_ids']if i!=1954}
    assert min(others.values())>6
    assert not any(mask.covers(Point(mesh.to_xy(np.array([r['wgs84']]))[0]))for r in review['house25_source_points'])
    collision=ground.buffer(.025,join_style='mitre').simplify(.012,preserve_topology=True)
    assert ground.difference(collision).area<.0003
    variants={};surfaces={};seams={}
    for variant,(tris,rest,assignment)in decoded.items():
        original=mesh.project_faces(tris);peers=mesh.project_faces(rest)
        cut=original.intersection(mask)
        assert 18<cut.area<27 and original.difference(mask).area>400
        assert peers.distance(mask)>5
        seam=geo.line_merge(mask.boundary.intersection(original))
        pieces=[seam] if seam.geom_type=='LineString' else [g for g in seam.geoms if g.geom_type=='LineString' and g.length>.02]
        assert pieces and sum(g.length for g in pieces)>8
        surfaces[variant]=original;seams[variant]=pieces
        variants[variant]={'old_m2':original.area,'removed_forecourt_m2':cut.area,'remaining_m2':original.difference(mask).area,'height_m':float(tris[:,:,2].max()),'neighboring_geometry_gap_m':peers.distance(mask),'decoded_tris':len(tris),'assignment':assignment}
    # Use the exact registered polygon boundary in WGS84. Resampling or
    # rounding the sharp corner could otherwise move the cap off the cut.
    raw=geo.transform(surfaces['far'],mesh.to_wgs)
    geo_seam=geo.line_merge(exact_wgs.boundary.intersection(raw))
    parts=[geo_seam] if geo_seam.geom_type=='LineString' else [g for g in geo_seam.geoms if g.geom_type=='LineString'and g.length>1e-8]
    caps=MultiLineString([list(g.coords)for g in parts])
    ground_tests=[]
    for label,x,y,blocked in [('closed black gate',-.64,.02,True),('southwest brick pillar',-1.59,.15,True),('northeast brick pillar',.30,.15,True),('wing plinth',1.61,.12,True),('lane in front of plate',-1.59,-.65,False),('interior of open court',0,2.85,False),('street at neighboring door',5.7,-.55,False)]:
        point=Point(x,y)
        assert collision.covers(point)==blocked,(label,collision.distance(point))
        ground_tests.append({'label':label,'xy':[x,y],'wgs84':mesh.to_wgs(np.array([[x,y]]))[0].tolist(),'model_collision':blocked,'under_mask':mask.covers(point)})
    contract={'id':model,**review['author_frame']['anchor'],'heading':review['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':1954},'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,'replacement_geometry':registered,'collision_geometry':mesh.wgs(collision),'source_section_caps':{'geometry':mapping(caps),'base_m':0,'roof_m':variants['far']['height_m'],'far_sha256':sha(args.macro/'far.glb'),'height_reference':[ready['origin_longitude'],ready['origin_latitude']]},'overviewBearing':-5.38,'overviewPitch':55,'overviewZoom':21.93,'lod_switch_in_m':500,'lod_switch_out_m':700,'maxDistance':390,'placement':{'status':'estimated','note':'依据25号门口原照、25至33号连续地址与航片上的前院带，登记弄面院墙。户界与构件尺寸按比例估算。'},'navigation':{'listed':False,'status':'从支弄向25号黑色双扇院门和绿色门牌看去。'},'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for name in ['replacement_geometry','collision_geometry']:checked_geometry(contract[name],name,collision=name=='collision_geometry')
    check_source_section_caps(contract,exact_wgs)
    args.out.mkdir(parents=True,exist_ok=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':model,'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),'reference_sha256':sha(src),'contract_sha256':sha(args.out/'final-placement-contract.json'),'assets':assets,'group':group,'other_group_owners':others,'native_variants':variants,'display_profile_m2':profile.area,'footprint_at_ground_m2':ground.area,'collision_m2':collision.area,'mask_m2':mask.area,'ground_points':ground_tests,'section_cap_length_m':sum(x.length for x in seams['far']),'osm':{'tile_sha256':vec['sha256'],'feature':64634100,'components':len(polygons),'target_component':index,'row_area_m2':osm.area,'removed_court_m2':osm.intersection(mask).area,'retained_m2':osm.difference(mask).area,'untouched_other_components':len(polygons)-1},'roof_clearance_m':5.5-(4.82+.06),'nearest_estimated_party_boundary_margin_m':4.99-(2.08+2.26)})
    print('registered courtyard',index,variants)
