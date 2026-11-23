"""Reconstruct facade heights from the original full-panorama row, camera tilt and range."""
import argparse
import hashlib
import json
from math import radians, tan
from pathlib import Path
from statistics import median

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('project',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args();audit=a.project/'data/audit/arnhold-building-southwest-corner-v1'
survey_path=audit/'preflight/vertical-survey.json'
survey=json.loads(survey_path.read_bytes())
input_images=json.loads((audit/'preflight/pano-z4-sources.json').read_bytes())
records=[]
for shot in survey['sightlines']:
    rows=shot['raw_y'][1:]
    measures={}
    for (feature,expected),y in zip(shot['height'].items(),rows,strict=True):
        corrected_angle=(1024-y)*180/2048+shot['horizon_offset_deg']
        height=shot['eye']+shot['range_m']*tan(radians(corrected_angle))
        assert abs(height-expected)<.001,(feature,height,expected)
        measures[feature]=round(height,3)
    capture=input_images[str(shot['crop'])]
    assert capture['id']==shot['id']
    records.append({'station':shot['id'],'date':shot['date'],'crop':shot['crop'],'distance_m':shot['range_m'],'heights_m':measures})
summary={k:round(median(r['heights_m'][k] for r in records),3) for k in survey['meters']}
assert all(abs(summary[k]-v)<.0011 for k,v in survey['meters'].items()) and len(records)==4
a.output.write_text(json.dumps({'survey_sha256':hashlib.sha256(survey_path.read_bytes()).hexdigest(),'cameras':records,'median_height_m':summary},ensure_ascii=False,indent=2)+'\n')
