"""Verify the garden house while retaining the northern wing and every neighbouring structure."""
import argparse
import subprocess
import shapely as geo
from pathlib import Path
import sys
import numpy as np
from shapely import Point, union_all
from shapely.geometry import box, LineString, MultiLineString

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='jingan-jewish-club'
OWNER=2124

def classify_sources(layout,group):
    # This group almost touches a second building. Test every vertex in addition to triangle centres.
    layout.link('baseline-far.glb',layout.files['far.glb'])
    layout.link('baseline-near.glb.gz',layout.files[Path(group['file']).name])
    layout.link('macro-READY.json',layout.files['READY.json'])
    ids=group['feature_local_ids']
    write(layout.work/'context-features.json',[{'localId':i}for i in ids])
    subprocess.run(['node',layout.decoders/'map-decode-source.mjs'],env=layout.env,cwd=layout.work,check=True,stdout=subprocess.DEVNULL)
    out={}
    for variant in ['near','far']:
        tri=np.fromfile(layout.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2]@layout.axes.T
        if variant=='far':
            assigned=np.fromfile(layout.work/'baseline-far-owners.u32',np.uint32)
            evidence={'method':'per-vertex _FEATURE_ID_0'}
        else:
            assigned=None;checks=[]
            for weights in [[1/3]*3,[1.,0,0],[0,1.,0],[0,0,1.]]:
                points=geo.points(np.asarray(weights)@tri[:,:,:2])
                matrix=np.column_stack([geo.distance(points,layout.footprints[i]) for i in ids])
                choice=np.asarray(ids)[matrix.argmin(axis=1)]
                if assigned is None:assigned=choice
                assert np.array_equal(assigned,choice)
                ranked=np.sort(matrix[choice==OWNER],axis=1)
                worst=float(ranked[:,0].max());margin=float((ranked[:,1]-ranked[:,0]).min())
                assert worst<.105 and margin>3*worst
                checks.append({'barycentric':weights,'largest_own_distance_m':worst,'smallest_next_owner_margin_m':margin})
            evidence={'method':'All three vertices of every triangle and its centroid agree on the nearest registered footprint',
                      'triangle_ownership_disagreements':0,'samples':checks}
        assert set(assigned)==set(ids)
        out[variant]=(tri[assigned==OWNER],tri[assigned!=OWNER],evidence)
    return out

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
    pieces=classify_sources(layout,group)
    owner=layout.footprints[OWNER]
    seam_y=15.82
    replacement=owner.buffer(.225,join_style=2).intersection(box(-30,-1.5,30,seam_y))
    # The back of the ground-floor galleries is closed behind glass. All three doorways and side windows
    # are shut. Only fill the occupied ground-floor envelope, preserving the open visitor court.
    vertices=[(-28.43,1.58),(-26.81,-.08),(-22.08,-.08),(-20.52,1.67),(-20.52,.38),
              (-6.60,.38),(-6.60,1.25),(-3.22,1.25),(-3.22,-.28),(3.22,-.28),(3.22,1.25),
              (6.60,1.25),(6.6,.38),(20.52,.38),(20.52,1.67),(22.08,-.08),(26.81,-.08),
              (28.43,1.58),(28.43,15.86),(-28.43,15.86)]
    collision=union_all([geo.Polygon(vertices),foot],grid_size=.001).simplify(.025,preserve_topology=True)
    assert full.intersection(owner).difference(replacement).area<1
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
        assert .20<measured[variant]['retained_fraction']<.26
        assert measured[variant]['other_source_intersection_m2']<.0001
    line=profiles['far'].intersection(LineString([(-25,seam_y),(25,seam_y)]))
    assert line.geom_type=='LineString' and 14<line.length<16
    neighbors={k:g.distance(replacement) for k,g in layout.footprints.items() if k!=OWNER and g.distance(replacement)<32}
    assert min(neighbors.values())>.17 and neighbors[2772]<.5
    ready=read(layout.files['READY.json']);s=src['owner']
    probes=[]
    def probe(label,x,y,occupied,detail,retained):
        p=Point(x,y);covered=collision.covers(p);old=owner.difference(replacement).covers(p)
        nearby=[i for i,g in layout.footprints.items()if i!=OWNER and g.covers(p)]
        assert covered==detail and old==retained and bool(old or covered or nearby)==occupied,(label,covered,old,nearby)
        probes.append({'label':label,'point':layout.to_wgs(np.array([[x,y]]))[0].tolist(),'expected':'building' if occupied else None,'detail_collision':covered,'retained_owner':old,'other_original_owners':nearby})
    probe('central passage leads to the closed front door',0,1.63,True,True,False)
    probe('western glazed ground-floor gallery',-12.1,.76,True,True,False)
    probe('eastern glazed ground-floor gallery',12.1,.76,True,True,False)
    probe('remaining northern wing',12,23,True,False,True)
    probe('retained lawn and carriage drive',0,-5,False,False,False)
    probe('courtyard behind west roof',-14,19.5,False,False,False)
    for n in [2772,2624,2228,803]:
        probe('neighbour '+str(n),*layout.footprints[n].representative_point().coords[0],True,False,False)
    cap={'base_m':0,'roof_m':measured['far']['height_m'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],
         'far_sha256':sha(layout.files['far.glb']),'geometry':layout.wgs(MultiLineString([line]))}
    manifest=read(args.manifest);frame=src['author_frame']
    contract={'id':ID,**frame['anchor'],'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,'owner':{'macro_id':s['macro_id'],'feature_local_id':OWNER},
        'source_feature_ids':{'building':[s['source_key'].split(':')[1]],'building_part':[]},'bounds_glb':bounds,'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},
        'replacement_geometry':layout.wgs(replacement),'collision_geometry':layout.wgs(collision),'source_section_caps':cap,
        'overview_focus_bounds_glb':{'min':[-6,0,-2],'max':[6,13.1,.5]},
        'overviewBearing':-1,'overviewPitch':65,'overviewZoom':19.0,'maxDistance':550,'lod_switch_in_m':550,'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'南京西路722号宅邸南楼面向庭院的外观，供俯瞰。'},
        'placement':{'status':'estimated','note':'按原体2124南边、办公地址和影像定位。保留北侧垂直翼和所有相邻原体，南京西路702号另列。'},
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
