"""Check the delivered school office, open porches and thirteen adjacent owners."""
import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import LineString, Point, box, shape
from shapely.ops import polygonize

audit = Path(__file__).resolve().parent
project = audit.parents[2]
sys.path.insert(0, str(project / 'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, sha, write

model = 'jingan-huashan-american-school-office'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro', type=Path, required=True)
parser.add_argument('--vector', type=Path, required=True)
parser.add_argument('--manifest', type=Path, default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out', type=Path, default=audit)
args = parser.parse_args()


def wall_section(triangles, height):
    """Reconstruct solid wall and pier outlines at a pedestrian torso height."""
    z = triangles[:, :, 2]
    lines = []
    for triangle in triangles[(z.min(axis=1) < height) & (z.max(axis=1) > height)]:
        points = []
        for a,b in zip(triangle, np.roll(triangle, -1, axis=0)):
            if (a[2] < height) != (b[2] < height):
                t = (height-a[2])/(b[2]-a[2])
                points.append(a[:2] + t*(b[:2]-a[:2]))
        if len(points) == 2 and np.linalg.norm(points[0]-points[1]) > .00001:
            lines.append(LineString(np.round(points,4)))
    noded = geo.union_all(lines, grid_size=.001)
    return geo.union_all(list(polygonize(noded)))


source_path = project/'source/precise'/model/'footprint-review.json'
source, vector, manifest = read(source_path), read(args.vector), read(args.manifest)
assert manifest['id'] == model and vector['sha256'] == 'ef9df460f908f294d516f8753ac4366603662b592d4fb5bd2c214df51e6cf5e0'
owner = source['owner']
group, = source['near_tiles']
assert owner['feature_local_id'] == 3170 and len(group['feature_local_ids']) == 14
with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp)
    for receipt in source['frozen_bindings']:
        suffix = receipt['repository_path'].split(owner['macro_id']+'/')[1]
        (work/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh = PlacementMeshes(project,work,source)
    assets,bounds,profile,low_faces = mesh.decode_model(args.manifest)
    # Floor tiles at +0.23 and +0.31 m are traversable at both entrances.
    # Inside the closed room body the measured plinth fills the whole plan.
    # In the open porches union the two horizontal cuts, retaining the piers,
    # jambs and lower rails while permitting movement behind the columns.
    sections=[]
    for item in read(work/'delivered-decode.json'):
        vertices=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        local=vertices[:,:,[0,2,1]]*[1,-1,1]
        sections.extend(wall_section(local,z) for z in (.71,1.71))
    room = box(-14.55,-6,14.55,3.80)
    ground = geo.union_all([low_faces.intersection(room), *sections],grid_size=.001)
    collision = ground.buffer(.035, join_style='mitre').simplify(.025,preserve_topology=True)
    assert ground.difference(collision).area < .006
    decoded=mesh.decode_group(group,3170)
    sources={role:mesh.project_faces(v[0]) for role,v in decoded.items()}
    retained={role:mesh.project_faces(v[1]) for role,v in decoded.items()}
    original=mesh.footprints[3170]
    aggregate, = vector['features']
    assert aggregate['id'] == 147898520 and aggregate['properties']['render_height'] == 5
    polygons = list(geo.transform(shape(aggregate['geometry']),mesh.to_xy).geoms)
    target, = [g for g in polygons if g.intersection(original).area > 440]
    theater, = [g for g in polygons if g.intersection(mesh.footprints[3433]).area > 325]
    contained=[profile,original,target,*sources.values()]
    mask=geo.union_all(contained).buffer(.07,join_style='mitre').simplify(.035,preserve_topology=True)
    assert all(g.difference(mask).area < .0001 for g in contained)
    assert all(g.distance(mask)>4 for g in retained.values())
    assert theater.distance(mask)>4
    assert all(g.intersection(mask).area==0 for g in polygons if not g.equals(target))
    peers=sorted((v.distance(mask),i) for i,v in mesh.footprints.items() if i!=3170)
    assert peers[0][0]>4 and {3888,3433}<=set(i for d,i in peers[:4])
    probes=[]
    for label,x,y,blocked in [('office interior',0,0,True),('garden west pier',9.68,7.17,True),
                              ('garden central pier',.10,7.17,True),('terrace behind piers',2.7,5.55,False),
                              ('central opening between piers',2.7,7.1,False),
                              ('street porch inside the arch',0,-7.7,False),
                              ('street porch jamb',2.7,-8.91,True),
                              ('lawn',0,10,False),('gate approach',0,-12,False),
                              ('east side path',-17,0,False)]:
        point=Point(x,y)
        assert collision.covers(point)==blocked,(label,collision.covers(point),collision.distance(point))
        probes.append({'label':label,'point':mesh.to_wgs(np.array([[x,y]]))[0].tolist(),
                       'model_collision':blocked,'under_mask':mask.covers(point)})
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':3170},
              'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':mesh.wgs(mask),'collision_geometry':mesh.wgs(collision),
              'overviewBearing':-27.9,'overviewPitch':49,'overviewZoom':19.05,
              'maxDistance':470,'lod_switch_in_m':600,'lod_switch_out_m':780,
              'placement':{'status':'estimated','note':'按2018、2022、2024三期航片校正临街办公楼的檐口与露台位置。遮挡端部、进深和标高据外观估算。'},
              'navigation':{'listed':False,'status':'从院内草坪可看到办公楼两层柱廊和东部弧形露台。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ('replacement_geometry','collision_geometry'):
        checked_geometry(contract[k],k,collision=k=='collision_geometry')
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    other={k:{'area_m2':g.area,'unintended_loss_m2':g.intersection(mask).area,'gap_m':g.distance(mask)}
           for k,g in mesh.footprints.items() if k in set(group['feature_local_ids'])-{3170}}
    report={'id':model,'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),
            'source_sha256':sha(source_path),'contract_sha256':sha(args.out/'final-placement-contract.json'),
            'group':group,'assets':assets,'source_records':{role:{'area_m2':g.area,'residual_m2':g.difference(mask).area,
            'original_top_m':float(decoded[role][0][:,:,2].max()),'other_triangles_gap_m':retained[role].distance(mask),
            'assignment':decoded[role][2]} for role,g in sources.items()},'other_group_owners':other,
            'model_area_m2':profile.area,'all_lower_faces_area_m2':low_faces.area,'collision_area_m2':collision.area,
            'collision_section_heights_m':[.71,1.71],'replacement_area_m2':mask.area,'ground_points':probes,
            'osm':{'sha256':vector['sha256'],'source':aggregate['id'],'components':len(polygons),
            'office_area_m2':target.area,'remaining_office_m2':target.difference(mask).area,
            'theater_area_m2':theater.area,'theater_after_m2':theater.difference(mask).area,
            'theater_gap_m':theater.distance(mask),'unaffected_components':len(polygons)-1}}
    write(args.out/'placement-geometry.json',report)
    print(model,report['osm'],[(r,v['other_triangles_gap_m'])for r,v in report['source_records'].items()])
