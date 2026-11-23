"""Derive only the two relief regions from the triangles that actually intersected."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from shapely.geometry import MultiPoint


def profile(filepath):
    d=json.loads(filepath.read_bytes());bands={}
    for key,name in [('base','Inferred window reveals'),('eave','Inferred neutral plaster')]:
        rows=[r for r in d['segments']if r['old_material']==name]
        assert rows and all('east wall facing adjoining plot' in r['part']for r in rows)
        old=np.array([p for r in rows for p in r['old']])
        contact=np.array([p for r in rows for p in r['intersection']])
        bands[key]={'z_min':float(contact[:,2].min()),'z_max':float(contact[:,2].max()),
                    'old_roof_or_reveal_outline_xy':list(MultiPoint(old[:,:2]).convex_hull.exterior.coords),
                    'original_contact_pairs':len(rows),'contact_xyz_bounds':[contact.min(0).tolist(),contact.max(0).tolist()]}
    return {'datum':'Metres in No. 2 survey frame. The convex hull uses only the original faces that contacted this wall. Input comes from exact old/new intersections.',
            'input_sha256':hashlib.sha256(filepath.read_bytes()).hexdigest(),'old_city_tile_sha256':d['published_tile_sha256'],
            'xy_clearance_m':.020,'z_clearance_m':.020,'relief_bands':bands}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('seams',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();a.output.write_text(json.dumps(profile(a.seams),indent=2)+'\n')
