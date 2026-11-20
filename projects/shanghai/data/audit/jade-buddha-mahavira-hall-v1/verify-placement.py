"""Check the relocated hall in its present position, its original forecourt and seventeen neighboring owners."""
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

model = 'putuo-jade-buddha-mahavira-hall'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro', type=Path, required=True)
parser.add_argument('--vector', type=Path, required=True)
parser.add_argument('--manifest', type=Path, default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out', type=Path, default=audit)
args = parser.parse_args()


source_path = project/'source/precise'/model/'footprint-review.json'
source, vector, manifest = read(source_path), read(args.vector), read(args.manifest)
assert manifest['id'] == model and vector['sha256'] == '01127bf6cc584c8be8a8bd880b6178e8f8e52da9d7855a117fed0c8ec3a877ac'
owner = source['owner']
group, = source['near_tiles']
assert owner['feature_local_id'] == 979 and len(group['feature_local_ids']) == 18
with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp)
    for receipt in source['frozen_bindings']:
        suffix = receipt['repository_path'].split(owner['macro_id']+'/')[1]
        (work/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh = PlacementMeshes(project,work,source)
    assets,bounds,profile,low_faces = mesh.decode_model(args.manifest)
    # The raised terrace and stair base physically contact the ground. The
    # broad projecting eaves do not. Use all three delivered lower meshes.
    ground=low_faces
    collision=ground.buffer(.035,join_style='mitre').simplify(.018,preserve_topology=True)
    assert ground.difference(collision).area < .003
    decoded=mesh.decode_group(group,979)
    sources={role:mesh.project_faces(v[0]) for role,v in decoded.items()}
    retained={role:mesh.project_faces(v[1]) for role,v in decoded.items()}
    original=mesh.footprints[979]
    aggregate, = vector['features']
    assert aggregate['id'] == 117811070 and aggregate['properties']['render_height']==5
    polygons=list(geo.transform(shape(aggregate['geometry']),mesh.to_xy).geoms)
    assert len(polygons)==755
    target,=[part for part in polygons if part.intersection(original).area>670]
    protected={i:mesh.footprints[int(i)] for i in source['retained_hall_features']}
    contained=[profile,original,target,*sources.values()]
    mask=geo.union_all(contained).buffer(.065,join_style='mitre').simplify(.022,preserve_topology=True)
    assert all(g.difference(mask).area < .0001 for g in contained)
    assert all(g.distance(mask)>.4 for g in retained.values())
    assert all(g.distance(mask)>.4 for g in protected.values())
    assert all(g.intersection(mask).area==0 for g in polygons if not g.equals(target))
    peers=sorted((g.distance(mask),i) for i,g in mesh.footprints.items() if i!=979)
    assert peers[0][0]>.4,peers[:4]
    probes=[]
    for label,x,y,blocked in [('inside the main hall',0,0,True),('hall terrace',8,-8.15,True),
                              ('front steps near threshold',0,-8.75,True),('front steps lower tread',0,-10.55,True),
                              ('free under east eave',13.76,0,False),('free under west eave',-13.76,0,False),
                              ('forecourt beyond the flight',0,-12,False),('former hall position',0,-30,False),
                              ('east side path',15.6,0,False),('north rear path',0,12,False)]:
        point=Point(x,y)
        assert collision.covers(point)==blocked,(label,collision.covers(point),collision.distance(point))
        probes.append({'label':label,'point':mesh.to_wgs(np.array([[x,y]]))[0].tolist(),
                       'model_collision':blocked,'under_mask':mask.covers(point)})
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':979},
              'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':mesh.wgs(mask),'collision_geometry':mesh.wgs(collision),
              'overviewBearing':-31.5,'overviewPitch':49,'overviewZoom':19.25,
              'maxDistance':470,'lod_switch_in_m':600,'lod_switch_out_m':780,
              'placement':{'status':'estimated','note':'按2016发布的平移前影像、2017工程俯视照、2019／2021年平移后航片与寺方导览确定今日大雄宝殿，殿前旧址保留为空庭。屋高、进深和被遮挡的侧背根据外观估算。'},
              'navigation':{'listed':False,'status':'从南前庭看正面四块匾额、格扇门和两层灰瓦飞檐。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ('replacement_geometry','collision_geometry'):
        checked_geometry(contract[k],k,collision=k=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    other={k:{'area_m2':g.area,'unintended_loss_m2':g.intersection(mask).area,'gap_m':g.distance(mask)}
           for k,g in mesh.footprints.items() if k in set(group['feature_local_ids'])-{979}}
    report={'id':model,'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),
            'source_sha256':sha(source_path),'contract_sha256':sha(args.out/'final-placement-contract.json'),
            'group':group,'assets':assets,'source_records':{role:{'area_m2':g.area,'residual_m2':g.difference(mask).area,
            'original_top_m':float(decoded[role][0][:,:,2].max()),'other_triangles_gap_m':retained[role].distance(mask),
            'assignment':decoded[role][2]} for role,g in sources.items()},'other_group_owners':other,
            'model_area_m2':profile.area,'all_lower_faces_area_m2':low_faces.area,'collision_area_m2':collision.area,
            'collision_derivation':'union of delivered lower surfaces and treads from raw, web and LOD','replacement_area_m2':mask.area,'ground_points':probes,
            'osm':{'sha256':vector['sha256'],'source':aggregate['id'],'components':len(polygons),
            'hall_component':537,'hall_area_m2':target.area,'remaining_hall_m2':target.difference(mask).area,
            'unaffected_components':len(polygons)-1},'preserved_temple_neighbors':{
            str(i):{'area_m2':g.area,'removed_m2':g.intersection(mask).area,'gap_m':g.distance(mask)}for i,g in protected.items()},
            'old_site':{'passable':True,'within_replacement':mask.covers(Point(0,-30))}}
    assert not report['old_site']['within_replacement']
    write(args.out/'placement-geometry.json',report)
    print(model,report['osm'],[(r,v['other_triangles_gap_m'])for r,v in report['source_records'].items()])
