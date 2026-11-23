"""Check source owner overlaps against actual near or far triangles in the authored GLB."""
import argparse,json,runpy,hashlib,math
from pathlib import Path
import numpy as np
from shapely.geometry import MultiPoint,Polygon
from shapely import contains_xy
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
def compare(path):
    ground=json.loads((HERE/'yen-hall-ground-control.json').read_bytes());az=math.radians(ground['positive_x_true_bearing']);lon,lat=ground['world_origin']
    def planar(pt):
        east=(pt[0]-lon)*111320*math.cos(math.radians(lat));north=(pt[1]-lat)*110860
        return east*math.sin(az)+north*math.cos(az),-east*math.cos(az)+north*math.sin(az)
    triangles=runpy.run_path(str(HELPER))['load_triangles'](path)[0];cent=triangles.mean(axis=1);hull=MultiPoint(triangles.reshape(-1,3)[:,:2]).convex_hull;rows={}
    for k,v in {'1435':ground['source_40'],**ground['other_owners']}.items():
        poly=Polygon([planar(q)for q in v['rings'][0]])
        rows[k]={'centroids_inside':int(np.sum(contains_xy(poly,cent[:,0],cent[:,1]))),'hull_overlap_m2':hull.intersection(poly).area,'gap_m':hull.distance(poly)}
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),faces=len(triangles),hull_area_m2=hull.area,campus_owners=rows)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('json_output',type=Path);a=cli.parse_args();a.json_output.write_text(json.dumps(compare(a.mesh),indent=2)+'\n')
