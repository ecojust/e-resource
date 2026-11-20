"""Bind the Continental Bank north frontage to its delivered meshes and the registered city GLBs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import LineString, MultiLineString, box, mapping, shape

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',required=True,type=Path)
parser.add_argument('--manifest',required=True,type=Path)
parser.add_argument('--macro',required=True,type=Path,help='Directory containing READY.json, far.glb and the registered near tile')
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
project=args.project.resolve();sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ident='huangpu-continental-bank'
src=read(project/'source/precise'/ident/'footprint-review.json')
manifest=read(args.manifest)
def decoded_attached_owners(layout, group, cut):
    """Exclude both sides of every near triangle ambiguous at the shared party wall."""
    import subprocess
    ids=group['feature_local_ids']
    layout.link('baseline-far.glb',layout.files['far.glb'])
    layout.link('baseline-near.glb.gz',layout.files[Path(group['file']).name])
    layout.link('macro-READY.json',layout.files['READY.json'])
    write(layout.work/'context-features.json',[{'localId':i} for i in ids])
    subprocess.run(['node',layout.decoders/'map-decode-source.mjs'],env=layout.env,check=True,stdout=subprocess.DEVNULL)
    output={}
    for variant in ['far','near']:
        tris=np.fromfile(layout.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
        tris[:,:,:2]=tris[:,:,:2]@layout.axes.T
        if variant=='far':
            labels=np.fromfile(layout.work/'baseline-far-owners.u32',np.uint32)
            result={'method':'decoded per-vertex _FEATURE_ID_0'}
        else:
            centers=geo.points(tris[:,:,:2].mean(1))
            distances=np.stack([geo.distance(centers,layout.footprints[i])for i in ids],axis=1)
            sorted_distance=np.sort(distances,axis=1)
            labels=np.asarray(ids)[np.argmin(distances,axis=1)]
            # 1718 and 1782 share a party edge. Treat all primitives whose first two
            # distances differ by less than 0.45m as potentially belonging to either.
            margin=sorted_distance[:,1]-sorted_distance[:,0]
            ambiguous=margin<.45
            assert sorted_distance[:,0].max()<.085
            assert set(labels[ambiguous])=={1718,1782}
            # Use a convex hull for every individual projected triangle: this keeps
            # collapsed, near-vertical edges as lines instead of discarding them.
            possible=geo.union_all(geo.convex_hull(geo.multipoints(tris[ambiguous,:,:2])))
            assert possible.disjoint(cut) and possible.distance(cut)>.060
            result={'method':'nearest registered footprint; both owners assigned conservatively at the narrow party wall',
                    'triangles':len(tris),'largest_triangle_center_distance_m':float(sorted_distance[:,0].max()),
                    'smallest_center_margin_m':float(margin.min()),'ambiguous_threshold_m':.45,
                    'ambiguous_by_nearest_owner':{str(i):int(sum(ambiguous&(labels==i)))for i in ids},
                    'all_ambiguous_projected_triangles_clear_cut':True,'ambiguous_triangle_clearance_m':possible.distance(cut)}
        assert set(labels)==set(ids)
        output[variant]=tris[labels==1718],tris[labels!=1718],result
    return output


with tempfile.TemporaryDirectory() as tmp:
    work=Path(tmp)
    for r in src['frozen_bindings']:
        suffix=r['repository_path'].split(src['owner']['macro_id']+'/')[1]
        shutil.copyfile(args.macro/suffix,work/Path(suffix).name)
    layout=PlacementMeshes(project,work,src)
    assets,bounds,full,foot=layout.decode_model(args.manifest)
    # The eastern party wall splays inward. Follow the surrounding owner's side
    # rather than using the rectangular bounding box of this street section.
    front_y=-.85;rear_y=8.38;west=15.06
    def east(y):return -15.32154+.06445*y+.51
    edges=[(east(front_y),front_y),(west,front_y),(west,rear_y),(east(rear_y),rear_y)]
    cut=geo.Polygon(edges)
    assert cut.is_valid
    pieces=decoded_attached_owners(layout,src['near_tiles'][0],cut)
    profiles={k:layout.project_faces(t) for k,(t,n,method) in pieces.items()}
    neighbors={k:layout.project_faces(n) for k,(t,n,method) in pieces.items()}
    # Roofs and fascia are measured outside the conservative cut near the party
    # wall. They may overlap the target's original shell, but never its neighbor.
    overhang=full.difference(cut)
    assert overhang.area/full.area < .01
    assert full.difference(cut.buffer(.30)).area < .0001
    assert full.intersection(layout.footprints[1782]).area < .0001
    coll=foot
    assert coll.is_valid and coll.intersection(layout.footprints[1782]).area<.0001
    # Each side cut and the rear line end on the original far-tile shell.
    seams=[profiles['far'].intersection(LineString([a,b])) for a,b in
           [(edges[1],edges[2]),(edges[2],edges[3]),(edges[3],edges[0])]]
    assert all(v.geom_type=='LineString' and v.length>7.8 for v in seams)
    line=MultiLineString(seams)
    # Source far and near floors are not presumed equal until the actual decoded faces are checked.
    heights={k:float(t[:,:,2].max()) for k,(t,n,m) in pieces.items()}
    info={};checks=[]
    for variant,shape2d in profiles.items():
        retained=shape2d.difference(cut)
        other=neighbors[variant]
        info[variant]={'source_projection_m2':shape2d.area,'retained_m2':retained.area,'retained_fraction':retained.area/shape2d.area,
                       'other_geometry_clip_overlap_m2':other.intersection(cut).area,'neighbor_clearance_m':other.distance(cut),
                       'peak_source_height_m':heights[variant],'assignment':pieces[variant][2]}
        assert .75<info[variant]['retained_fraction']<.77 and info[variant]['other_geometry_clip_overlap_m2']<.001
    limits={i:g.distance(cut) for i,g in layout.footprints.items() if i!=1718 and g.distance(cut)<50}
    assert .50<min(limits.values())<.52
    def probe(label,x,y,expected):
        q=geo.Point(x,y);lng,lat=layout.to_wgs(np.array([[x,y]]))[0];checks.append({'label':label,'point':[lng,lat],'expected':expected,'model_collision':coll.covers(q),'in_display_clip':cut.covers(q)})
    probe('floor inside the bank entrance',0.,1.35,'building')
    probe('remaining office block behind the street facade',0.,18.,'building')
    probe('public pavement on Jiujiang Road',0.,-2.20,None)
    for owner in [1782,2201,539,53]:
        pt=layout.footprints[owner].representative_point()
        probe('separate neighboring building '+str(owner),pt.x,pt.y,'building')
    assert checks[0]['model_collision'] and all(not c['model_collision'] for c in checks[1:])
    assert all(not c['in_display_clip'] for c in checks[1:])
    frames=src['author_frame'];anchor=frames['anchor']; ready=read(args.macro/'READY.json')
    # True model-space dimensions and near/far evidence are retained in the review.
    cap={'base_m':0,'roof_m':heights['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':ready['far']['sha256'],'geometry':layout.wgs(line)}
    contract={'id':ident,**anchor,'heading':frames['runtime_heading_deg'],'scale':1,'altitude':0,
              'owner':{'macro_id':src['owner']['macro_id'],'feature_local_id':1718},
              'source_feature_ids':{'building':[src['owner']['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':layout.wgs(cut),'collision_geometry':layout.wgs(coll),'source_section_caps':cap,
              'overviewBearing':151,'overviewPitch':39,'overviewZoom':19.5,'maxDistance':510,
              'lod_switch_in_m':550,'lod_switch_out_m':700,
              'navigation':{'listed':False,'status':'沿街立面局部模型，供俯瞰。'},
              'placement':{'status':'estimated','note':'正面沿九江路北偏西外墙定位。门洞阶梯以及约8.4米进深按照片估计，后部和两侧独立业主保留城市原景。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(json.loads(json.dumps(contract[k])),k,collision=k=='collision_geometry')
    args.output.mkdir(parents=True,exist_ok=True)
    write(args.output/'final-placement-contract.json',contract)
    write(args.output/'footprint-review.json',{'id':ident,'manifest_sha256':sha(args.manifest),'verified_source_sha256':sha(project/'source/precise'/ident/'footprint-review.json'),
        'script_sha256':sha(Path(__file__)),'source':src['owner'],'far_and_near':info,'near_tile':src['near_tiles'][0],'other_nearby_feature_minimum_clearance_m':min(limits.values()),
        'decoded_model_assets':assets,'bounds_glb':bounds,'full_mesh_projection_m2':full.area,'ground_mesh_projection_m2':foot.area,'collision_area_m2':coll.area,
        'clip_overlap_limit':{'target_projection_m2_outside_cut':overhang.area,'maximum_extension_m':.30,'model_eastern_neighbor_intersection_m2':full.intersection(layout.footprints[1782]).area},'section_cap_length_m':line.length,'probe_points':checks,'contract_sha256':sha(args.output/'final-placement-contract.json')})
    print(json.dumps(info,ensure_ascii=False))
