"""Measure Nankin Hotel balcony projections in the two street charts and in each shipped GLB."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import runpy
from statistics import median
import subprocess
import tempfile

def read(p):
    return json.loads(p.read_bytes())

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('project',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
project=args.project.resolve()
model='huangpu-nankin-hotel-shanxi-front'
source=project/'source/precise'/model/'source'
audit=project/'data/audit/nankin-hotel-shanxi-front-v1'
assets=project/'assets/models/candidates'/model
dimensions=read(source/'dimensions.json')
survey=read(source/'balcony-depths.json')
station=read(source/'balcony-measurements.json')
cameras={cam['camera']:cam for cam in station['sources']}
camera_ids={cam['camera']:cam['id'] for cam in survey['sources']}
observed=defaultdict(list)
samples=[]
for row in survey['samples']:
    ray_camera=cameras[camera_ids[row['camera']]]
    wall_z=26-row['wall_joint_y']/30
    for point in row['measures']:
        far_z=26-point['front_y']/30
        depth=ray_camera['west']*(1-(wall_z-2.32)/(far_z-2.32))
        assert abs(depth-point['relative_depth_m'])<.001
        observed[point['role']].append(depth)
        samples.append({'camera':ray_camera['camera'],'chainage_m':row['bay_chainage_m'],'role':point['role'],'wall_px':row['wall_joint_y'],'front_px':point['front_y'],'offset_m':round(depth,4)})
depths={name:round(median(values),3) for name,values in observed.items()}
for name,depth in depths.items():
    assert abs(depth-survey['relative_depth_m'][name]['median'])<=.001
manifest=read(assets/'manifest.json')
entries=read(audit/'preflight/entry-design-validation.json')['variants']
original=read(audit/'native-and-web-surface-checks.json')['models']
check=runpy.run_path(str(audit/'verify-export.py'))['check']
decoder=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
variants={}
with tempfile.TemporaryDirectory() as temp:
    for role in ('raw','full','lod'):
        asset=manifest['assets'][role]
        file=assets/asset['file']
        assert sha256(file.read_bytes()).hexdigest()==asset['sha256']
        decoded=file
        if role!='raw':
            decoded=Path(temp)/(role+'.glb')
            subprocess.run(['node',decoder,file,decoded,project/'vendor/meshopt_decoder.module.js'],check=True)
        result=check(decoded,dimensions,entries[int(role=='lod')]['rays'])
        assert result['triangles']==asset['triangles'] and len(result['tests'])==len(original[role]['tests'])
        for a,b in zip(result['tests'],original[role]['tests'],strict=True):
            assert a['part']==b['part'] and a['material']==b['material']
            assert max(abs(u-v) for u,v in zip(a['point'],b['point'],strict=True))<1e-6
        balcony=[t for t in result['tests'] if t['part'].endswith('projecting masonry')]
        assert len(balcony)==36 and len(dimensions['bay_axes'])==6
        measured=[]
        for level,rows in [('L4',balcony[:18]),('L5',balcony[18:])]:
            for i,x in enumerate(dimensions['bay_axes']):
                left,tip,right=rows[i*3:i*3+3]
                assert all(t['part'].startswith(level) for t in [left,tip,right])
                measured.append({'level':level,'axis_m':x,'sample_offsets_m':[round(t['point'][1],4) for t in (left,tip,right)]})
        variants[role]={'triangles':asset['triangles'],'sha256':asset['sha256'],'ray_checks':len(result['tests']),'twelve_balconies':measured}
result={'building':model,'photo_recipe':{'height_m':2.32,'wall_distance_m':{k:cameras[v]['west'] for k,v in camera_ids.items()},'photo_ids':[r['sha256'] for r in survey['sources']]},'measured_photo_samples':samples,'median_m':depths,'models':variants}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
