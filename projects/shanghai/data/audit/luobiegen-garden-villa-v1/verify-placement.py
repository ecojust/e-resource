"""Bind the main villa to OSM way 1316079023 while retaining its western connecting strip."""
import argparse
from pathlib import Path
import sys

import numpy as np
import shapely as geo

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha

ID='changning-luobiegen-garden-villa'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    src=PROJECT/'source/precise'/ID/'footprint-review.json';review=read(src)
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,collision=site.decode_model(args.manifest)
    owner=1431;source=site.footprints[owner]
    group=next(tile for tile in review['near_tiles'] if owner in tile['feature_local_ids'])
    variants=site.decode_group(group,owner)
    west_limit=model.bounds[0]-.18
    documented_side=geo.box(west_limit,-50,50,50)
    projected={name:site.project_faces(triangles[0]) for name,triangles in variants.items()}
    rendered_body=geo.union_all([source,*projected.values()]).intersection(documented_side)
    mask=geo.union_all([model,rendered_body]).convex_hull.buffer(.075,join_style='mitre').intersection(documented_side)
    assert model.covered_by(mask) and mask.is_valid and mask.geom_type=='Polygon'
    old_strip=source.difference(mask)
    assert old_strip.area>35 and 250<source.intersection(mask).area<370
    other_features={i:p for i,p in site.footprints.items() if i!=owner}
    nearest=sorted([(i,p.distance(mask),p.distance(model)) for i,p in other_features.items()],key=lambda r:r[1])
    assert nearest[0][1]>.5,nearest[:3]
    evidence={}
    for name,(own,others,method) in variants.items():
        native=projected[name];same_group=site.project_faces(others);outside=native.difference(mask)
        assert native.intersection(documented_side).difference(mask).area<.0005
        assert mask.disjoint(same_group) and model.disjoint(same_group)
        assert outside.area>35 and abs(outside.area-old_strip.area)<6
        evidence[name]={'owner_triangles':len(own),'source_height_m':float(own[:,:,2].max()),'source_assignment':method,
            'source_projected_m2':native.area,'outside_cut_kept_m2':outside.area,'residual_on_main_side_m2':native.intersection(documented_side).difference(mask).area,
            'mask_to_other_members_m':mask.distance(same_group),'model_to_other_members_m':model.distance(same_group)}
    # Probe native contact surfaces and the old strip independently of any size metadata.
    cells=[('garden front open between gables',-3.0,-9.24,False),('enclosed west bay',-7.58,-7.21,True),('central hall',-2.7,0,True),
           ('east end room',7.6,0,True),('south garden',-.7,-14,False),('western connecting strip',-15.4,3.82,False)]
    probes=[]
    for label,x,y,blocked in cells:
        pt=geo.Point(x,y);got=collision.covers(pt);assert got==blocked,(label,got)
        old=source.covers(pt);cut=mask.covers(pt);probes.append({'name':label,'local_xy':[x,y],'wgs84':site.to_wgs(np.array([[x,y]]))[0].tolist(),
            'in_original_owner':old,'in_replacement_mask':cut,'in_model_collision':got,'expected_city_collision':'building' if got or (old and not cut) else None})
    assert probes[-1]['in_original_owner'] and not probes[-1]['in_replacement_mask']
    rec=review['owners'][0];frame=review['author_frame'];assert rec['local_id']==owner and rec['record_id']=='w1316079023@2'
    contract={'id':ID,'owner':{'macro_id':review['frozen_macro'],'feature_local_id':owner},'source_feature_ids':{'building':[rec['key'].split(':')[1]],'building_part':[]},
       'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(collision),'lng':site.lon,'lat':site.lat,'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,
       'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'overviewBearing':-11,'overviewPitch':52,'overviewZoom':19,
       'maxDistance':450,'lod_switch_in_m':510,'lod_switch_out_m':650,'navigation':{'listed':False,'status':'罗别根花园英式主宅花园立面与屋脊俯瞰。'},
       'placement':{'status':'estimated','note':'依2017年南向花园照片方位、区规划资源局双山墙照片、屋顶影像与OSM源体1431配准主宅。西侧原有狭长连接段及独立长排均保留。'},
       'partial_model':True,'model_scope':read(args.manifest)['scope']}
    out=args.out;out.mkdir(parents=True,exist_ok=True);write(out/'final-placement-contract.json',contract)
    write(out/'placement-geometry.json',{'id':ID,'script_sha256':sha(Path(__file__)),'helper_sha256':sha(PROJECT/'tools/candidate_placement_meshes.py'),
       'source_sha256':sha(src),'manifest_sha256':sha(args.manifest),'contract_sha256':sha(out/'final-placement-contract.json'),'assets':assets,'variants':evidence,
       'source_footprint_m2':source.area,'source_remainder_m2':old_strip.area,'model_projection_m2':model.area,'model_collision_m2':collision.area,'mask_m2':mask.area,
       'western_cut_local_x_m':west_limit,'nearest_preserved_sources_m':[{'local_id':i,'mask_clearance':d,'model_clearance':m}for i,d,m in nearest[:7]],'ground_probes':probes})
    print('Verified',ID,evidence,old_strip.area,nearest[:2],flush=True)


if __name__=='__main__':main()
