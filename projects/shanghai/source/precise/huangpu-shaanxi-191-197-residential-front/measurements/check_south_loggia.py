"""Cross-check the southern loggia against two independent winter/summer stations.

This is a local correction to projections for comparing the porch alone. All
calibration windows lie on the main house. No porch point is used in the fit.
"""
from pathlib import Path
import sys,json
import numpy as np
from scipy.optimize import least_squares,minimize_scalar,root
M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parent/'source'))
from west_photo_plane import matrix,on_wall,pixel,FRAME_SETBACK
controls=json.loads((M/'west-upper-window-observations.json').read_bytes())['corners']
lower={
 '2018_commons':{'GNTL':[1162,1637],'GNTR':[1476,1634],'GSTL':[2015,1638],'GSTR':[2326,1639]},
 'target17':{'GNTR':[199,416],'GSTL':[434,413],'GSTR':[558,416]},
 'near15':{'GNTL':[365,437],'GNTR':[416,440],'GSTL':[504,446],'GSTR':[536,448]},
 'calsouth15':{'GNTR':[118,431],'GSTL':[193,426],'GSTR':[224,420]},
 'calnorth21':{'GNTL':[520,408],'GNTR':[553,409],'GSTL':[627,418]},
 'target13':{'GSTL':[435,442],'GSTR':[557,437]},
}
for t,add in lower.items(): controls[t].update(add)
named={'U sill left':[2675,1370],'U left jamb base':[2702,1369],'U right jamb base':[2926,1369],'U sill right':[2962,1370],'U top left':[2702,970],'U top right':[2926,969],'arch crown':[2829.8,1565],'arch L spring':[2707,1689],'arch R spring':[2953,1689]}
# Fit current planar camera to two rows of windows only, using an affine correction
# then also compute an independent unconstrained plane homography for sensitivity.
def fact(t):
 src=[];dst=[]
 for name,pt in controls[t].items():
  src.append(pixel(on_wall(*controls['2018_commons'][name],FRAME_SETBACK),t));dst.append(pt)
 src=np.array(src);dst=np.array(dst);ctr=src.mean(0);scale=np.std(src,axis=0).max()
 X=(src-ctr)/scale
 base=np.array([1.,0,0,0,1.,0,0,0])
 def warp(p,xy):
  xy=(np.asarray(xy)-ctr)/scale;d=1+xy@p[6:8]
  a=np.column_stack((xy,np.ones(len(xy))))@p[:6].reshape(2,3).T
  return ctr+scale*a/d[:,None]
 def fun(p):
  err=(warp(p,src)-dst).flatten()
  return np.r_[err,[35*p[6],35*p[7]]]
 fit=least_squares(fun,base,loss='soft_l1',f_scale=2.5)
 return lambda xy:warp(fit.x,np.atleast_2d(xy))[0],np.round(warp(fit.x,src)-dst,1).tolist()

front={'target17':{'U left jamb base':(727,321,5.),'U right jamb base':(847,317,6.)},
       'calsouth15':{'U left jamb base':(278,362,6.),'U right jamb base':(307,354,8.)},
       'near15':{'U left jamb base':(573,389,9.),'U right jamb base':(595,396,9.)}}
names_view=['target17','calsouth15','near15']
def calc():
    corrections={v:fact(v)[0] for v in names_view}
    reports={}
    for t in names_view:
        f,err=fact(t)
        reports[t]={'reference_window_pixel_residuals':dict(zip(controls[t],err)),'front_edge_checks':{}}
        for k,(u,v,sigma) in front[t].items():
            def displacement(y):
                uv=np.array(f(pixel(on_wall(*named[k],y),t)));return uv-[u,v]
            val=minimize_scalar(lambda y:displacement(y)[0]**2,bounds=(-1.2,2.),method='bounded')
            reports[t]['front_edge_checks'][k]={'read_pixel':[u,v],'horizontal_reading_uncertainty_px':sigma,
                'plane0_projected':np.round(displacement(0)+[u,v],2).tolist(),
                'best_depth_horizontal_only_m':round(val.x,3),
                'vertical_residual_at_best_horizontal_median_px':round(float(displacement(val.x)[1]),2)}
    def residual(y):
        values=[]
        for v in names_view:
            for k,(u,_,sd) in front[v].items():
                values.append((corrections[v](pixel(on_wall(*named[k],y),v))[0]-u)/sd)
        return np.array(values)
    opt=minimize_scalar(lambda y:sum(residual(y)**2),bounds=(-1.2,1.5),method='bounded')
    def side(x,u,v,camera,corrected):
        p=matrix(camera);m=np.column_stack((p[:,1],p[:,2],p[:,3]+p[:,0]*x));q=np.linalg.solve(m,[u,v,1]);yz=q[:2]/q[2]
        if corrected:
            yz=root(lambda yz:corrections[camera](pixel([x,*yz],camera))-[u,v],yz).x
        return [round(float(z),3) for z in yz]
    near=side(5.90,2926,1369,'2018_commons',False)[0]
    single={}
    for k,uv in {'western front jamb':[2926,1369],'first surviving southern intrados arris':[2825,1192],
                 'same intermediate pier lower edge':[2820,1315],'inner partial edge':[2793,1336]}.items():
        yz=side(5.90,*uv,'2018_commons',False)
        single[k]={'primary_pixel':uv,'x_assumed':5.90,'y_z_m':yz,'depth_relative_to_front_m':round(yz[0]-near,3)}
    lateral={str(uv):{str(x):{'nominal_yz':side(x,*uv,'calsouth15',False),
             'control_window_adjusted_yz':side(x,*uv,'calsouth15',True)} for x in (6.,6.45)}
             for uv in ([389,341],[412,344],[422,342],[435,345])}
    o={'period':548,'subject':'195 Shaanxi Road South, southern two-storey loggia',
       'method':'Front opening is triangulated in horizontal parallax only, with primary and two-level sash calibration held separately from the porch. Depth sensitivity from correcting the winter station on the visible upper and lower main-house windows is reported explicitly.',
       'primary_camera_unchanged':True,'views':reports,'best_common_front_y_m':round(opt.x,3),
       'horizontal_objective':{str(y):round(float(sum(residual(y)**2)),2) for y in (-1.,-.5,-.2,0.,.2,.4,.7,1.)},
       'front_y_interpretation_m':[-.2,.4],'frontal_2018_looking_into_return':single,
       'south_2015_oblique_side_face':lateral,'suggested_intermediate_rear_pier_depth_m':2.3,
       'return_depth_sensitivity_m':[1.8,2.8],
       'limits':['2017 railing and sill line and its 2015 predecessor are lower in these photographs than the 2018 forward projection. Correcting for setback does not eliminate that vertical difference. Ledges, railing members and aperture noses are separate edges; fit the depiction of a given year to that photograph.',
       'The horizontal fit uses the upper western opening. Inside the 2018 ground-floor front arch a second curved opening and alternating sunlit piers are visible. The 2015 southern view confirms a railing/opening on the perpendicular return. The depth range is an estimate of the visible second pier, not a survey of a rear wall.',
       'In the 2021 northern oblique the main corner/rainwater projection and front roofline remain recognizable; adjacent poles and the far oblique incidence conceal the back side edge. The 2013 balcony has an opaque railing panel and does not supply a matching baluster corner.']}
    (M/'south-loggia-cross-registration.json').write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n')
    print(o['best_common_front_y_m'],o['horizontal_objective'],single,lateral)
if __name__=='__main__':calc()
