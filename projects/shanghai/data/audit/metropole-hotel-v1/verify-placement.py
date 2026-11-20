"""Measure the shared party line at the Metropole and preserve the adjoining low block."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-metropole-hotel'
HOTEL=358
PARTY=724
KINCHENG=1708
TWINS=1844
NEIGHBORS=[PARTY,KINCHENG,1120,TWINS,1554]


def grouped_sources(site,group):
    ids=group['feature_local_ids']
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':i}for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    for variant in ['near','far']:
        tr=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
        tr[:,:,:2]=tr[:,:,:2]@site.axes.T
        if variant=='far':
            assignments=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            ties=np.zeros(len(tr),dtype=bool)
        else:
            centers=geo.points(tr[:,:,:2].mean(axis=1))
            distances=np.column_stack([geo.distance(centers,site.footprints[i])for i in ids]);sorted_dist=np.sort(distances,axis=1)
            assignments=np.array(ids)[distances.argmin(axis=1)]
            ties=sorted_dist[:,1]-sorted_dist[:,0]<.35
            assert sorted_dist[:,0].max()<.36
        yield variant,tr,assignments,ties


def number_triangles(polygon):
    return sum(len(part.exterior.coords)-3 for part in geo.get_parts(polygon))


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    source=read(PROJECT/'source/precise'/ID/'footprint-review.json');mf=read(args.manifest)
    site=PlacementMeshes(PROJECT,args.work,source);assets,bounds,model,_=site.decode_model(args.manifest)
    source_rows={i['local_id']:i for i in source['owners']}
    group=next(g for g in source['near_tiles']if HOTEL in g['feature_local_ids'])
    assert PARTY in group['feature_local_ids'] and KINCHENG in group['feature_local_ids']
    old=site.footprints[HOTEL];low_block=site.footprints[PARTY];envelope=old.buffer(.42,join_style='mitre')
    # The old source polygons cross by almost two square metres. Narrow overlap
    # cannot be attributed by nearest 2D triangle centre in the untagged near
    # group. The full-height cut therefore stays clear of the entire low block.
    protected=low_block.buffer(.53,join_style='mitre')
    cut=envelope.difference(protected);shared=envelope.intersection(protected)
    assert cut.is_valid and shared.is_valid and cut.geom_type==shared.geom_type=='Polygon'
    assert model.disjoint(low_block) and cut.distance(low_block)>.50 and old.intersection(low_block).area>1.8
    result={};far_foot=None;z_limit=25.74
    for variant,tr,assigned,ties in grouped_sources(site,group):
        high=tr[:,:,2].max(1);centers=geo.points(tr[:,:,:2].mean(1));close=assigned==PARTY
        if variant=='near':
            # Interior roof triangles measure the actual height of 724. Where
            # overlapping outlines make ownership ambiguous, test against all
            # geometry in this protected zone at the adjoining roof's height.
            inner=geo.contains(low_block.buffer(-.45),centers)
            assert inner.sum()>=2
            neighbor_top=float(tr[inner,:,2].max());assert abs(neighbor_top-25.6)<.012
            # Long triangles can cross most of the main hotel's party side
            # while their centroid lies inside the low building. Compare every
            # vertex to every group footprint and test the independently known
            # roof limit. Keep all possible owners in the remaining 134 ties.
            ids=group['feature_local_ids'];verts=geo.points(tr[:,:,:2].reshape(-1,2))
            max_distance=np.column_stack([geo.distance(verts,site.footprints[i]).reshape(-1,3).max(1)for i in ids])
            heights=np.array([source_rows[i]['source_height_m']for i in ids])
            possible=(max_distance<=.395)&(high[:,None]<=heights[None,:]+.04)
            assert possible.any(1).all() and max_distance.min(1).max()<.13
            plausible_hotel=possible[:,ids.index(HOTEL)]
            plausible_neighbor=possible[:,ids.index(PARTY)]
            ambiguous=possible.sum(1)>1
            assert (possible[ambiguous][:,[ids.index(HOTEL),ids.index(PARTY)]].all(1)).all()
            assert tr[plausible_neighbor,:,2].max()<=neighbor_top+.04
            other_low=site.project_faces(tr[plausible_neighbor]);neg=other_low.intersection(cut).area
            assert neg<.00001,('near protected overlap',neg)
            independent=~plausible_hotel & ~plausible_neighbor
            other=site.project_faces(tr[independent]);assert other.disjoint(cut) and other.disjoint(shared)
            source_body=site.project_faces(tr[plausible_hotel&~ambiguous]);observed_gap=model.distance(other_low)
            assert observed_gap>.13,(variant,observed_gap)
            result[variant]=dict(group_triangles=len(tr),original_hotel_height_m=float(tr[plausible_hotel,:,2].max()),
                protected_roof_height_m=neighbor_top,protected_low_triangles=int(plausible_neighbor.sum()),
                ambiguous_party_triangles_conservatively_protected=int(ambiguous.sum()),
                largest_best_match_vertex_distance_m=float(max_distance.min(1).max()),
                protected_geometry_overlap_with_full_height_cut_m2=neg,model_to_protected_low_geometry_m=observed_gap,
                independent_unsuppressed_triangles=int(independent.sum()),independent_gap_m=model.distance(other),
                unambiguous_hotel_projection_m2=source_body.area)
        else:
            source_body=site.project_faces(tr[assigned==HOTEL]);other=site.project_faces(tr[assigned==PARTY]);far_foot=source_body
            neighbor_top=float(tr[assigned==PARTY,:,2].max());assert abs(neighbor_top-25.6)<.012
            assert envelope.covers(source_body)and cut.disjoint(other) and z_limit>neighbor_top+.12
            assert model.distance(other)>.13
            result[variant]=dict(group_triangles=len(tr),hotel_triangles=int((assigned==HOTEL).sum()),adjoining_triangles=int((assigned==PARTY).sum()),
                original_hotel_height_m=float(tr[assigned==HOTEL,:,2].max()),protected_roof_height_m=neighbor_top,
                hotel_projection_m2=source_body.area,retained_party_wall_m2=source_body.intersection(shared).area,
                removed_full_height_m2=source_body.intersection(cut).area,cut_to_neighbor_m=cut.distance(other),model_to_neighbor_m=model.distance(other),
                owner_assignment='Per-vertex _FEATURE_ID_0, verified across each triangle.')
    assert far_foot is not None
    # Cover the near/far boundary once. The protected party strip is short;
    # upper heights on 358 beyond the actual roof of 724 have separate binding.
    lines=geo.line_merge(protected.boundary.intersection(far_foot)).simplify(.0002)
    caps=MultiLineString([lines])if lines.geom_type=='LineString' else MultiLineString(list(lines.geoms))
    assert len(caps.geoms)>=1 and len(caps.geoms)<=2 and caps.length>13
    target=source_rows[HOTEL];own=dict(macro_id=source['frozen_macro'],feature_local_id=HOTEL)
    city=read(site.files['READY.json']);href=[city['origin_longitude'],city['origin_latitude']]
    # The mass is closed behind the shopfronts. Three entrance openings lead
    # through the physical front plane to separate recessed doors.
    footprint=projected_base(site.work,site)
    y=-.58772
    niches=[geo.box(x-.77,y-.22,x+.77,y+1.485)for x in [-2.04,0,2.04]]
    collision=footprint.difference(geo.union_all(niches)).simplify(.013)
    assert collision.is_valid and collision.geom_type=='Polygon'
    height_clip=dict(id=ID+'-party-wall-upper-trim',owner=own,geometry=site.wgs(shared),min_height=z_limit,max_height=45.2,height_reference=href)
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[target['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),display_height_clips=[height_clip],
        source_section_caps=dict(geometry=site.wgs(caps),base_m=0,roof_m=z_limit,height_reference=href,far_sha256=sha(site.files['far.glb'])),
        lng=site.lon,lat=site.lat,heading=source['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:r['sha256']for k,r in assets.items()},overviewBearing=28,overviewPitch=33,overviewZoom=18.47,
        maxDistance=725,lod_switch_in_m=650,lod_switch_out_m=800,navigation=dict(listed=False,status='都城饭店东北转角主楼。'),
        placement=dict(status='estimated',note='江西中路与福州路东北角358。724的25.60米低楼及共同界面保留，1708金城银行与1844福州大楼独立。'),
        partial_model=True,model_scope=mf['scope'])
    for k in ['replacement','collision']:checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    write(args.out/'final-placement-contract.json',contract)
    tests=[('ground before recessed central doors',[0,.32],False),('closed central entrance door',[0,1.08],True),
           ('ground at west entrance',[-2.04,.32],False),('ground at east entrance',[2.04,.32],False),
           ('right granite pier',[3.14,-.36],True),('occupied corner tower',[0,5],True),('circular road junction',[0,-5.15],False)]
    residual=far_foot.intersection(shared).difference(collision).difference(low_block.buffer(.08));pt=residual.representative_point()
    assert residual.area>.1
    ground=[]
    for name,xy,solid in tests:
        pt2=geo.Point(xy);assert collision.covers(pt2)==solid,(name,collision.distance(pt2))
        ground.append(dict(name=name,xy=xy,expected='building'if solid else None,modelObstacle=solid,cut=cut.covers(pt2)))
    ground.append(dict(name='retained shared lower party wall',xy=[pt.x,pt.y],expected='building',modelObstacle=False,cut=False))
    added=number_triangles(cut)+number_triangles(shared)
    case=dict(id=ID,previous='huangpu-oriental-hotel',existingGroupOwners=[KINCHENG],existingCandidateOwners=[KINCHENG,1554],
        adjacentModel='huangpu-kincheng-bank',neighbors=NEIGHBORS,addedTriangles=added,groupTriangles=2+added,sourceSectionCount=len(caps.geoms),
        front=dict(center=[0,0],elevation=21,pitch=53,zoom=18.93,bearingOffset=0),roof=dict(center=[0,5.4],elevation=27,pitch=31,zoom=18.67,bearingOffset=-15),
        ground=ground,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in NEIGHBORS})
    write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),source_review_sha256=sha(PROJECT/'source/precise'/ID/'footprint-review.json'),
        model_assets=assets,group=group,party_source_polygon_overlap_m2=old.intersection(low_block).area,protected_neighbor_buffer_m=.53,
        numeric_masks=dict(full_height_area_m2=cut.area,restricted_height_band_m2=shared.area,upper_trim_above_m=z_limit),
        decoded=result,section_count=len(caps.geoms),section_total_length_m=caps.length,ground_m2=collision.area,ground_witnesses=ground,
        unfitted_model_projection_m2=model.area,checker=sha(Path(__file__))))


def projected_base(work,site):
    from shapely.geometry import Polygon
    # Trace the full ground-level wall loop from the conditioned 0–0.5 m
    # triangles, excluding the shallow outdoor flashings and stairs.
    d=read(work/'delivered-decode.json')[0];tri=np.fromfile(d['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
    masks=np.fromfile(d['triangle_material_ids_file'],np.uint16);keep=np.isin(masks,[d['material_names'].index(i)for i in ['pale cast stone','upper render','polished granite']]);outer=site.ground_faces(tri[keep])
    # The open threshold is represented above. Exterior ring corner controls
    # below must lie in the decoded physical wall (centimetre-level tolerance).
    from math import sin,cos,radians
    a=[(13.93*sin(radians(v)),13.93*(cos(radians(v))-1))for v in [-52.4,-39.4,-16.7,16.7,39.4,52.4]]
    poly=Polygon([(-20.76,4.03),*a,(17.52,1.02),(-2.96,21.09)])
    assert all(outer.distance(geo.Point(v))<.26 for v in poly.exterior.coords)
    return poly


if __name__=='__main__':main()
