"""Read the delivered mesh against the multi-date roof controls and public photographs."""
from pathlib import Path
import argparse,json,sys
import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def measure(path):
    mesh=SerialScene(path)
    roof_tests=[]
    for y in [1.9,6.0,13.0,22.5]:
        # This estimated axis and its plan-error allowance come from the dated aerial
        # register. Locate the highest surface independently in the delivered mesh.
        expected_x=8+(5.5-8)*y/24
        section=[]
        for x in np.arange(expected_x-3.25,expected_x+3.26,.125):
            hit=mesh.ray([x,y,17],[0,0,-1],28)
            if hit:
                section.append({'x':round(float(x),3),'z':hit['point_enu_m'][2],'material':hit['material']})
        peak=max(section,key=lambda r:r['z'])
        okay=abs(peak['x']-expected_x)<1.65 and 8.6<peak['z']<9.7 and 'ridge' in peak['material']
        roof_tests.append({'station_y':y,'aerial_axis_expected_x':round(expected_x,3),'observed_highest':peak,'observed_points':len(section),'pass':okay})
    footprint_tests=[]
    for name,x,y,lo,hi,mat in [
        ('314 north roof outer plane',1.6,13.4,6.7,8.6,'weathered clay tile'),
        ('314 south roof outer plane',13.3,14.5,6.4,8.0,'weathered clay tile'),
        ('310 west roof interior',18.7,17.7,7.9,9.5,'weathered clay tile'),
        ('310 east roof interior',27.1,17.4,7.9,9.5,'weathered clay tile'),
        ('northwest gateway passage is open',-.74,.62,-.09,.05,'aged coping'),
        ('southeast gateway passage is open',16.35,.64,-.09,.05,'aged coping'),
        ('310 entrance is open between its piers',23.35,2.6,-.06,.04,'aged coping'),
        ('310 narrow passage before inner gate',22.98,6.3,-.06,.04,'aged coping')]:
        # Passage clearance is measured below each spanning lintel.
        origin_height=2.4 if 'open' in name or 'passage' in name else 17.
        hit=mesh.ray([x,y,origin_height],[0,0,-1],28)
        okay=bool(hit and lo<=hit['point_enu_m'][2]<=hi and mat in hit['material'])
        footprint_tests.append({'feature':name,'xy':[x,y],'ray_origin_height':origin_height,'expected_elevation_m':[lo,hi],'material_expected':mat,'first_surface':hit,'pass':okay})
    return {'mesh':mesh.asset,'reference_files':['placement-identity.json','streetside-triangulation.json','registered-houses-and-photographs.json'],'ridge_sections':roof_tests,'roofs_and_openings':footprint_tests,'passed':sum(int(r['pass']) for r in roof_tests+footprint_tests),'count':len(roof_tests+footprint_tests)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();report=measure(args.mesh);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(report['passed'],report['count'],[r for r in report['ridge_sections']+report['roofs_and_openings'] if not r['pass']])
