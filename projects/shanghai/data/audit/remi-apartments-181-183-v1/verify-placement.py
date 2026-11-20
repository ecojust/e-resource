"""Measure both household sources in their separate streamed groups and the remaining row houses."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys
import numpy as np
import shapely as geo
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ID='xuhui-remi-apartments-181-183'
OWNERS=[2268,2598]
NEIGHBORS=[3215,2035,1065,159,2530]
GROUPED=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--out',type=Path,default=HERE)
    cli.add_argument('--previous',default='xuhui-yongjia-village-no15')
    args=cli.parse_args()
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    byid={f['local_id']:f for f in review['owners']}
    # Separate frozen fronts form a shallow angle at their common party wall.
    mask=geo.box(-3.69,-.34,4.24,1.80)
    depth=1.75
    body=geo.box(-3.63,0,4.18,depth)
    clear=geo.union_all([geo.box(-.565-.815/2,.0,-.565+.815/2,.284),
                         geo.box(.535-.835/2,.0,.535+.835/2,.284)])
    collision=body.difference(clear)
    source={};seams={};heights={};groups={}
    for group in review['near_tiles']:
        identity=sorted(set(group['feature_local_ids'])&set(OWNERS))
        assert len(identity)==1
        owner=identity[0]
        groups[group['id']]=identity
        row={}
        for variant,tr,assigned,ties in GROUPED(site,group):
            actual=tr[assigned==owner];retained=tr[(assigned!=owner)|ties]
            target=site.project_faces(actual);protected=site.project_faces(retained)
            assert target.intersects(mask) and protected.disjoint(mask),(owner,variant,protected.intersection(mask).area)
            portion=target.intersection(mask)
            percent=100*(1-portion.area/target.area)
            assert 89<percent<99,(owner,variant,percent)
            section=target.intersection(mask.boundary).simplify(.018)
            seams[owner,variant]=section
            heights[owner,variant]=float(actual[:,:,2].max())
            row[variant]=dict(owner_faces=len(actual),protected_faces=len(retained),protected_ambiguous_faces=int(ties.sum()),
                              closest_protected_face_m=mask.distance(protected),original_m2=target.area,cut_m2=portion.area,
                              retained_percent=percent,roof_m=heights[owner,variant],seam_length_m=section.length)
        source[owner]=row
    assert len(groups)==2 and set(source)==set(OWNERS)
    back_near=geo.union_all([seams[i,'near']for i in OWNERS])
    back_far=geo.union_all([seams[i,'far']for i in OWNERS])
    assert back_far.hausdorff_distance(back_near)<.35
    # The far sources measure 16.00 and 16.10 m. The shared section uses their midpoint.
    assert abs(heights[2268,'far']-heights[2598,'far'])<.12,heights
    section_height=(heights[2268,'far']+heights[2598,'far'])/2
    coords=[(a,b)for ln in geo.get_parts(geo.line_merge(back_far).simplify(.020)) for a,b in zip(ln.coords,list(ln.coords)[1:])if geo.Point(a).distance(geo.Point(b))>.04]
    assert coords
    samples=[('street',0,-1.5,False),('front of 181',-.565,-.12,False),('entry 181',-.565,.145,False),
             ('door 181',-.565,.40,True),('entry 183',.535,.145,False),('door 183',.535,.40,True),
             ('dividing pier',0,.10,True),('181 wall',-2.7,.28,True),('183 wall',2.6,.27,True),
             ('rear original 181',-2.1,4.8,True),('rear original 183',2.0,4.8,True),
             ('approach to 179',-4.8,-.8,False),('approach to 185',5.8,-.8,False)]
    orig=geo.union_all([site.footprints[i]for i in OWNERS])
    requests=[]
    for label,x,y,blocked in samples:
        pt=geo.Point(x,y);cut=mask.covers(pt);solid=collision.covers(pt)
        assert (solid if cut else orig.covers(pt))==blocked,label
        requests.append(dict(name=label,xy=[x,y],**({'ownerLocalId':2268 if x<0 else 2598} if label.startswith('rear original') else {}),expected='building'if blocked else None,modelObstacle=solid,cut=cut))
    report=dict(model_id=ID,owner_results=source,owners_by_group=groups,collision_m2=collision.area,mask_m2=mask.area,ground=requests,
                section_roof_m=section_height,largest_vertical_cap_difference_m=max(abs(heights[o,'far']-section_height) for o in OWNERS),combined_section_segments=len(coords),combined_near_far_seam_difference_m=back_far.hausdorff_distance(back_near))
    write(args.out/'source-geometry.json',report)
    if not args.manifest:return
    assets,bounds,model,_=site.decode_model(args.manifest)
    assert mask.covers(model),(model.bounds,model.difference(mask).area)
    ready=read(site.files['READY.json'])
    owners=[dict(macro_id=review['frozen_macro'],feature_local_id=i)for i in OWNERS]
    heading=review['author_frame']['runtime_heading_deg']
    contract=dict(id=ID,owner=owners[0],owners=owners,source_feature_ids=dict(building=[byid[i]['key'][9:]for i in OWNERS],building_part=[]),
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,
        bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=161.56,overviewPitch=31,overviewZoom=20.1,
        maxDistance=470,lod_switch_in_m=460,lod_switch_out_m=650,source_section_caps=dict(geometry=site.wgs(geo.MultiLineString(coords)),base_m=0,
        roof_m=section_height,height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        placement=dict(status='estimated',note='三站识别181、183号和共用山墙。只裁分属不同近组的2268与2598临街前凸，保留后半栋与两侧入户。'),
        navigation=dict(listed=False,status='从永康路人行道看向181、183号双门山墙。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ['replacement','collision']:checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    case=dict(id=ID,previous=args.previous,addedOwners=OWNERS,neighbors=NEIGHBORS,
              groups=[dict(id=g,addedOwners=o,addedTriangles=2,groupTriangles=2)for g,o in groups.items()],
              addedTriangles=4,groupTriangles=2,residualCutProbes={'2268':[-1.2,.8],'2598':[1.2,.8]},sourceSectionCount=len(coords),ground=requests,
              front=dict(center=[0,.07],elevation=4.65,pitch=31,zoom=20.35,bearingOffset=0),
              roof=dict(center=[0,.52],elevation=8.7,pitch=30,zoom=20.22,bearingOffset=12),
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in NEIGHBORS})
    report.update(assets=assets,model_m2=model.area,manifest_sha256=sha(args.manifest))
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',report)


if __name__=='__main__':main()
