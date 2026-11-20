"""Intersect the actual OpenFreeMap building polygons with the staged 722 model and retained neighbors."""
from pathlib import Path
import argparse,hashlib,json,math
import mapbox_vector_tile
import numpy as np
from shapely import transform
from shapely.geometry import shape
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('pbf',type=Path);args=ap.parse_args()
    data=args.pbf.read_bytes();url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13719/6694.pbf'
    digest=hashlib.sha256(data).hexdigest()
    source=json.loads((PROJECT/'source/precise/jingan-jewish-club/footprint-review.json').read_bytes())
    native=json.loads((HERE/'final-placement-contract.json').read_bytes());cut=shape(native['replacement_geometry'])
    layer=mapbox_vector_tile.decode(data,default_options={'y_coord_down':True})['building']
    extent=layer['extent'];lon,lat=native['lng'],native['lat'];k=6371008.8*math.cos(math.radians(lat))
    def tile_xy(t):
        east=(13719+t[:,0]/extent)/16384*2*math.pi-math.pi
        north=math.pi*(1-2*(6694+t[:,1]/extent)/16384)
        return np.column_stack((east-math.radians(lon),north-math.asinh(math.tan(math.radians(lat)))))*k
    def wgs_xy(t):
        return np.column_stack((np.radians(t[:,0]-lon),np.arcsinh(np.tan(np.radians(t[:,1])))-math.asinh(math.tan(math.radians(lat)))))*k
    geometry=unary_union([transform(shape(f['geometry']),tile_xy) for f in layer['features']])
    clip=transform(cut,wgs_xy);retained=geometry.difference(clip)
    others=[]
    for row in source['nearby']:
        fp=transform(shape(row['geometry']),wgs_xy)
        before=geometry.intersection(fp).area;after=retained.intersection(fp).area
        assert abs(before-after)<.001,(row['local_id'],before,after)
        others.append({'id':row['local_id'],'before_m2':before,'after_m2':after,'independent_clearance_m':clip.distance(fp)})
    out={'source_url':url,'actual_pbf_bytes':len(data),'actual_pbf_sha256':digest,'mapbox_features':len(layer['features']),'tile_geometry_removed_m2':clip.intersection(geometry).area,'unrelated_original_features':others,'contract_sha256':hashlib.sha256((HERE/'final-placement-contract.json').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/'fallback-geometry.json').write_text(json.dumps(out,indent=2)+'\n')
    print(len(others),min(x['independent_clearance_m']for x in others),out['tile_geometry_removed_m2'])
if __name__=='__main__':main()
