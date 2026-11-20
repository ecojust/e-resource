"""Bind the Gaolan Road church meshes and retain the unverified northern service area and its source roof."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

import shapely as sg
from shapely.geometry import box, LineString, MultiLineString, Point

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
ID = 'huangpu-gaolan-st-nicholas-church'
OWNER = 2197
sys.path.insert(0, str(PROJECT / 'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry


def verify(args, scratch):
    source = read(PROJECT/'source/precise'/ID/'footprint-review.json')
    camera = read(PROJECT/'source/precise'/ID/'camera-preflight.json')
    for row in source['frozen_bindings']:
        name = row['repository_path'].split(source['frozen_macro']+'/')[1]
        f = args.macro/name
        assert sha(f) == row['sha256'] and f.stat().st_size == row['bytes']
        (scratch/f.name).symlink_to(f.resolve())
    mesh = PlacementMeshes(PROJECT, scratch, source)
    assets,bounds,visual,collision = mesh.decode_model(args.manifest)
    # The designer's identifiable north church wall is at y=5.86. The registered rectangle
    # continues behind it into unsurveyed rooms shown differently in the renovation plan.
    stop = 6.15
    cut = box(-6.94,-8.45,6.98,stop)
    assert visual.difference(cut).area < .001 and collision.difference(cut).area < .001
    assert collision.is_valid and collision.geom_type in ('Polygon','MultiPolygon'), collision.geom_type
    if collision.geom_type=='MultiPolygon':
        components=sorted([g.area for g in collision.geoms],reverse=True)
        assert components[0]>.975*collision.area and len(components)<=24, components
    assert 90 < collision.area < 168 and collision.area <= visual.area + .2
    original = mesh.decode_group(source['near_tiles'][0], OWNER)
    evidence, footprints = {}, {}
    for role,(own,other,method) in original.items():
        old = mesh.project_faces(own)
        neighbor = mesh.project_faces(other)
        residual = old.difference(cut)
        assert .095 < residual.area/old.area < .12 and neighbor.distance(cut)>2.0
        assert abs(float(own[:,:,2].max())-18) < .06
        assert neighbor.intersection(collision).area < .001
        footprints[role]=old
        evidence[role]={'owner_triangles':len(own),'other_triangles':len(other),
            'owner_height_m':float(own[:,:,2].max()),'footprint_m2':old.area,
            'retained_m2':residual.area,'retained_fraction':residual.area/old.area,
            'neighbor_distance_m':neighbor.distance(cut),'neighbor_clip_overlap_m2':neighbor.intersection(cut).area,
            'owner_assignment':method}
    related = {i:{'clip_clearance_m':g.distance(cut),'collision_clearance_m':g.distance(collision)}
            for i,g in mesh.footprints.items()if i!=OWNER and g.distance(cut)<28}
    assert all(row['clip_clearance_m']>2 for row in related.values()) and 4245 in related and 2038 in related
    intercept = LineString([(-9,stop),(9,stop)])
    far = footprints['far'].intersection(intercept);near = footprints['near'].intersection(intercept)
    assert far.geom_type == 'LineString' and near.geom_type in ('LineString','MultiLineString')
    assert 12.6<far.length<13.3 and near.hausdorff_distance(far)<.16
    edge = MultiLineString([far]);ready=read(args.macro/'READY.json')
    cap={'base_m':0,'roof_m':18,'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
         'far_sha256':ready['far']['sha256'],'geometry':mesh.wgs(edge)}
    checks=[]
    def check(name,x,y,source_obstacle,walks,cut_here):
        pos=Point(x,y)
        assert cut.covers(pos)==cut_here and collision.covers(pos)==walks, (name,x,y)
        checks.append({'name':name,'local_xy':[x,y],'expected':source_obstacle,'modelObstacle':walks,
                       'cut':cut_here,'wgs84':mesh.wgs(pos)['coordinates']})
    check('closed Gaolan Road entrance',1.24,-7.39,'building',True,True)
    check('western pair of street arches',-2.70,-7.16,'building',True,True)
    check('crossing below the gold dome',-.75,-.97,'building',True,True)
    check('east apse centre',5.25,-.80,'building',True,True)
    check('west vestibule',-5.0,-1.22,'building',True,True)
    check('front public pavement',0,-9.85,None,False,False)
    check('courtyard east of the front opening',5.84,-7.24,None,False,True)
    check('western corner court',-4.8,-6.2,None,False,True)
    check('rear service area in original block',.05,7.05,'building',False,False)
    check('registered eastern neighbor beyond the gap',9.02,0,None,False,False)
    frame=source['author_frame'];man=read(args.manifest);_,bearing,pitch=camera['recommendation']
    contract={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,
              'owner':{'macro_id':source['frozen_macro'],'feature_local_id':OWNER},
              'source_feature_ids':{'building':[source['owner']['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':mesh.wgs(cut),'collision_geometry':mesh.wgs(collision),'source_section_caps':cap,
              'overviewBearing':bearing,'overviewPitch':pitch,'overviewZoom':19.5,'maxDistance':500,
              'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'现状主堂外观，仅供俯瞰。'},
              'placement':{'status':'estimated','note':'据现状三期外景、改造平面与具名源2197配准。原底图北缘约1.8米延入后勤房范围，保留其18米粗略源高。初建九顶为历史记录。'},
              'partial_model':True,'model_scope':man['model_scope_zh']}
    for key in ('replacement_geometry','collision_geometry'):
        checked_geometry(json.loads(json.dumps(contract[key])),key,collision=key=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',{'id':ID,'asset_sha256':assets,'frozen_bindings':source['frozen_bindings'],
          'source_variants':evidence,'ground_collision_m2':collision.area,'model_projection_m2':visual.area,
          'remaining_north_strip_m':{k:round(x.bounds[3]-stop,4)for k,x in footprints.items()},
          'section_witness':{'near_m':near.length,'far_m':far.length,'maximum_alignment_error_m':near.hausdorff_distance(far)},
          'neighbors':related,'ground_checks':checks,'contract_sha256':sha(args.out/'final-placement-contract.json'),
          'note':'Rear original 18 m height is a property-block estimate and is not an estimate of the historical service-room height.'})
    print(evidence,len(checks),collision.area,flush=True)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--macro',type=Path,required=True)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    cli.add_argument('--out',type=Path,default=AUDIT)
    opts=cli.parse_args()
    with tempfile.TemporaryDirectory()as scratch:verify(opts,Path(scratch))
