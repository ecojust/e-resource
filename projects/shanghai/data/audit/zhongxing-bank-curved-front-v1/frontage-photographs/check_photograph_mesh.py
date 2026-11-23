"""Compare measured street-photo pixels with the actual three delivered model surfaces."""
import argparse
import hashlib
import json
import math
import runpy
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

parser = argparse.ArgumentParser()
parser.add_argument("--project", type=Path, required=True, help="projects/shanghai directory")
parser.add_argument("--registration", type=Path, required=True)
parser.add_argument("--decoded", type=Path, required=True, help="directory for independently decoded GLBs")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
project = args.project.resolve()
record = json.loads(args.registration.read_bytes())
fit = record["fit"]
landmark = "huangpu-zhongxing-bank-curved-front"
assets = project / "assets/models/candidates" / landmark
manifest = json.loads((assets / "manifest.json").read_bytes())["assets"]
reader = runpy.run_path(str(project / "data/audit/postal-office-v1/independent-glb-review-helpers.py"))
radius = record["arc_radius_m"]
width = record["working_pixels"]["width"]
height = record["working_pixels"]["height"]
focal = width * fit["focal_equiv_mm"] / 36
pp = np.array([(width-1)/2, (height-1)/2])
span = fit["spacing_m"]
levels = {
    "ground-contact": 0., "ground-aperture-sill": .70, "ground-aperture-head": 3.40, "base-cap": 4.48,
    "L2-sill": 4.67, "L2-head": 6.61, "L3-sill": 8.13, "L3-head": 10.07,
    "L4-sill": 11.59, "L4-head": 13.53, "L5-sill": 15.05, "L5-head": 16.99,
    "L6-sill": 19.24, "L6-head": 20.58,
}
def digest(path):
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()
def rotation(angles):
    yaw, pitch, roll = angles
    direction = [math.sin(yaw)*math.cos(pitch), math.cos(yaw)*math.cos(pitch), math.sin(pitch)]
    right = [math.cos(yaw), -math.sin(yaw), 0.]
    return Rotation.from_rotvec([0.,0.,roll]).as_matrix() @ np.array([right, np.cross(direction,right), direction])
def facade(arc,z):
    theta = arc/radius
    return np.array([radius*math.sin(theta), radius*(1-math.cos(theta)), z])
def project_points(parameters, points):
    xyz=(points-parameters[:3]) @ rotation(parameters[3:]).T
    return xyz[:,:2]/xyz[:,2,None]*focal+pp
def ray(parameters,uv):
    return rotation(parameters[3:]).T @ np.r_[(np.asarray(uv)-pp)/focal,1.]
free=np.r_[fit["camera_m"],np.radians(fit["yaw_pitch_roll_degrees"])]
features = list(levels)
actual=[]
world=[]
weights=[]
for key,z in levels.items():
    actual.extend(record['normalized_observations'][key]['working_px'])
    world.extend(facade(s,z) for s in [-span,0.,span])
    weights.extend([{'ground-contact':.4,'ground-aperture-sill':.65,'ground-aperture-head':.75,'base-cap':.7}.get(key,1.)]*3)
actual=np.array(actual)
world=np.array(world)
weights=np.array(weights)[:,None]
rigid=least_squares(lambda v:((project_points(v,world)-actual)*weights).ravel(),free,loss="soft_l1",f_scale=1.2,max_nfev=500).x
errors=np.linalg.norm(project_points(rigid,world)-actual,axis=1)
# Independent hand readings at clear areas of paired panes. These positions are
# neither projected from the model nor used in the 42-point station fit.
samples={
    'ground':[(342,459),(443,465),(543,465)],
    'L2':[(340,365),(363,365),(434,358),(464,360),(531,365),(559,366)],
    'L3':[(348,285),(369,283),(435,280),(465,277),(530,283),(553,290)],
    'L4':[(349,224),(375,219),(435,211),(464,210),(527,222),(548,223)],
    'L5':[(355,159),(375,155),(437,145),(464,146),(525,158),(544,161)],
    'L6':[(362,87),(378,83),(438,71),(463,70),(525,85),(542,86)]}
def photo_hits(scene,parameters):
    readings=[]
    for level,points in samples.items():
        for uv in points:
            contact=scene.ray(parameters[:3],ray(parameters,uv),length=55)
            readings.append({'level':level,'uv_840':uv,'hit':None if contact is None else contact['material']})
    return {'first_hits':readings,'surface_counts':dict(Counter(x['hit'] for x in readings))}
def probes(scene):
    tests=[]
    def shoot(s,z,expected):
        theta=s/radius
        normal=np.array([math.sin(theta),-math.cos(theta),0.])
        hit=scene.ray(facade(s,z)+2*normal,-normal,3.5)
        tests.append({'arc_m':round(s,4),'z_m':z,'expected':expected,'actual':None if hit is None else hit['material'],
                      'radial_depth_m':None if hit is None else round(2-hit['distance_m'],4)})
    for axis in [-span,0.,span]:
        shoot(axis+.41,1.90,'grey blue glazing')
        for z in [5.5,8.96,12.42,15.88,19.84]:
            for t in [-.68,.68]:
                shoot(axis+t+.11,z,'grey blue glazing')
            shoot(axis,z,'cream jointed facing')
    # Five samples on a single uninterrupted curved face. Compare to the chord
    # joining the two outer hits, as a flat wall could not pass this test.
    arc=[]
    for s in np.linspace(-6.1,6.1,5):
        normal=np.array([math.sin(s/radius),-math.cos(s/radius),0.])
        hit=scene.ray(facade(s,3.83)+2*normal,-normal,3.5)
        assert hit['material']=='warm ground stone'
        arc.append(np.asarray(hit['point_enu_m'][:2]))
    chord=(arc[0]+arc[-1])/2
    return {'rays':tests,'passes':sum(row['expected']==row['actual'] for row in tests),'count':len(tests),
            'plan_five_hits_xy_m':[v.tolist() for v in arc],'centre_to_endpoint_chord_m':float(np.linalg.norm(arc[2]-chord))}
roles={}
args.decoded.mkdir(parents=True,exist_ok=True)
for key in ['raw','full','lod']:
    asset=assets/manifest[key]['file']
    assert digest(asset)==manifest[key]['sha256']
    physical=asset
    if key!='raw':
        physical=args.decoded/(key+'.glb')
        subprocess.run(['node',str(project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'),str(asset),str(physical),str(project/'vendor/meshopt_decoder.module.js')],check=True,stdout=subprocess.DEVNULL)
    scene=reader['SerialScene'](physical)
    assert len(scene.tri)==manifest[key]['triangles']
    roles[key]={'file':asset.name,'sha256':digest(asset),'decoded_sha256':digest(physical),'triangles':len(scene.tri),
        'arc_and_three_paired_axes':probes(scene),'conditional_photo_station':photo_hits(scene,free),'fixed_model_station':photo_hits(scene,rigid)}
    del scene
results={'photo_sha256':record['photo_sha256'],'working_width':width,'aperture_readings':sum(map(len,samples.values())),
    'station_comparison':{'conditional_photo_height_fit_median_px':fit['median'],'conditional_photo_height_fit_max_px':fit['max'],
                          'fixed_mesh_levels_best_station_median_px':float(np.median(errors)),'fixed_mesh_levels_best_station_max_px':float(errors.max()),
                          'fixed_mesh_camera_m':rigid[:3].tolist(),'fixed_mesh_yaw_pitch_roll_deg':np.degrees(rigid[3:]).tolist(),
                          'fixed_mesh_median_by_level_px':{key:round(float(np.median(errors[i*3:i*3+3])),2) for i,key in enumerate(features)}},
    'model_and_conditional_photo_m':{k:{'model':v,'photo':round(fit['levels_m'][k],3),'signed_photo_minus_model':round(fit['levels_m'][k]-v,3)} for k,v in levels.items()},
    'roles':roles}
args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print([ (k,r['triangles'],r['arc_and_three_paired_axes']['passes'],r['fixed_model_station']['surface_counts']) for k,r in roles.items() ],results['station_comparison'])
