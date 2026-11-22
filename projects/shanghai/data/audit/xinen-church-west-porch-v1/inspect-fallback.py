"""Decode the real map fallback and record all components crossing the gate, courtyard and original cut."""
from pathlib import Path
from argparse import ArgumentParser
import math,gzip,sys,hashlib,json
import numpy as np
import shapely as geo
from shapely.geometry import shape,box
import mapbox_vector_tile
HERE=Path(__file__).resolve().parent;PROJECT=Path(__import__('os').environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[2]));sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
ID='jingan-xinen-church-west-porch'
def main():
    p=ArgumentParser(description=__doc__)
    for k in ('tile','contract','work','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();review=read(Path(__import__('os').environ.get('XINEN_FOOTPRINT',PROJECT/'source/precise'/ID/'footprint-review.json')))
    site=PlacementMeshes(PROJECT,a.work,review);contract=read(a.contract);assert contract['id']==ID
    cut=geo.transform(shape(contract['replacement_geometry']),site.to_xy);corr=box(-4.21,1.58,4.21,4.75)
    layer=mapbox_vector_tile.decode(a.tile.read_bytes(),default_options={'y_coord_down':True})['building']
    def xy(uv):
        x=13718+uv[:,0]/layer['extent'];y=6694+uv[:,1]/layer['extent'];return site.to_xy(np.c_[x/16384*360-180,np.degrees(np.arctan(np.sinh(np.pi*(1-2*y/16384))))])
    total=0;changed=[];near=[]
    for f in layer['features']:
        group=geo.transform(shape(f['geometry']),xy);parts=geo.get_parts(group);total+=len(parts)
        for i,part in enumerate(parts):
            if part.distance(cut)>38:continue
            before=part.intersection(cut);after=part.difference(cut)
            if before.area>.000005:
                changed.append(dict(feature=f['id'],component=i,group_components=len(parts),old_area_m2=part.area,removed_m2=before.area,retained_m2=after.area,original_walk_overlap_m2=part.intersection(corr).area,after_walk_overlap_m2=after.intersection(corr).area))
            near.append(dict(id=f['id'],component=i,outline=site.wgs(part),height=f['properties'].get('render_height')or f['properties'].get('height')or 12,source_clearance_to_gate_m=part.distance(cut),stage_retained_area_m2=after.area))
    assert sha(a.tile)=='1fdad607f7b21b88e0ad7de7768cd646aba6c88aca481544ba3409575d5e2bb2' and total>500
    r=dict(passed=True,contract_sha256=sha(a.contract),url='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13718/6694.pbf',tile_sha256=sha(a.tile),original_building_features=len(layer['features']),original_parts=total,changed_parts=changed,untouched_parts=total-len(changed),nearby=near)
    write(a.out,r);print(total,changed,flush=True)
if __name__=='__main__':main()
