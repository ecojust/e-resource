"""Measure the front roof's clearance over the first sloping verge on the southern gable."""
import argparse,json,sys
from pathlib import Path
import numpy as np

here=Path(__file__).resolve()
project=next(p for p in here.parents
             if (p/'tools/verify_editable_model.py').is_file())
sys.path.insert(0,str(project/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def measure(mesh,layout,scale):
    scene=SerialScene(mesh)
    wing=json.loads(layout.read_bytes())['wings']['right']
    x,z=wing['verge_start']
    def wall_top(x0):
        if x0<=x:return z
        k=(x0-x)/(wing['ridge'][0]-x)
        return z+k*(wing['ridge'][1]-z)
    rows=[]
    for dx in (-.32,-.10,0,.10,.32,.65):
        a=x+dx
        b=wing['y']+.067
        hit=scene.ray(np.array([a*scale,b*scale,19.]),np.array([0.,0.,-1.]),35.)
        high=hit['point_enu_m'][2] if hit else None
        wall=wall_top(a)*scale
        rows.append(dict(author_x=a,author_depth=b,expected_wall_top_m=wall,roof_material=hit['material'] if hit else None,
                         observed_roof_upper_z_m=high,roof_above_wall_m=high-wall if high else None))
    return dict(mesh=scene.asset,scale=scale,rights='Measured on the authored geometry; no third-party imagery is included.',
                method='Vertical first intersections .067 local units inside the west-facing south gable. Wall elevations use the photographed, reprojected verge start and ridge. Roofing nominal top is .025 author units above the gable and its thickness is .13.',
                rows=rows)
if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('mesh',type=Path);c.add_argument('layout',type=Path);c.add_argument('output',type=Path);c.add_argument('--scale',type=float,default=.683);a=c.parse_args()
    r=measure(a.mesh,a.layout,a.scale);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print([round(v['roof_above_wall_m'],5) for v in r['rows']])
