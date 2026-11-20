"""Bind the modelled entrance and retain the rest of the actual registered church."""
import argparse
from pathlib import Path
import sys
import numpy as np
from shapely import Point, union_all
from shapely.geometry import box, LineString, MultiLineString

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-dongjiadu-cathedral'
OWNER=1831

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',required=True,type=Path,help='Scratch directory, optionally preloaded with frozen city files by basename.')
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    args.output.mkdir(exist_ok=True,parents=True)
    source_file=PROJECT/'source/precise'/ID/'footprint-review.json'
    src=read(source_file)
    layout=PlacementMeshes(PROJECT,args.work,src)
    assets,bounds,full,foot=layout.decode_model(args.manifest)
    group=src['near_tiles'][0]
    pieces=layout.decode_group(group,OWNER)
    owner=layout.footprints[OWNER]
    seam_y=3.19
    replacement=owner.buffer(1.45,join_style=2).intersection(box(-20,-1.6,20,seam_y))
    # Floor behind the three physically closed leaves is enclosed by both returns and the rear wall.
    # Projections at walking height add the actual pilasters and door mouldings out front.
    collision=union_all([box(-15.31,.01,15.31,3.20),foot],grid_size=.001).simplify(.012,preserve_topology=True)
    assert full.difference(replacement.buffer(.025)).area<.006
    measured={}
    profiles={}
    for variant,(native,other,assignment) in pieces.items():
        mesh=layout.project_faces(native);profiles[variant]=mesh
        neighbors=layout.project_faces(other);removed=mesh.intersection(replacement)
        retained=mesh.difference(replacement)
        measured[variant]={'source_triangles':len(native),'adjacent_source_triangles':len(other),'scope_assignment':assignment,
            'footprint_m2':mesh.area,'cut_m2':removed.area,'retained_m2':retained.area,
            'retained_fraction':retained.area/mesh.area,'nearest_group_neighbor_m':neighbors.distance(replacement),
            'other_source_intersection_m2':neighbors.intersection(replacement).area,'height_m':float(native[:,:,2].max())}
        assert .91<measured[variant]['retained_fraction']<.97
        assert measured[variant]['other_source_intersection_m2']<.0001
    line=profiles['far'].intersection(LineString([(-25,seam_y),(25,seam_y)]))
    assert line.geom_type=='LineString' and 30<line.length<32
    neighbors={k:g.distance(replacement) for k,g in layout.footprints.items() if k!=OWNER and g.distance(replacement)<32}
    assert neighbors[1822]>4 and min(neighbors.values())>4
    ready=read(layout.files['READY.json']);s=src['owner']
    probes=[]
    def probe(label,x,y,occupied,detail,retained):
        p=Point(x,y);covered=collision.covers(p);old=owner.difference(replacement).covers(p)
        nearby=[i for i,g in layout.footprints.items()if i!=OWNER and g.covers(p)]
        assert covered==detail and old==retained and bool(old or covered or nearby)==occupied,(label,covered,old,nearby)
        probes.append({'label':label,'point':layout.to_wgs(np.array([[x,y]]))[0].tolist(),'expected':'building' if occupied else None,'detail_collision':covered,'retained_owner':old,'other_original_owners':nearby})
    probe('recessed closed central door',0,.405,True,True,False)
    for x in [-8.93,8.93]:probe('closed side door '+str(x),x,.40,True,True,False)
    probe('inside the untouched nave',0,15,True,False,True)
    probe('near north end of the church',0,48,True,False,True)
    probe('forecourt outside south entrance',0,-4,False,False,False)
    probe('east path outside side wall',17.8,2,False,False,False)
    probe('east adjoining area building',*layout.footprints[1822].representative_point().coords[0],True,False,False)
    cap={'base_m':0,'roof_m':measured['far']['height_m'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
         'far_sha256':sha(layout.files['far.glb']),'geometry':layout.wgs(MultiLineString([line]))}
    manifest=read(args.manifest);frame=src['author_frame']
    contract={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':s['macro_id'],'feature_local_id':OWNER},
        'source_feature_ids':{'building':[s['source_key'].split(':')[1]],'building_part':[]},'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},
        'replacement_geometry':layout.wgs(replacement),'collision_geometry':layout.wgs(collision),'source_section_caps':cap,
        'overviewBearing':1,'overviewPitch':67,'overviewZoom':19.16,'maxDistance':550,'lod_switch_in_m':550,'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'董家渡天主堂历史南入口，供俯瞰。'},
        'placement':{'status':'estimated','note':'以董家渡路北侧的具名主堂轮廓南边和航片配准。原有主体及邻楼保留，入口历史外观取自2010至2012年照片。'},
        'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    write(args.output/'final-placement-contract.json',contract)
    report={'model_id':ID,'script_sha256':sha(Path(__file__)),'source_review_sha256':sha(source_file),'assets':assets,'manifest_sha256':sha(args.manifest),
        'source':s,'native':measured,'all_macro_neighbor_clearance_m':neighbors,'section_cap_length_m':line.length,
        'full_detailed_projection_m2':full.area,'ground_mesh_projection_m2':foot.area,'closed_floor_and_mesh_collision_m2':collision.area,
        'removed_vector_m2':owner.intersection(replacement).area,'retained_vector_m2':owner.difference(replacement).area,'probe_points':probes,
        'contract_sha256':sha(args.output/'final-placement-contract.json')}
    write(args.output/'placement-geometry.json',report)
    print({k:(v['retained_fraction'],v['nearest_group_neighbor_m'])for k,v in measured.items()})
if __name__=='__main__':main()
