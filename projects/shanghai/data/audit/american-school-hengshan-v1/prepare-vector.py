"""Decode both complete OpenMapTiles building aggregates intersecting the school."""
import argparse
import hashlib
import json
from pathlib import Path

import mapbox_vector_tile
import numpy as np
import shapely
from shapely.geometry import mapping, shape

audit = Path(__file__).resolve().parent
project = audit.parents[2]
review = json.loads((project/'source/precise/xuhui-shanghai-american-school-main/footprint-review.json').read_bytes())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--tiles', required=True, type=Path, help='Directory containing vector-13718.pbf and vector-13719.pbf')
parser.add_argument('--out', required=True, type=Path)
args = parser.parse_args()
wing = shape(review['reconstructed_eastern_wing'])
sources = []
for tile in review['osm_fallback_tiles']:
    raw = (args.tiles/f"vector-{tile['x']}.pbf").read_bytes()
    assert len(raw) == tile['bytes'] and hashlib.sha256(raw).hexdigest() == tile['sha256']
    buildings = mapbox_vector_tile.decode(raw, default_options={'y_coord_down':True})['building']
    def wgs(points):
        east = (tile['x'] + points[:,0]/buildings['extent']) / 2**tile['z']
        north = (tile['y'] + points[:,1]/buildings['extent']) / 2**tile['z']
        return np.column_stack((east*360-180, np.degrees(np.arctan(np.sinh(np.pi*(1-2*north))))))
    overlapping = []
    for feature in buildings['features']:
        geo = shapely.transform(shape(feature['geometry']), wgs)
        if not geo.intersects(wing):
            continue
        overlapping.append({'type':'Feature','id':feature['id'],'properties':feature['properties'],'geometry':mapping(geo)})
    assert len(overlapping) == 1 and overlapping[0]['properties']['render_height'] == 5
    sources.append({'tile':tile,'features':overlapping})
args.out.write_text(json.dumps(sources, ensure_ascii=False, separators=(',',':'))+'\n')
