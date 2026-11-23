"""Trace photographed openings and the south terrace through an exported house or an isolated roof."""
from pathlib import Path
import argparse
import json
import runpy
import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
Scene=runpy.run_path(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['SerialScene']

def exposure04():
    yaw,elev,roll=np.deg2rad([-139.06617564456207,18.7264862877179,.8947572326458619])
    cy,ce,cr=np.cos([yaw,elev,roll]); sy,se,sr=np.sin([yaw,elev,roll])
    f=1218.387360411953
    forward=np.array([cy*ce,sy*ce,se])
    right=np.array([sy,-cy,0]); up=np.array([-cy*se,-sy*se,ce])
    R=np.array([f*(cr*right+sr*up)+540*forward,-f*(-sr*right+cr*up)+404.5*forward,forward])
    A,B=np.array([10.82,12.58,7.45]),np.array([8.59,12.58,7.45])
    c,d=np.array([490,404]),np.array([638,459])
    delta=R@(B-A)
    depth=(d-c)@(delta[:2]-d*delta[2])/((d-c)@(d-c))
    return np.column_stack([R,np.r_[c,1]*depth-R@A])

def exposure03():
    P=np.array([[188.72341492203344,516.7375758587307,57.22710607562499,3616.1621428889107],[-191.5416758677746,245.8143031779306,-410.23325394878947,5024.704700418674],[-.5957873237641044,.7781674222646077,.19872827621670383,13.543678437786186]])
    return P@np.array([[0,1,0,-12.28],[-1,0,0,10.52],[0,0,1,0],[0,0,0,1]])

def shoot(scene,P,u,v):
    R=P[:,:3]
    origin=-np.linalg.solve(R,P[:,3])
    direction=np.linalg.solve(R,[u,v,1])
    hit=scene.ray(origin,direction,150)
    return hit

def hits(scene):
    P=exposure04()
    measured=json.loads((HERE/'paper04-native-roof-points.json').read_bytes())['stable_points_native_pixels']
    points=[]
    for group in ['left_dormer_cap','right_dormer_cap']:
        r=measured[group]
        for t in (.25,.5,.75):
            left=np.array(r['front_left_window_head'])*.5+np.array(r['front_left_window_sill'])*.5
            right=np.array(r['front_right_window_head'])*.5+np.array(r['front_right_window_sill'])*.5
            q=left*(1-t)+right*t
            hit=shoot(scene,P,*q)
            points.append(dict(exposure='paper04',feature=group,relative_width=t,uv=q.tolist(),actual=hit))
    corners=np.array(list(measured['right_flush_rooflight'].values()))
    q=corners.mean(axis=0)
    points.append(dict(exposure='paper04',feature='flush rooflight',uv=q.tolist(),actual=shoot(scene,P,*q)))
    study=json.loads((HERE/'roof-2016-other-views.json').read_bytes())['primary']
    for feature,q in [('flush rooflight interior',[2805.,394.]),('open left leaf in 2016',[1372.,570.]),('tile shoulder above right dormer',[2812.,289.])]:
        actual=shoot(scene,np.asarray(study['projection_native']),*q)
        points.append(dict(exposure='Gao 05, 2016',feature=feature,uv=q,actual=actual))
    physical=[]
    for name,x,y,z in [('court left',9.8,8.1,8.95),('court right',9.8,8.58,8.95),('return left',7.52,12.02,9.),('return right',7.52,12.46,9.)]:
        for camera,Pj in [('paper03 or Gao04',exposure03()),('paper04',P)]:
            uvw=Pj@np.array([x,y,z,1.]); uv=uvw[:2]/uvw[2]
            hit=shoot(scene,Pj,*uv)
            physical.append(dict(exposure=camera,name=name,projection=uv.tolist(),actual=hit))
    for x,y in [(5.9,.66),(6.9,1.8),(8.4,2.73),(9.7,.91),(9.4,3.2)]:
        hit=scene.ray((x,y,25.),(0.,0.,-1.),30)
        assert hit is None or not hit['material'].startswith('Huang garden |'), (x,y,hit)
        physical.append(dict(name='open south terrace',xy=[x,y],actual=hit))
    glazing='Huang garden | pale old roof glazing'
    casement='Huang garden | dormer casement'
    tile='Huang garden | weathered red clay pantiles'
    for row in points:
        expected=[tile] if row['feature'].startswith('tile shoulder') else [glazing,casement]
        row['allowed_materials']=expected
        assert row['actual'] and row['actual']['material'] in expected,(row,expected)
    for row in physical:
        if row['name']!='open south terrace':
            assert row['actual'] and row['actual']['material']==glazing,row
    return dict(asset=scene.asset,measured_photo_samples=points,projected_physical_controls=physical,passed=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('nets',nargs='+',type=Path)
    args=parser.parse_args()
    result=[hits(Scene(f)) for f in args.nets]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for row in result:
        print(row['asset']['file'],[(p['feature'],p['actual']['material']if p['actual']else None)for p in row['measured_photo_samples']])
