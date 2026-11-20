"""Fit Wayfoong House, protecting the lower party neighbor on Middle Sichuan Road."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-wayfoong-house'
OWNER,PARTY=419,1787
GROUP_CHECK=PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--work',required=True,type=Path)
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--out',type=Path,default=HERE)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    source=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,a.work,source);mf=read(a.manifest)
    assets,bounds,model,ground=site.decode_model(a.manifest)
    old=site.footprints[OWNER];peer=site.footprints[PARTY]
    group=next(g for g in source['near_tiles'] if OWNER in g['feature_local_ids'])
    ids=group['feature_local_ids'];rows={r['local_id']:r for r in source['owners']}
    envelope=old.buffer(.37,join_style='mitre')
    protected=peer.buffer(.345,join_style='mitre')
    full_cut=envelope.difference(protected);upper_cut=envelope.intersection(protected)
    assert old.intersection(peer).area>7.8 and model.distance(peer)>.28
    assert full_cut.geom_type==upper_cut.geom_type=='Polygon'
    zlimit=22.55
    data={};far_owner=None
    for variant,tri,labels,ties in runpy.run_path(str(GROUP_CHECK))['grouped_sources'](site,group):
        high=tri[:,:,2].max(1)
        if variant=='near':
            verts=geo.points(tri[:,:,:2].reshape(-1,2));heights=np.array([rows[i]['source_height_m'] for i in ids])
            distances=np.stack([geo.distance(verts,site.footprints[i]).reshape(-1,3).max(1) for i in ids],axis=1)
            # Retain every plausible 1787 face, including the 261 ambiguous wall faces.
            fits=(distances<=.395)&(high[:,None]<=heights[None,:]+.05)
            assert fits.any(1).all() and distances.min(1).max()<.105
            belongs=fits[:,ids.index(OWNER)];party=fits[:,ids.index(PARTY)]
            ambiguous=fits.sum(1)>1;assert (belongs[ambiguous]&party[ambiguous]).all()
        else:
            belongs=labels==OWNER;party=labels==PARTY;ambiguous=np.zeros(len(tri),bool)
        possible_peer=site.project_faces(tri[party]);independent=site.project_faces(tri[~belongs&~party])
        owner=site.project_faces(tri[belongs]);peak=float(high[party].max())
        assert abs(peak-22.4)<.012 and abs(high[belongs].max()-32)<.015
        assert zlimit>peak+.12 and model.distance(possible_peer)>.22
        assert full_cut.disjoint(possible_peer) and envelope.disjoint(independent)
        if variant=='far':
            far_owner=owner
            assert envelope.covers(owner)
        data[variant]=dict(group=group['id'],total_faces=len(tri),owner_faces=int(belongs.sum()),
            protected_faces=int(party.sum()),ambiguous_party_faces=int(ambiguous.sum()),
            independent_faces=int((~belongs&~party).sum()),model_to_peer_m=model.distance(possible_peer),
            full_cut_to_peer_m=full_cut.distance(possible_peer),independent_clearance_m=envelope.distance(independent),
            source_height_m=float(high[belongs].max()),peer_height_m=peak,retained_low_strip_m2=owner.intersection(upper_cut).area)
    lines=geo.line_merge(protected.boundary.intersection(far_owner)).simplify(.0002)
    caps=MultiLineString([lines] if lines.geom_type=='LineString' else list(lines.geoms))
    assert 1<=len(caps.geoms)<=2 and caps.length>24
    frame=read(site.files['READY.json']);href=[frame['origin_longitude'],frame['origin_latitude']]
    own=dict(macro_id=source['frozen_macro'],feature_local_id=OWNER)
    # Exclude the walkable 12cm thresholds and the flush entrance floor to the two closed glass leaves.
    niches=geo.union_all([geo.box(x-1.38,-.56,x+1.38,.86) for x in [-17.58,17.58]])
    collision=ground.difference(niches).simplify(.012)
    probes=[('四川中路人行道',[0,-1.60],False),('中央商业底层',[0,.64],True),('前座',[0,7],True),
            ('后座',[0,27],True),('东侧服务巷',[1,31.0],False)]
    for x in [-17.58,17.58]:
        probes.extend([('门外',[x,-.58],False),('凹门洞',[x,.41],False),('门扇之后',[x,1.03],True),
                       ('石门框旁',[x+1.52,.04],True)])
    ground_probes=[]
    for name,xy,expected in probes:
        observed=collision.covers(geo.Point(xy));assert observed==expected,(name,xy,observed)
        ground_probes.append(dict(label=name,xy=xy,expected_solid=expected,actual_solid=observed))
    for polygon,label in [(full_cut,'full cut'),(upper_cut,'shared upper cut'),(collision,'collision')]:
        checked_geometry(site.wgs(polygon),label,collision=label=='collision')
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[rows[OWNER]['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(full_cut),collision_geometry=site.wgs(collision),
        display_height_clips=[dict(id=ID+'-south-shared-upper-trim',owner=own,geometry=site.wgs(upper_cut),
            min_height=zlimit,max_height=34.0,height_reference=href)],
        source_section_caps=dict(geometry=site.wgs(caps),base_m=0,roof_m=zlimit,height_reference=href,far_sha256=sha(site.files['far.glb'])),
        lng=site.lon,lat=site.lat,heading=source['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
        bounds_glb=bounds,model_geometry_sha256={i:t['sha256']for i,t in assets.items()},
        overviewBearing=80,overviewPitch=38,overviewZoom=18.38,maxDistance=630,lod_switch_in_m=650,lod_switch_out_m=800,
        navigation=dict(listed=False,status='从四川中路观赏新汇丰大楼西立面和两端入口。'),
        placement=dict(status='map-aligned',note='实名419对应四川中路210–220号。南侧1787屋面的22.40米以下完整保留，另为419的上段裁剪。'),
        partial_model=True,model_scope=mf['scope'])
    write(a.out/'final-placement-contract.json',contract)
    write(a.out/'placement-geometry.json',dict(model_id=ID,assets=assets,manifest_sha256=sha(a.manifest),
        source_area_m2=old.area,source_party_overlap_m2=old.intersection(peer).area,full_cut_m2=full_cut.area,
        shared_upper_cut_m2=upper_cut.area,actual_model_m2=model.area,ground_m2=collision.area,
        ground_probes=ground_probes,source_tests=data,cap_length_m=caps.length,cap_segments=sum(len(q.coords)-1 for q in caps.geoms),
        neighbors=[dict(local_id=i,mesh_to_source_m=model.distance(site.footprints[i]),full_cut_clearance_m=full_cut.distance(site.footprints[i])) for i in [PARTY,1362,536,529,1960]],
        checker_sha256=sha(Path(__file__)),grouped_decoder_sha256=sha(GROUP_CHECK),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
    print('Wayfoong House party geometry and both doors verified')


if __name__=='__main__':
    main()
