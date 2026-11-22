"""Estimate the garden corner's two planes from the published 690 × 821 view.

The return of the projecting bay has its own vanishing point. The three
vertically aligned windows instead establish the receding plane of the main
house. The front wall meets the previously fitted terrace at y = 1.555 m.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

DEST = Path(__file__).resolve().parent
BAY = np.array([
    [.06713343273288565,-.03396391068048788,-.0015388957236482593,.5271740648929393],
    [.03809807606244797,.03053820841336545,-.07064923477058233,.842049864122244],
    [.00005730748615420991,.0000554905577534079,-.000003641856858868641,.001162795624016514]])
X,Y = -3.00883,1.555
# Far jamb head, near jamb head, near jamb sill, far jamb sill; stone outer edges.
OUTLINES = {
    'upper': [[146,251],[188,197],[189,294],[146,337]],
    'middle': [[145,410],[187,377],[187,480],[145,502]],
    'lower': [[144,576],[187,562],None,None]}
# These are independent of the window sills; the eave and the street-side frame
# remain visible high above the garden foliage.
EAVE_LIP = [[234,28],[31,349]]
def project(P, xyz):
    v=P @ np.r_[xyz,1.]
    return v[:2]/v[2]
def fixed_plane(P, uv, axis, value):
    m=P[:2,:]-np.outer(uv,P[2,:])
    other=np.delete(np.arange(3),axis)
    xyz=np.zeros(3);xyz[axis]=value
    xyz[other]=np.linalg.solve(m[:,other],-m[:,axis]*value-m[:,3])
    return xyz
def calibration():
    pairs=[]
    for a,b,c,d in OUTLINES.values():
        pairs.append([a,b])
        if c: pairs.append([d,c])
    # Residual in pixels at the far jamb, independent of line length.
    def residual(vp):
        return [(np.cross([*b,1.],[*vp,1.]) @ [*a,1.])/np.linalg.norm(np.subtract(b,vp)) for a,b in pairs]
    vanishing=least_squares(residual,[-190.,680.],loss='soft_l1').x
    vx=BAY[:,0]/BAY[2,0];vz=BAY[:,2]/BAY[2,2];vy=np.r_[vanishing,1.]
    a,b,c=[v[:2] for v in (vx,vy,vz)]
    principal=np.linalg.solve([b-c,a-c],[a@(b-c),b@(a-c)])
    focal=np.sqrt(-(a-principal)@(b-principal))
    intrinsic=np.array([[focal,0.,principal[0]],[0.,focal,principal[1]],[0.,0.,1.]])
    scale=np.linalg.norm(np.linalg.solve(intrinsic,BAY[:,0]))/np.linalg.norm(np.linalg.solve(intrinsic,vy))
    # The six bay controls fit a very distant vertical vanishing point; at this
    # corner the external arris is vertical within the resolution of the print.
    # Retain the original front-wall scale at mid-height, with an upright local
    # vertical measured at the arris. Keep both calibrations in the record.
    reference=np.array([X,Y,4.75,1.])
    denominator=BAY[2]@reference
    px_per_m=(project(BAY,[X,Y,0])[1]-project(BAY,[X,Y,9.47])[1])/9.47
    P=np.zeros((3,4));P[:,0]=BAY[:,0];P[:,1]=vy*scale
    P[:,2]=(0.,-denominator*px_per_m,0.)
    P[:,3]=denominator*np.array([250.,720.,1.])-P[:,:2]@[X,Y]
    return P,vanishing,residual(vanishing)
def main():
    P,vp,residual=calibration()
    samples={}
    for name,corners in OUTLINES.items():
        samples[name]=[fixed_plane(P,uv,0,X).round(5).tolist() if uv else None for uv in corners]
    soffit_height=fixed_plane(P,[250,98],0,X)[2]
    outer=fixed_plane(P,[237,59],2,soffit_height)
    offsets=np.array([X,Y])-outer[:2]
    p={ 'subject':'上海美丽园14号，园侧主墙转角', 'source_url':'https://s1.sinaimg.cn/mw690/001HIrzOzy7eMoPOZck90&690',
        'source_sha256':'3839cbc07009853fb9d993fab33609d72c06e94c7ec662771a7826a1f3b3870c',
        'source_size_px':[690,821],'arranged_on_bay_datum_m':[X,Y],
        'bay_projection':BAY.tolist(),'main_corner_projection':P.tolist(),
        'main_return_vanishing_point_px':vp.round(5).tolist(),'window_line_residuals_px':np.round(residual,4).tolist(),
        'camera_position':np.linalg.solve(P[:,:3],-P[:,3]).tolist(),
        'opening_outer_stone_corners_px':OUTLINES,'opening_outer_stone_corners_m':samples,
        'inner_soffit_corner_px':[250,98],'outer_soffit_corner_px':[237,59],
        'soffit_height_m':round(soffit_height,5),'soffit_estimated_xy_projection_m':offsets.round(5).tolist(),
        'scale_and_limits':'米制基准沿用凸窗估计尺寸。侧墙消失点来自三个窗头和两个可见窗台，附墙两面按直角估算。窗框尺寸、出檐深度与最下窗台被遮部分均非测绘数据。'}
    (DEST/'garden-corner-camera.json').write_text(json.dumps(p,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__': main()
