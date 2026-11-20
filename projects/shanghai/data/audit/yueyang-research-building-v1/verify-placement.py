"""Validate the hall, two unfilled courts, separate low porch source and retained campus buildings."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='xuhui-yueyang-320-research-building'
OWNERS=[714,715]
NEIGHBORS=[448,761,1044,1290,2134]


def read_group(site,group):
    ids=group['feature_local_ids']
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':i}for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    for variant in ['near','far']:
        vertices=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
        vertices[:,:,:2]=vertices[:,:,:2]@site.axes.T
        if variant=='far':
            owners=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            assignment={'method':'per-vertex _FEATURE_ID_0'}
        else:
            points=geo.points(vertices[:,:,:2].mean(1))
            distances=np.stack([geo.distance(points,site.footprints[i])for i in ids],axis=1)
            owners=np.asarray(ids)[distances.argmin(1)]
            assignment={'method':'triangle-centroid distance to its actual frozen group'}
            for i in set(ids)&set(OWNERS):
                ordered=np.sort(distances[owners==i],axis=1)
                own=float(ordered[:,0].max());margin=float((ordered[:,1]-ordered[:,0]).min())
                assert own<.43 and margin>1.5,(i,own,margin)
                assignment[str(i)]={'largest_own_distance_m':own,'minimum_next_owner_margin_m':margin}
        assert set(owners)==set(ids),(ids,set(owners))
        yield variant,vertices,owners,assignment


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--previous')
    cli.add_argument('--sources-only',action='store_true')
    cli.add_argument('--out',type=Path,default=HERE)
    args=cli.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    hall=site.footprints[714]
    courtyard=[geo.Polygon(ring)for ring in hall.interiors]
    assert len(courtyard)==2
    shell=geo.Polygon([(-48.48,-1.44),(-11.18,-1.44),(-11.18,-9.38),(11.18,-9.38),
                       (11.18,-1.44),(48.48,-1.44),(48.48,46.67),(-48.48,46.67)])
    mask=shell.difference(geo.union_all([c.buffer(-.63,join_style='mitre')for c in courtyard]))
    records=[]
    for group in review['near_tiles']:
        for variant,vertices,owners,assignment in read_group(site,group):
            covered=[]
            for i in sorted(set(owners)):
                tri=vertices[owners==i];plan=site.project_faces(tri)
                if i in OWNERS:
                    remaining=plan.difference(mask)
                    assert remaining.area<.0001,(variant,i,remaining.area,remaining.bounds)
                    for c in courtyard:assert not plan.intersects(c.representative_point()),(variant,i,'closed court')
                    covered.append(dict(local_id=int(i),triangles=len(tri),area_m2=plan.area,retained_m2=remaining.area,
                                        height_at_old_coarse_roof_m=float(tri[:,:,2].max())))
                else:
                    assert plan.disjoint(mask),(i,variant,plan.intersection(mask).area)
                    covered.append(dict(local_id=int(i),retained_triangles=len(tri),distance_to_clip_m=plan.distance(mask)))
            records.append(dict(group=group['id'],variant=variant,assignment=assignment,owners=covered))
    summary=dict(id=ID,owners=OWNERS,source_groups=records,courtyard_cut_clear_areas_m2=[c.difference(mask).area for c in courtyard],
                 ground_plan_independent_from_mesh=True,checker_sha256=sha(Path(__file__)))
    write(args.out/'source-geometry.json',summary)
    if args.sources_only:
        print('checked both source owners in near and far and both preserved courtyards')
        return
    assert args.manifest and args.previous
    assets,bounds,model,_=site.decode_model(args.manifest)
    assert mask.covers(model),(model.difference(mask).area,model.difference(mask).bounds)
    source_dir=PROJECT/'source/precise'/ID/'source'
    sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
    sys.path.insert(0,str(source_dir))
    from research_hall import BODY,PORT_CENTER,PORT_FRONT,PORT_WIDTH
    # Terrain and the steps remain walkable. Columns alone obstruct the seven front bays.
    interval=PORT_WIDTH/7
    cols=[geo.box(PORT_CENTER+(i-3.5)*interval-.297,PORT_FRONT-.05,
                  PORT_CENTER+(i-3.5)*interval+.297,PORT_FRONT+.58)for i in range(8)]
    collision=geo.union_all([BODY,*cols])
    ground=[]
    def witness(name,x,y,blocked):
        point=geo.Point(x,y)
        assert collision.covers(point)==blocked,name
        ground.append(dict(name=name,xy=[x,y],expected='building'if blocked else None,modelObstacle=blocked,cut=mask.covers(point)))
    for i in range(7):witness(f'open arcade bay {i+1}',PORT_CENTER+(i-3)*interval,PORT_FRONT+.27,False)
    for i in range(8):witness(f'square sandstone column {i+1}',PORT_CENTER+(i-3.5)*interval,PORT_FRONT+.27,True)
    for i,c in enumerate(courtyard):
        point=c.representative_point();witness(f'open inner court {i+1}',point.x,point.y,False)
    for name,x,y,v in [('east apron',0,-10.1,False),('front step',0,-7.59,False),('behind arch',0,-3.7,False),
                        ('central tower rear of doorway',0,-.39,True),('central spine',0,24.5,True),
                        ('south east wing',-22,4.1,True),('north east wing',22,4.1,True)]:
        witness(name,x,y,v)
    group=next(g for g in review['near_tiles']if 714 in g['feature_local_ids'])
    assert 715 in group['feature_local_ids']
    row={r['local_id']:r for r in review['owners']}
    owners=[dict(macro_id=review['frozen_macro'],feature_local_id=i)for i in OWNERS]
    contract=dict(id=ID,owner=owners[0],owners=owners,source_feature_ids=dict(building=[row[i]['key'][9:]for i in OWNERS],building_part=[]),
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,
        heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:r['sha256']for k,r in assets.items()},
        overviewBearing=254,overviewPitch=45,overviewZoom=18.16,maxDistance=660,lod_switch_in_m=540,lod_switch_out_m=760,
        navigation=dict(listed=False,status='从岳阳路一面看向在君楼的七券门廊。'),partial_model=True,model_scope=read(args.manifest)['scope'],
        placement=dict(status='estimated',note='以双院主楼714和前廊715配准。院落及独立邻楼保留，侧墙和西侧无逐窗照片处采用素面。'))
    for k in ['replacement','collision']:checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    # With holes, triangulation uses n+2h−2 triangles for the ring vertices.
    n=len(mask.exterior.coords)-1+sum(len(h.coords)-1 for h in mask.interiors)
    count=(n+2*len(mask.interiors)-2)*len(OWNERS)
    case=dict(id=ID,previous=args.previous,addedOwners=OWNERS,neighbors=NEIGHBORS,addedTriangles=count,groupTriangles=count,
              front=dict(center=[0,-3],elevation=9.20,pitch=40,zoom=19.08,bearingOffset=0),
              roof=dict(center=[0,21],elevation=11.70,pitch=27,zoom=18.51,bearingOffset=16),ground=ground,
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in NEIGHBORS})
    summary.update(manifest_sha256=sha(args.manifest),assets=assets,projection_m2=model.area,collision_m2=collision.area,mask_m2=mask.area,ground=ground)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'map-case.json',case);write(args.out/'placement-geometry.json',summary)


if __name__=='__main__':
    main()
