"""Check the public overview camera against surrounding buildings and 343's retained roof."""
import argparse
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, shape

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('feature_table', type=Path)
args = parser.parse_args()
audit = Path(__file__).resolve().parent
project = audit.parents[2]
contract_file = audit / 'final-placement-contract.json'
contract = json.loads(contract_file.read_bytes())
source = json.loads((project / 'source/precise' / contract['id'] / 'footprint-review.json').read_bytes())
feature_sha = hashlib.sha256(args.feature_table.read_bytes()).hexdigest()
assert feature_sha == next(r['sha256'] for r in source['frozen_bindings'] if r['repository_path'].endswith('feature-table.json.gz'))
with gzip.open(args.feature_table) as f:
    features = json.load(f)['features']

screens = [{'width':1280,'height':800,'insets':{'left':322,'right':65,'top':138,'bottom':184}},
           {'width':390,'height':844,'insets':{'left':16,'right':65,'top':168,'bottom':210}}]
script = """import fs from 'node:fs';import {candidateOverviewCamera} from './src/candidate-overview-camera.js';
const {contract,screens}=JSON.parse(fs.readFileSync(0));
console.log(JSON.stringify(screens.map(s=>candidateOverviewCamera({...contract,city_integration:true},s))));"""
cameras = json.loads(subprocess.check_output(['node','--input-type=module','-e',script], cwd=project,
                   input=json.dumps({'contract':contract,'screens':screens}).encode()))
lng,lat = contract['lng'],contract['lat']
heading = math.radians(contract['heading'])
k = 6371008.8 * math.cos(math.radians(lat))
phi = np.arcsinh(np.tan(np.radians(lat)))
rotation = np.array([[math.cos(heading),-math.sin(heading)],[math.sin(heading),math.cos(heading)]])

def project_local(coords):
    east = np.radians(coords[:,0]-lng)*k
    north = (np.arcsinh(np.tan(np.radians(coords[:,1])))-phi)*k
    return np.column_stack((east,north)) @ rotation.T

anchor = Point(lng,lat)
obstacles = [(f['localId'],f['height'] or 0,shapely.transform(shape(f['geometry']),project_local))
             for f in features if f['localId'] != 343 and shape(f['geometry']).distance(anchor)<.0022]
residual = shape(source['source_outline']).difference(shape(contract['replacement_geometry']))
obstacles.append((343,source['source_height_m'],shapely.transform(residual,project_local)))
targets = [('central gable timbers',.4,-5.92,9.53),('southeast gable',8.7,-9.66,8.09),
           ('five garden openings',-2.13,-12.0,2.22),('fifth opening',4.15,-12.0,2.22),
           ('west round return',-12.02,-2.06,5.54),('roof chimney',-6.45,.75,10.12)]
observations = []
for screen,camera in zip(screens,cameras):
    bearing = math.radians(camera['bearing'])
    pitch = math.radians(camera['pitch'])
    focal = screen['height']/(2*math.tan(math.radians(36.87)/2))
    distance = focal*2*math.pi*k/(512*2**camera['zoom'])
    sight = np.array([math.sin(bearing),math.cos(bearing)]) @ rotation.T
    eye = project_local(np.array([camera['center']]))[0]-sight*distance*math.sin(pitch)
    eye_z = camera['elevation']+distance*math.cos(pitch)
    blocked = {}
    for label,x,y,z in targets:
        ray = LineString([eye,[x,y]])
        for owner,height,polygon in obstacles:
            intersect = shapely.get_coordinates(ray.intersection(polygon))
            for point in intersect:
                ray_height = eye_z+(z-eye_z)*ray.project(Point(point),normalized=True)
                if ray_height < height-.1:
                    blocked.setdefault(label,[]).append(owner)
                    break
    assert not blocked, (screen,blocked)
    observations.append({'screen':screen,'camera':camera,'assumed_eye_enu_height_m':[*eye,eye_z],
                         'occluded_by_other_owners':blocked})
report = {'model':contract['id'],'targets':targets,'screens':observations,'bearing':contract['overviewBearing'],
          'pitch':contract['overviewPitch'],'height_table_sha256':feature_sha,
          'fitted_camera_module_sha256':hashlib.sha256((project/'src/candidate-overview-camera.js').read_bytes()).hexdigest(),
          'contract_sha256':hashlib.sha256(contract_file.read_bytes()).hexdigest(),
          'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'method':'Project six sightlines from each fitted camera through all intersecting retained roof outlines, including the preserved east portion of source 343 at the original source height.'}
(audit/'candidate-camera-sightlines.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'{len(targets)} clear sightlines on each of {len(screens)} screens')
