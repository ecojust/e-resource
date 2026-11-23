"""Shared 313 Xiangyang Road court-facade and footprint coordinates (metres)."""
import json
from pathlib import Path

def load(path=None):
    return json.loads(Path(path or Path(__file__).with_name('3304-local-footprint.json')).read_bytes())

def facade_point(case,x,y,z,plan=None):
    key={'1':'case1','2':'case2'}.get(str(case),str(case))
    transform=(plan or load())['facade_frames'][key]['local_to_ENU']
    return tuple(sum(a*b for a,b in zip(row,(x,y,z,1))) for row in transform[:3])

def ground_ring(plan=None):
    return [tuple(p['ground_EN_m']) for p in (plan or load())['vertices']]

def roof_ring(plan=None):
    return [tuple(p['roof_registered_EN_m']) for p in (plan or load())['vertices']]
