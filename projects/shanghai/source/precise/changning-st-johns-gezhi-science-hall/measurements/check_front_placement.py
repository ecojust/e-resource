"""Count the centres of actual author-space triangles lying inside the measured west-campus original science building."""
import hashlib,argparse,json,runpy,math
from pathlib import Path
import numpy as np
from shapely import contains_xy
from shapely.geometry import shape
HERE=Path(__file__).resolve().parent
REVIEW=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
def check(path):
    d=json.loads((HERE/'science-hall-parcel.json').read_bytes());ring=shape(d['full_source_polygon']);tri,_,_,_=runpy.run_path(str(REVIEW))['load_triangles'](path);p=tri.mean(axis=1);a=math.radians(160.52);u=np.array([math.sin(a),math.cos(a)]);v=np.array([-math.cos(a),math.sin(a)]);ll=np.array([121.4134394,31.2278442]);axes=[111320*math.cos(math.radians(ll[1])),110860];xy=(p[:,0,None]+19.97)*u+p[:,1,None]*v;wgs=ll+xy/axes
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(p),inside_city_2173=int(contains_xy(ring,wgs[:,0],wgs[:,1]).sum()),axis_true_bearing=160.52,west_corner_wgs84=ll.tolist(),west_corner_local_x_m=-19.97,source_uuid=d['city_source'])
if __name__=='__main__':
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('mesh',type=Path);q.add_argument('out',type=Path);args=q.parse_args();args.out.write_text(json.dumps(check(args.mesh),indent=2)+'\n')
