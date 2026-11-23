"""Reproject the registered garden elevation and an independently fitted bay close-up."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
ROOT=next(p for p in Path(__file__).absolute().parents if (p/'tools/package_architectural_model.py').exists())
sys.path.insert(0,str(ROOT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def east():
    k=np.array([[463.98590676,0,301.04197323],[0,463.98590676,223.87783771],[0,0,1]])
    r=np.array([[.79330083,.60880409,-.00560027],[-.12534454,.15431474,-.98003863],[-.59578732,.77816742,.19872828]])
    center=np.array([9.39572795,-10.59699343,1.51167332])
    garden_to_photo=np.array([[0,1,0,-12.28],[-1,0,0,10.52],[0,0,1,0],[0,0,0,1]])
    return k@np.column_stack((r,-r@center))@garden_to_photo

def close():
    import math
    arc=[];center=np.array([-.0-4.335,-.093])
    for angle in np.linspace(-177,-33,4):
        arc.append(center+2.213*np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))]))
    xyz=[];uv=[]
    observations=[(1,.22,2.985,[164,267]),(1,-.22,2.985,[261,283]),(1,.22,.965,[155,469]),(1,-.22,.965,[267,464]),(0,-.22,2.985,[106,257]),(0,-.22,.965,[88,466]),(2,.22,2.985,[304,292]),(2,.22,.965,[311,451])]
    for face,d,z,pix in observations:
        a=arc[face];dxy=arc[face+1]-a;vec=dxy/np.linalg.norm(dxy)
        ss,tt=(a if d>0 else arc[face+1])+d*vec
        xyz.append([10.52-tt,12.28+ss,z]);uv.append(pix)
    points=np.array(xyz);pixels=np.array(uv)
    # The close-up is an upright 24-mm-equivalent frame. Allow cropped focal length
    # a moderate range, holding the optical centre at the frame centre.
    def camera(theta):
        f=np.exp(theta[6]);k=np.array([[f,0,194.5],[0,f,292.5],[0,0,1]])
        r=Rotation.from_rotvec(theta[:3]).as_matrix()
        return k@np.column_stack((r,-r@theta[3:6]))
    def residual(theta):
        p=np.column_stack((points,np.ones(len(points))))@camera(theta).T
        return ((p[:,:2]/p[:,2:3]-pixels).reshape(-1)).tolist()+[(theta[6]-np.log(450))*10]
    eye=np.array([15.5,6.5,1.50]);direction=points.mean(0)-eye;direction/=np.linalg.norm(direction)
    right=np.cross(direction,[0,0,1]);right/=np.linalg.norm(right)
    rot=Rotation.from_matrix(np.array([right,np.cross(direction,right),direction])).as_rotvec()
    params=least_squares(residual,[*rot,*eye,np.log(450)],bounds=([-5,-5,-5,12.8,1,-1,np.log(280)],[5,5,5,32,17,4,np.log(740)]),max_nfev=900).x
    return camera(params),[dict(xyz_m=p,uv=u) for p,u in zip(xyz,uv)],np.hypot(*np.array(residual(params)[:-1]).reshape(-1,2).T).tolist()
S='cream dressed stone';R='pale ochre roughcast';T='painted joinery';G='glazing';L='garden light'
east_probes=[(217,194,R),(251,148,R),(291,196,R),(239,187,[T,G,L]),(243,200,[T,G,L]),(243,205,S),(382,242,R),(391,252,R),(341,181,[T,G,L]),(382,292,[T,G,L]),(406,293,[T,G,L]),(205,315,S),(265,312,S),(264,259,S),(281,313,['dark entrance door',T]),(222,319,R),(233,365,'stone tread'),(228,370,'stone tread'),(143,229,'aged iron'),(154,244,S),(151,256,S),(138,301,S),(155,296,[T,G,L]),(161,336,['plinth',S,R]),(487,306,[T,G,L])]
close_probes=[(241,387,[T,G,L]),(182,385,[T,G,L]),(213,334,T),(123,397,[R,S]),(288,407,[R,S]),(212,472,S),(68,367,[T,G,L]),(205,221,S),(196,200,S),(105,120,'aged iron'),(195,136,[R,T,G,L])]
def inspect(scene,p,probes):
    origin=np.linalg.solve(p[:,:3],-p[:,3]);results=[]
    for u,v,expect in probes:
        direction=np.linalg.solve(p[:,:3],[u,v,1])
        hit=scene.ray(origin,direction,120)
        wanted=[expect] if isinstance(expect,str) else expect
        results.append(dict(pixel=[u,v],expected_material_contains=wanted,first_hit=hit,match=bool(hit and any(x in hit['material'] for x in wanted))))
    return {'projection':p.tolist(),'center_enu_m':origin.tolist(),'observations':results,'matched':sum(v['match'] for v in results),'tested':len(results)}
def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);cli.add_argument('models',type=Path,nargs='+');args=cli.parse_args()
    p,controls,errors=close();result={'axes':'local east along garden south edge, north toward street, up','reference_east':{'gao_04_original_px':[1080,809],'measured_on_px':[600,449],'image_source_sha256':'ac33a4c02f80','line_vanishing_points_px':[[-316.77,321.51],[664.04,315.88],[288.04,-2064.25]],'scope':'External lines and pier toes set the pose. The older broad field view has lower silhouette detail than the 2016 June close-up.'},'reference_close':{'width_px':389,'height_px':585,'reference':'gao-real-07.jpg, original 3264×4912','controls':controls,'control_residual_px':errors,'median_fit_px':float(np.median(errors)),'p90_fit_px':float(np.quantile(errors,.9))},'models':[]}
    for model in args.models:
        scene=SerialScene(model)
        result['models'].append({'asset':scene.asset,'broad_east':inspect(scene,east(),east_probes),'round_bay_close':inspect(scene,p,close_probes)})
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
