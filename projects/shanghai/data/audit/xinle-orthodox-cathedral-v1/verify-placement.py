"""Check the two cathedral source meshes and preserve the separate west building up to its own roof."""
import argparse
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, Point, shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

MODEL='xuhui-xinle-orthodox-cathedral'
OWNER=3953
WEST=640
grouped_sources=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--out',type=Path,default=AUDIT)
    args=cli.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    source=PROJECT/'source/precise'/MODEL
    layout=read(source/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,layout)
    assets,bounds,silhouette,ground=site.decode_model(args.manifest)
    group,=layout['near_tiles']
    ids=group['feature_local_ids']
    assert set(ids)=={4835,3316,3340,640,2159,5164,3953,1631}
    original,west=site.footprints[OWNER],site.footprints[WEST]
    envelope=original.buffer(.39,join_style='mitre')
    protected=west.buffer(.32,join_style='mitre')
    cut=envelope.difference(protected)
    upper=envelope.intersection(protected)
    roof=29.22
    assert .8<original.intersection(west).area<1.25
    assert silhouette.distance(west)>.36 and silhouette.difference(cut).area<.00002
    assert cut.disjoint(west)
    assert ground.is_valid and ground.geom_type=='Polygon'
    rows={r['local_id']:r for r in layout['owners']}
    heights=np.array([rows[i]['height']for i in ids])
    checks={}
    for lod,tris,assigned,ties in grouped_sources(site,group):
        if lod=='far':
            ours=assigned==OWNER
            neighbors=assigned==WEST
            ambiguous=0
        else:
            vertices=geo.points(tris[:,:,:2].reshape(-1,2))
            errors=np.column_stack([geo.distance(vertices,site.footprints[i]).reshape(-1,3).max(1)for i in ids])
            possible=(errors<.45)&(tris[:,:,2].max(1)[:,None]<=heights[None,:]+.10)
            assert possible.any(1).all() and errors.min(1).max()<.11
            ours=possible[:,ids.index(OWNER)]
            neighbors=possible[:,ids.index(WEST)]
            ambiguous=int((ours&neighbors).sum())
            assert ambiguous>0
        own=site.project_faces(tris[ours])
        neighbor=site.project_faces(tris[neighbors])
        others=site.project_faces(tris[~(ours|neighbors)])
        assert own.difference(envelope).area<.00001
        assert neighbor.intersection(cut).area<.00001 and others.disjoint(envelope)
        assert silhouette.distance(neighbor)>.22
        assert tris[neighbors,:,2].max()<roof-.08 and tris[ours,:,2].max()>30.70
        rest=own.intersection(upper)
        checks[lod]=dict(triangles_in_tile=len(tris),target_surface_triangles=int(ours.sum()),
                          west_surface_triangles=int(neighbors.sum()),ambiguous_wall_triangles=ambiguous,
                          west_roof_m=float(tris[neighbors,:,2].max()),old_church_roof_m=float(tris[ours,:,2].max()),
                          target_projection_m2=own.area,retained_party_edge_below_limit_m2=rest.area,
                          other_buildings_full_height_loss_m2=others.intersection(cut).area,
                          west_full_height_loss_m2=neighbor.intersection(cut).area,
                          model_gap_to_west_mesh_m=silhouette.distance(neighbor))
        if lod=='far':
            far=own
    vector=read(source/'vector-footprints.json')
    result=[]
    for component in vector['components']:
        polygon=geo.transform(shape(component['geometry']),site.to_xy)
        removed=polygon.intersection(cut).area
        if component['component']==337:
            assert removed>640 and polygon.difference(cut).area<10 and polygon.difference(envelope).area<.00001
        else:
            assert removed<.00001
        result.append(dict(id=component['id'],component=component['component'],total=component['total_components'],
                           area_m2=polygon.area,full_height_removed_m2=removed,retained_m2=polygon.difference(cut).area))
    border=geo.line_merge(protected.boundary.intersection(far)).simplify(.0002)
    lines=[line for line in geo.get_parts(border)if line.geom_type=='LineString' and line.length>0.01]
    assert lines and sum(line.length for line in lines)>12
    caps=MultiLineString(lines)
    ready=read(site.files['READY.json'])
    name=dict(macro_id=layout['frozen_macro'],feature_local_id=OWNER)
    ref=[ready['origin_longitude'],ready['origin_latitude']]
    contract=dict(id=MODEL,owner=name,source_feature_ids=dict(building=[layout['owner']['source_key'].split(':')[1]],building_part=[]),
                  lng=site.lon,lat=site.lat,heading=layout['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
                  bounds_glb=bounds,model_geometry_sha256={k:r['sha256']for k,r in assets.items()},
                  replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(ground),
                  display_height_clips=[dict(id=MODEL+'-west-wall-roof',owner=name,geometry=site.wgs(upper),
                                             min_height=roof,max_height=31.35,height_reference=ref)],
                  source_section_caps=dict(geometry=site.wgs(caps),base_m=0,roof_m=roof,height_reference=ref,
                                           far_sha256=sha(site.files['far.glb'])),
                  overviewBearing=-169,overviewPitch=46,overviewZoom=19.35,maxDistance=630,lod_switch_in_m=640,lod_switch_out_m=820,
                  navigation=dict(listed=False,status='街面可见新乐路入口、襄阳北路窗墙及五座穹顶。'),
                  placement=dict(status='estimated',note='按55号门牌、两街照片、具名底图及三期航片配准到主堂地块。'),
                  partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for key in ('replacement_geometry','collision_geometry'):
        checked_geometry(contract[key],key,collision=key=='collision_geometry')
    probes=[]
    def probe(label,x,y,solid,owner=OWNER):
        pt=Point(x,y)
        is_obstacle=ground.covers(pt)
        under_cut=cut.covers(pt)
        baseline=site.footprints[owner].covers(pt)
        assert (is_obstacle or baseline and not under_cut)==solid,(label,is_obstacle,under_cut,baseline)
        probes.append(dict(name=label,xy=[x,y],expected='building'if solid else None,
                           modelObstacle=is_obstacle,cut=under_cut,ownerLocalId=owner))
    for label,x,y,solid in [('closed central sanctuary',0,0,True),('north entrance threshold',0,12.49,True),
                           ('outer entrance step',0,13.24,True),('Xinle Road sidewalk',0,14.18,False),
                           ('east gable wall',11.65,-.3,True),('east pavement',12.55,0,False),
                           ('space beside the east gable',11.88,0,False),('outside north flank',7.8,12.4,False),
                           ('west gable wall',-11.5,4,True),('south sanctuary',0,-11.95,True),
                           ('south side yard',0,-13.18,False),('open north corner',10.98,12.23,False)]:
        probe(label,x,y,solid)
    sliver=far.intersection(upper).difference(west.buffer(.085)).difference(ground)
    assert sliver.area>.3
    point=sliver.representative_point()
    probe('retained lower shared wall',point.x,point.y,True)
    probe('separate west building',-19,5,True,WEST)
    others=sorted(set(ids)-{OWNER})
    added=sum(len(poly.exterior.coords)-3 for poly in [cut,upper])
    case=dict(id=MODEL,previous='huangpu-cixiu-nunnery-courtyard',neighbors=others,groupTriangles=added,addedTriangles=added,
              sourceSectionCount=len(lines),front=dict(center=[1,7.3],elevation=11,pitch=54,zoom=19.94,bearingOffset=-147.0),
              roof=dict(center=[1,0],elevation=22,pitch=31,zoom=19.18,bearingOffset=-139),ground=probes,
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in others})
    write(args.out/'map-case.json',case)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=MODEL,script_sha256=sha(Path(__file__)),
        manifest_sha256=sha(args.manifest),source_sha256=sha(source/'footprint-review.json'),
        contract_sha256=sha(args.out/'final-placement-contract.json'),assets=assets,group=group,variants=checks,
        ground_m2=ground.area,silhouette_m2=silhouette.area,source_overlap_m2=west.intersection(original).area,
        retained_west_wall_height_m=roof,section_length_m=caps.length,vector_tile_sha256=vector['sha256'],
        vector_components=result,ground_samples=probes))
    print('Verified',MODEL,added,'clip triangles',len(lines),'sections',len(probes),'pedestrian samples',checks,flush=True)


if __name__=='__main__':
    main()
