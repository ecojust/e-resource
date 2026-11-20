"""Preserve all independently valid native MVT polygons in object 64634100."""
from pathlib import Path
import argparse,hashlib,json
import mapbox_vector_tile
import numpy as np
import shapely as geo
from shapely.geometry import shape,mapping
arg=argparse.ArgumentParser(description=__doc__);arg.add_argument('pbf',type=Path);arg.add_argument('output',type=Path);args=arg.parse_args()
raw=args.pbf.read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert digest=='21ae0cc5b91bfb8c85d320d3d0295804e5af8d04fcca02fb316f3e5ef80449e2'
layer=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building'];extent=layer['extent'];feature,=[f for f in layer['features']if f['id']==64634100]
def wgs(p):
    return np.column_stack(((p[:,0]/extent+13719)/2**14*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/extent+6694)/2**14))))))
g=geo.transform(shape(feature['geometry']),wgs)
assert g.geom_type=='MultiPolygon' and len(g.geoms)==1813 and all(part.is_valid for part in g.geoms)
feature['geometry']=mapping(g)
args.output.write_text(json.dumps({'source':'https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6694.pbf','bytes':len(raw),'sha256':digest,'features':[feature]},separators=(',',':'))+'\n')
