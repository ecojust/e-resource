"""Verify the corner residence, its ground-level recesses and neighboring house ownership."""
import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import Point, shape

audit = Path(__file__).resolve().parent
project = audit.parents[2]
sys.path.insert(0, str(project / 'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, sha, write

model = 'huangpu-king-albert-corner-house'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro', type=Path, required=True)
parser.add_argument('--vector', type=Path, required=True)
parser.add_argument('--manifest', type=Path, default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out', type=Path, default=audit)
args = parser.parse_args()


source_path = project/'source/precise'/model/'footprint-review.json'
source, vector, manifest = read(source_path), read(args.vector), read(args.manifest)
assert manifest['id'] == model and vector['sha256'] == '36448c327185ab13a8d07e723bda4d00dec0c1d36c6831a4c6aa50de13a07893'
owner = source['owner']
group, = source['near_tiles']
assert owner['feature_local_id'] == 5464 and len(group['feature_local_ids']) == 25
with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp)
    for receipt in source['frozen_bindings']:
        suffix = receipt['repository_path'].split(owner['macro_id']+'/')[1]
        (work/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh = PlacementMeshes(project,work,source)
    assets,bounds,profile,low_faces = mesh.decode_model(args.manifest)
    # The low surfaces include the actual lower wall and the rooms inside its
    # base. The northern recess between the rear wings remains open to the lane.
    collision=low_faces.buffer(.03,join_style='mitre').simplify(.035,preserve_topology=True)
    assert low_faces.difference(collision).area<.025
    decoded=mesh.decode_group(group,5464)
    originals={role:mesh.project_faces(v[0])for role,v in decoded.items()}
    retained={role:mesh.project_faces(v[1])for role,v in decoded.items()}
    original=mesh.footprints[5464]
    aggregate,=vector['features']
    assert aggregate['id']==1658263140 and aggregate['properties']['render_height']==15
    components=list(geo.transform(shape(aggregate['geometry']),mesh.to_xy).geoms)
    assert len(components)==17
    target=components[9]
    assert 320<target.intersection(original).area<400
    protected={int(i):mesh.footprints[int(i)]for i in source['named_neighbors']}
    contained=[profile,original,target,*originals.values()]
    mask=geo.union_all(contained).convex_hull.buffer(.065,join_style='mitre')
    assert all(g.difference(mask).area<.0001 for g in contained)
    assert all(g.distance(mask)>1. for g in retained.values())
    assert all(g.distance(mask)>1. for g in protected.values())
    assert all(part.intersection(mask).area==0 for i,part in enumerate(components) if i!=9)
    peers=sorted((g.distance(mask),i)for i,g in mesh.footprints.items()if i!=5464)
    assert peers[0][0]>1.,peers[:4]
    probes=[]
    for label,x,y,blocked in [('front living rooms',0,-4,True),('west octagonal bay',-6.4,-8.0,True),
          ('east octagonal bay',6.4,-8.0,True),('west rear wing',-5.9,6.4,True),('east rear wing',5.9,6.4,True),
          ('open court between rear wings',0,6.4,False),('between front bay and gable',0,-8.0,False),
          ('open west walkway',-11.2,0,False),('open east walkway',11.2,0,False),('south sidewalk',0,-12.7,False)]:
        pt=Point(x,y)
        assert collision.covers(pt)==blocked,(label,collision.covers(pt),collision.distance(pt))
        probes.append({'label':label,'xy':[x,y],'point':mesh.to_wgs(np.array([[x,y]]))[0].tolist(),'model_collision':blocked,'under_mask':mask.covers(pt)})
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
        'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':5464},
        'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
        'replacement_geometry':mesh.wgs(mask),'collision_geometry':mesh.wgs(collision),
        'overviewBearing':10,'overviewPitch':55,'overviewZoom':20.07,'maxDistance':680,'lod_switch_in_m':630,'lod_switch_out_m':830,
        'placement':{'status':'estimated','note':'由真实道路交叉点、2012年路口照、181号楼地图标注和可分辨的蝶形屋面共同确定西南角一栋。楼体尺度、窗扇和后翼按比例估计。'},
        'navigation':{'listed':False,'status':'从复兴中路、陕西南路路口向东北看折角窗、山花和端烟囱。'},
        'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(contract[k],k,collision=k=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True);write(args.out/'final-placement-contract.json',contract)
    report={'id':model,'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),'source_sha256':sha(source_path),
        'contract_sha256':sha(args.out/'final-placement-contract.json'),'assets':assets,'group':group,
        'source_records':{role:{'old_area_m2':g.area,'remaining_m2':g.difference(mask).area,'old_top_m':float(decoded[role][0][:,:,2].max()),'other_triangles_gap_m':retained[role].distance(mask),'assignment':decoded[role][2]}for role,g in originals.items()},
        'collision_m2':collision.area,'display_m2':profile.area,'mask_m2':mask.area,'ground_points':probes,
        'other_group_owners':{i:{'gap_m':mesh.footprints[i].distance(mask),'removed_m2':mesh.footprints[i].intersection(mask).area}for i in group['feature_local_ids']if i!=5464},
        'neighboring_residences':{i:{'gap_m':g.distance(mask),'lost_m2':g.intersection(mask).area}for i,g in protected.items()},
        'osm':{'sha256':vector['sha256'],'feature':aggregate['id'],'components':len(components),'target_component':9,'old_area_m2':target.area,'remaining_m2':target.difference(mask).area,'other_components':len(components)-1}}
    write(args.out/'placement-geometry.json',report)
    print('corner house',report['osm'],[(r,v['other_triangles_gap_m'])for r,v in report['source_records'].items()])
