"""Cut the verified central pavilion out of one source; retain and close both wings."""
import argparse
from pathlib import Path
import sys

import shapely as geo
from shapely.geometry import box, MultiLineString, shape

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha

ID='xuhui-zhongshan-hospital-main-building'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,pavilion,ground=site.decode_model(args.manifest)
    # Actual roof edges extend to 28.268 m. The lower end-bays continue to 28.24 m.
    # Only the original coarse source can be cut. Both surviving wings need end walls.
    cut=box(-28.285,-10.35,28.285,10.35)
    assert cut.covers(pavilion) and ground.is_valid
    assert all(len(p.exterior.coords)<256 for p in ([ground]if ground.geom_type=='Polygon'else ground.geoms))
    group=review['near_tiles'][0];assert set(group['feature_local_ids'])=={2186,1132}
    checks={};sections={}
    for variant,(source,others,attribution) in site.decode_group(group,2186).items():
        original=site.project_faces(source);other=site.project_faces(others)
        retained=original.difference(cut)
        assert len(retained.geoms)==2 and min(a.area for a in retained.geoms)>350
        seams=geo.line_merge(cut.boundary.intersection(original)).simplify(.003)
        assert seams.geom_type=='MultiLineString' and len(seams.geoms)==2
        sections[variant]=seams
        assert all(abs(line.length-17.6)<1.18 for line in seams.geoms),[a.length for a in seams.geoms]
        assert cut.disjoint(other) and pavilion.disjoint(other)
        roof=float(source[:,:,2].max())
        checks[variant]={'owner_triangles':len(source),'other_owner_triangles':len(others),'assignment':attribution,'source_m2':original.area,
                         'replaced_m2':original.intersection(cut).area,'retained_wings_m2':sorted(g.area for g in retained.geoms),
                         'retained_other_owner_area_m2':other.area,'cut_to_other_member_m':cut.distance(other),
                         'wing_section_lengths_m':[l.length for l in seams.geoms],'source_roof_m':roof}
    assert sections['near'].hausdorff_distance(sections['far'])<.75
    assert abs(checks['near']['source_roof_m']-checks['far']['source_roof_m'])<.1
    nearest=sorted((cut.distance(g),i)for i,g in site.footprints.items() if i!=2186)
    assert nearest[0][0]>1,nearest[:3]
    ready=read(site.files['READY.json'])
    cap={'geometry':site.wgs(sections['far']),'base_m':0,'roof_m':checks['far']['source_roof_m'],
         'far_sha256':sha(site.files['far.glb']),'height_reference':[ready['origin_longitude'],ready['origin_latitude']]}
    row={'id':ID,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':2186},
         'source_feature_ids':{'building':[review['owner']['key'].split(':')[1]],'building_part':[]},
         'replacement_geometry':site.wgs(cut),'collision_geometry':site.wgs(ground),'source_section_caps':cap,
         'lng':site.lon,'lat':site.lat,'heading':review['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
         'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},
         'overviewBearing':100,'overviewPitch':49,'overviewZoom':18.8,'maxDistance':560,'lod_switch_in_m':550,'lod_switch_out_m':700,
         'navigation':{'listed':False,'status':'中山医院3号楼历史中央主楼、第五层平台与琉璃屋顶俯瞰。'},
         'placement':{'status':'estimated','note':'实名3号楼源仅开两个垂直剖面，中间置入实照明确的主楼。保留东西原生翼段、周边院楼与北侧空间。'},
         'partial_model':True,'model_scope':read(args.manifest)['scope']}
    write(args.out/'final-placement-contract.json',row)
    write(args.out/'placement-geometry.json',{'model_id':ID,'checked_against':review['baseline_commit'],'script_sha256':sha(Path(__file__)),
        'shared_checker_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),'manifest_sha256':sha(args.manifest),
        'assets':assets,'source':checks,'source_group':group,'collision_m2':ground.area,'profile_m2':pavilion.area,
        'source_cut_xy_m':cut.bounds,'near_to_far_seam_delta_m':sections['near'].hausdorff_distance(sections['far']),
        'nearest_unchanged_sources':[{'id':i,'clearance_m':d}for d,i in nearest[:10]],'contract_sha256':sha(args.out/'final-placement-contract.json')})
    print('ground,profile,retained wings',ground.area,pavilion.area,[(k,v['retained_wings_m2'])for k,v in checks.items()])

if __name__=='__main__':main()
