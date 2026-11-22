"""Read actual glTF geometry and check the paired roof and window profiles."""
import argparse
import json
import math
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from xiangshan_photo_plane import pixel
from xiangshan_dormers import DATA,PLASTER,FRAME,SASH,GLASS,BEAD,REVEAL,ROD,TILES
FRONT=np.array([0.,1.,0.])
UP=np.array([0.,0.,1.])
def surface_checks(low):
    for name in ('eastern','western','link'):
        row=DATA[name];west=name=='western';front=row.get('front_y',0.)
        for i,(x0,x1,z0,z1) in enumerate(row['openings']):
            key=f'{name} window {i+1}';wid=(x1-x0-.09)/2;y=front+.135;lo=z0+.03;hi=z1-.038
            for x in (x0+.020,x1-.020):
                for z in (.26,.55,.8):yield key+' casing',np.array([x,y-.03,z0+(z1-z0)*z]),FRONT,FRAME,.14
            for x in (.22,.52,.78):
                xpos=x0+(x1-x0)*x
                yield key+' exposed sill face',np.array([xpos,front-.055,z0-.02]),FRONT,REVEAL,.045 if west else .16
                if west:
                    yield key+' drying rail in front of sill',np.array([xpos,-.304,z0-.023]),FRONT,ROD,.24
            for leaf in range(2):
                hx=x0+.045+leaf*wid;ang=0.
                if west and i==1 and leaf==0:
                    observed=np.array(pixel([720/62-11,0,13.6-178/62],'roof-15-west'))
                    def error(a):return np.linalg.norm(np.array(pixel([hx+wid*math.cos(a),y-.03-wid*math.sin(a),hi-.015],'roof-15-west'))-observed)
                    ang=minimize_scalar(error,bounds=(.15,math.pi-.05),method='bounded').x
                tangent=np.array([math.cos(ang),-math.sin(ang),0.]);normal=np.array([math.sin(ang),math.cos(ang),0.]);origin=np.array([hx,y-.031,0.])
                def mark(x,dy,z,item,mat,gap):return key+' '+item,origin+tangent*x+normal*dy+UP*z,normal,mat,gap
                ba,he=lo+.034,hi-.032
                for x in (.014,wid-.014):
                    for frac in (.23,.58,.84):yield mark(x,-.018,lo+(hi-lo)*frac,'stile',SASH,.012 if ang else .08)
                for cell in range(3):
                    z=ba+(he-ba)*(cell+.49)/3
                    for f in (.23,.33,.68,.76):yield mark(wid*f,.003,z,'two lights separated by upright',GLASS,.015 if ang else .12)
                    yield mark(wid/2,-.012,z,'central upright',SASH,.015 if ang else .08)
                    for x in (.031,wid/2-.010,wid/2+.010,wid-.031):yield mark(x,.003 if low else -.009,z,'putty or distant pane',GLASS if low else BEAD,.012 if ang else .035)
            if west:
                for frac in (.22,.50,.78):
                    yield key+' drying rack',np.array([x0+(x1-x0)*frac,-.304,z0-.023]),FRONT,ROD,.24
        if name=='link':continue
        l,r=row['x'];center=row['ridge_x'];rise=row['ridge'];yf=-row['forward_overhang'];yr=row['far_y']
        for x in (center-.22,center+.24):yield name+' upper plaster',np.array([x,0.,row['spring']+.31]),FRONT,PLASTER,.2
        for e,sign in ((l,-1),(r,1)):
            end=e+sign*row['rake_overhang']; slope=(rise-row['spring'])/abs(center-e);count=max(3,round(abs(end-center)/.32));n=max(5,round((yr-yf)/.215))
            for i in range(0,count,2):
                for j in range(0,n,3):
                    x=center+(end-center)*(i+.5)/count;y=yf+(yr-yf)*(j+.5)/n
                    z=rise+row['roof_rise']-abs(x-center)*slope+.006+.009
                    yield name+' tile face',np.array([x,y,z]),-UP,TILES[(j+2*i+(1 if sign>0 else 0))%4],.08
def inspect(mesh,low):
    scene=SerialScene(mesh);records=[]
    for k,p,d,mat,gap in surface_checks(low):
        hit=scene.ray(p-d*gap,d,gap+.004);actual=hit['material']if hit else None
        err=None if not hit else float(np.linalg.norm(np.asarray(hit['point_enu_m'])-p))
        records.append(dict(feature=k,expected=mat,actual=actual,point_m=p.round(4).tolist(),photo_2018_px=np.round(pixel(p),1).tolist(),surface_error_m=err,passed=actual==mat and err is not None and err<.0035))
    return dict(**scene.asset,level='lod' if low else 'full',triangles=len(scene.tri),rays=len(records),passed=all(v['passed']for v in records),checks=records)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('level',choices=['full','lod']);p.add_argument('output',type=Path);a=p.parse_args()
    result=inspect(a.mesh,a.level=='lod');a.output.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print(sum(x['passed']for x in result['checks']),result['rays'],result['triangles']);sys.exit(int(not result['passed']))
