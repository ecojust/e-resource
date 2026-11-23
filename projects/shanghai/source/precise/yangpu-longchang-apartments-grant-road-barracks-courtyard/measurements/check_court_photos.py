"""Fit two historical images and compare the first mesh surface at marked architectural details."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
LAYOUT = json.loads((HERE.parent/'source/courtyard-layout.json').read_bytes())
F08 = json.loads((HERE/'court-short-end-photo-station.json').read_bytes())
F17 = json.loads((HERE/'stair-photo-points.json').read_bytes())

def camera(parameters):
    return np.r_[parameters,1].reshape(3,4)

def pixels(matrix,xyz):
    h = np.c_[xyz,np.ones(len(xyz))] @ matrix.T
    return h[:,:2]/h[:,2:]

def stair_station():
    xyz=np.array([v[0] for v in F17['calibration']])
    uv=np.array([v[1] for v in F17['calibration']])
    start=[-60,65,0,503,10,14,-130,630,.04,.04,-.01]
    fit=least_squares(lambda x:(pixels(camera(x),xyz)-uv).ravel(),start)
    projection=camera(fit.x)
    independent=[]
    for side,bay,xy in F17['independent_edges']:
        base=[bay,0] if side=='left' else [0,bay]
        z=least_squares(lambda v:pixels(projection,np.array([[*base,v[0]]]))[0]-xy,[1.5]).x[0]
        independent.append({'side':side,'bay':bay,'native_uv':xy,'recovered_height_storeys':round(z,5)})
    heights=np.array([v['recovered_height_storeys'] for v in independent])
    rise={'left_side':[abs(heights[1]-heights[0]),abs(heights[7]-heights[6])],
          'front_face':[abs(heights[4]-heights[3]),abs(heights[9]-heights[8])]}
    # Register the observed two tower planes using the roof footprint and the higher front landing.
    corners=np.array(LAYOUT['court_corners'])
    tangent=corners[1]-corners[0]
    tangent/=np.linalg.norm(tangent)
    inward=np.array([-tangent[1],tangent[0]])
    r=LAYOUT['stairs']['street']
    local_to_model=np.eye(4)
    local_to_model[:2,3]=corners[0]+tangent*(r['along']+r['width']/2)+inward*r['projection']
    local_to_model[2,3]=1.75*LAYOUT['storey_pitch']-.19
    local_to_model[:2,0]=-inward*r['projection']/3
    local_to_model[:2,1]=-tangent*r['width']/3
    local_to_model[2,2]=LAYOUT['storey_pitch']
    world=projection @ np.linalg.inv(local_to_model)
    return world,{'median_control_residual_px':float(np.median(np.linalg.norm(pixels(projection,xyz)-uv,axis=1))),
                  'rise_in_storeys':rise,'independent_edge_readings':independent,
                  'scope':'局部梯塔的柱格比例检查，前后两塔相似，整院站位属展示配准。'}

def test_scene(path):
    scene=SerialScene(path)
    back=np.array(LAYOUT['court_corners'][3]);end=np.array(LAYOUT['court_corners'][0])
    tangent=(end-back)/np.linalg.norm(end-back)
    normal=np.array([-tangent[1],tangent[0]])
    stair,station=stair_station()
    samples=[]
    def test(tag,cam,at,uv,component,allowed,valid):
        matrix=np.asarray(cam);eye=np.linalg.solve(matrix[:,:3],-matrix[:,3])
        ray=np.linalg.solve(matrix[:,:3],[*uv,1])
        if (matrix@np.r_[at,1])[2]<0:ray=-ray
        hit=scene.ray(eye,ray,150.)
        matched=bool(hit and hit['material'] in allowed and valid(np.array(hit['point_enu_m'])))
        samples.append({'photo':tag,'native_uv':uv,'feature':component,'match':matched,'first_hit':hit})

    wash='Court | washed aggregate';cope='Court | grey coping';slab='Court | floor concrete';h=LAYOUT['storey_pitch']
    gallery=[[(327,380),(479,379),(635,379),(727,375)],[(292,299),(353,308),(554,308),(602,305),(728,292)],
             [(286,233),(363,227),(500,229),(589,229),(650,225),(740,222)],[(264,147),(295,150),(369,157),(512,156),(636,148),(740,151)]]
    toward=[5,22,9]
    for level,points in enumerate(gallery,1):
        for uv in points:
            test('F08',F08['camera_P'],toward,uv,f'short-wing parapet {level}',[wash,cope],
                 lambda p:abs((p[:2]-back)@normal)<.35 and level*h-.12<=p[2]<=level*h+1.12)
    for uv in [(336,63),(476,65),(682,62)]:
        test('F08',F08['camera_P'],toward,uv,'short-wing roof rim',[cope],lambda p:abs((p[:2]-back)@normal)<.35 and 5*h<=p[2]<=5*h+1.)
    for uv in [(196,675),(321,623),(454,622),(717,662)]:
        test('F08',F08['camera_P'],toward,uv,'courtyard paving',[slab],lambda p:p[2]<.04)
    reg=LAYOUT['stairs']['street'];a=np.array(LAYOUT['court_corners'][0]);t=np.array(LAYOUT['court_corners'][1])-a;t/=np.linalg.norm(t);n=np.array([-t[1],t[0]])
    def on_tower(p):
        v=p[:2]-a
        return abs(v@t-reg['along'])<reg['width']/2+.5 and -.45<v@n<reg['projection']+.55
    groups={'landing':[(458,201),(483,222),(534,205),(521,199),(438,332),(470,349),(534,348),(527,480)],
            'diagonal parapet and turn':[(632,281),(645,271),(601,231),(583,365),(598,385),(594,518),(395,157),(395,151),(398,308),(399,312),(355,156),(356,421)],
            'cast frieze':[(654,99),(470,108),(514,89),(569,117),(655,137)],
            'pier':[(432,205),(504,450),(570,166),(626,170),(635,297)]}
    for feature,points in groups.items():
        for uv in points:test('F17',stair,[27,15,13],uv,feature,[wash,cope,slab],on_tower)
    return {'mesh':scene.asset,'F17_local_fit':station,'results':samples,
            'counts':{k:{'matched':sum(r['match'] for r in samples if r['photo']==k),'total':sum(r['photo']==k for r in samples)} for k in ['F08','F17']}}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path);cli.add_argument('meshes',nargs='+',type=Path)
    opts=cli.parse_args()
    results=[test_scene(p) for p in opts.meshes]
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print([r['counts'] for r in results])
