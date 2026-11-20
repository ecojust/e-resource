"""Measure the retained historic block, its two street neighbors and the walkable colonnade."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys
import numpy as np
import shapely as geo

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID = 'huangpu-bankers-association-building'
OWNER = 2170
COLS = [-7.35,-4.41,-1.47,1.47,4.41,7.35]


def separate_group_distances(site,groups,mask):
    rows=[]
    for group in groups:
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        write(site.work/'context-features.json',[dict(localId=i)for i in group['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ['near','far']:
            triangles=np.fromfile(site.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
            triangles[:,:,:2]=triangles[:,:,:2]@site.axes.T
            geometry=site.project_faces(triangles)
            assert mask.disjoint(geometry)
            rows.append(dict(group=group['id'],owners=group['feature_local_ids'],variant=variant,
                             triangles=len(triangles),nearest_geometry_m=mask.distance(geometry)))
    return rows


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',required=True,help='The actual preceding published model in the frozen control city')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    evidence=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,evidence)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    mask=geo.box(-11.10,-.76,11.10,4.23)
    assert model.difference(mask.buffer(.002)).area<.0001
    # The three floor steps remain walkable between the column plinths and up to the recessed door.
    rear=geo.box(-10.77,2.67,10.77,4.215).difference(geo.box(-1.015,2.66,1.015,3.375))
    blockers=[rear,geo.box(-10.77,0,-7.77,4.215),geo.box(7.77,0,10.77,4.215)]
    blockers.extend(geo.box(x-.595,.045,x+.595,1.235)for x in COLS)
    collision=geo.union_all(blockers,grid_size=.001)
    assert collision.is_valid and collision.difference(mask).is_empty
    group=next(g for g in evidence['near_tiles']if OWNER in g['feature_local_ids'])
    result={};seams={}
    for variant,(target,other,assign)in site.decode_group(group,OWNER).items():
        own=site.project_faces(target);other_projection=site.project_faces(other)
        assert mask.disjoint(other_projection)and model.disjoint(other_projection)
        keep=own.difference(mask);ratio=keep.area/own.area
        assert .85<ratio<.91,(variant,ratio)
        assert keep.geom_type=='Polygon'
        seam=geo.line_merge(own.intersection(mask.boundary)).simplify(.001)
        assert seam.geom_type=='LineString' and len(seam.coords)==2,(variant,seam)
        seams[variant]=seam
        result[variant]=dict(target_triangles=len(target),other_triangles=len(other),owner_assignment=assign,
          target_area_m2=own.area,retained_m2=keep.area,retained_percent=100*ratio,
          cut_area_m2=own.intersection(mask).area,mask_to_same_group_neighbors_m=mask.distance(other_projection),
          model_to_same_group_neighbors_m=model.distance(other_projection),cut_line_m=seam.length,roof_m=float(target[:,:,2].max()))
    assert seams['far'].hausdorff_distance(seams['near'])<.15
    # Close only the cut through the original north frontage; all other buildings retain their own sources.
    adjacent_groups=[g for g in evidence['near_tiles']if OWNER not in g['feature_local_ids']]
    extra=separate_group_distances(site,adjacent_groups,mask)
    min_gap=min(e['nearest_geometry_m']for e in extra)
    assert min_gap>.12,min_gap
    near=sorted((mask.distance(o),i)for i,o in site.footprints.items()if i!=OWNER)
    assert near[0][0]>.28,near[:3]
    checks=[('Hong Kong Road pavement',0,-1.17,False),('first stair',0,-.34,False),('principal aisle between columns',0,.70,False),
            ('sheltered approach',0,2.15,False),('recess between door jambs',0,3.15,False),('closed central door',0,3.43,True),
            ('back masonry',2.34,2.78,True),('east round column',-1.47,.65,True),('west round column',4.41,.65,True),
            ('western engaged column',7.35,.63,True),('eastern side bay',-9.14,.18,True),('original block behind the study',0,8.1,True)]
    ground_case=[]
    for label,x,y,solid in checks:
        q=geo.Point(x,y);screened=mask.covers(q);obs=collision.covers(q)
        assert (obs if screened else site.footprints[OWNER].covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(obs),cut=bool(screened)))
    src=next(r for r in evidence['owners']if r['local_id']==OWNER);ready=read(site.files['READY.json'])
    heading=evidence['author_frame']['runtime_heading_deg'];neighbors=[366,2229,944,1162]
    contract=dict(id=ID,owner=dict(macro_id=evidence['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[src['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,
        scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),
        source_section_caps=dict(geometry=site.wgs(geo.MultiLineString([seams['far']])),base_m=0,roof_m=result['far']['roof_m'],
           height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=220,overviewPitch=38,overviewZoom=19.75,maxDistance=480,lod_switch_in_m=550,lod_switch_out_m=700,
        navigation=dict(listed=False,status='香港路59号临街柱廊俯瞰。'),placement=dict(status='estimated',
          note='香港路南侧2170的一段北面石柱廊。原城市建筑后段、两侧独立街坊及对街楼体保留，边缘按原屋顶高度补切面。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,existingGroupOwners=[],existingCandidateOwners=[],
              groupTriangles=2,addedTriangles=2,sourceSectionCount=1,
              front=dict(center=[0,.96],elevation=5.75,pitch=38,zoom=19.72,bearingOffset=220-heading),
              roof=dict(center=[0,2.45],elevation=9.4,pitch=30,zoom=19.42,bearingOffset=210-heading),ground=ground_case,
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,owner=OWNER,manifest_sha256=sha(args.manifest),assets=assets,
        source=result,source_cap_segments=1,mask_m2=mask.area,model_projection_m2=model.area,
        step_and_other_ground_mesh_projection_m2=ground.area,modeled_obstacles_m2=collision.area,ground_witnesses=ground_case,
        independent_neighbor_meshes=extra,nearest_footprints=[dict(local_id=i,clearance_m=d)for d,i in near[:6]],
        checker_sha256=sha(Path(__file__)),common_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
