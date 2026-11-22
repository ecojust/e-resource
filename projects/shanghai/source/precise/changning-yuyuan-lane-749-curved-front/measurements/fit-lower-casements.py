"""Fit the two outward lower leaves using the corners outside the foreground cables."""
from pathlib import Path
import json,math,numpy as np
from scipy.optimize import least_squares
here=Path(__file__).absolute().parent
r=json.loads((here/'curved-corner-camera.json').read_bytes());D=r['model'];P=np.array(r['world_to_working_image'])
W=D['bay_widths_m'][1];radius=D['radius_m'];chord=radius*(math.sqrt(1-(W/(2*radius))**2)-1)
crop_corners=[[[56,91],[253,79],[299,584],[81,592]],[[283,77],[452,108],[488,607],[321,585]]]
uv=np.array(crop_corners)/np.array([3.3,2632/798])+np.array([398,458])
def geometry(p):
    deg0,deg1,w0,w1,d,xoff,zlo,zhi=p
    hi=D['lower_window_top_m']+zhi;lo=D['lower_window_top_m']-D['lower_window_height_m']+zlo
    rows=[]
    for i,(a,w)in enumerate([(deg0,w0),(deg1,w1)]):
        x=(-1 if i==0 else 1)*(W/2-.032)+xoff
        at=np.deg2rad(a);hinge=[x,-(d+chord)];swing=[x+(1 if i==0 else -1)*w*np.cos(at),-(d+chord+w*np.sin(at))]
        left,right=(hinge,swing)if i==0 else(swing,hinge)
        rows.append([[*left,hi],[*right,hi],[*right,lo],[*left,lo]])
    return np.array(rows)
def display(x):
    a=np.concatenate([x,np.ones(x.shape[:2]+(1,))],axis=2)@P.T;return a[:,:,:2]/a[:,:,2,None]
def error(p):
    return np.r_[((display(geometry(p))-uv)/1.85).ravel(),(p[2]-W*.465)/.045,(p[3]-W*.465)/.045,(p[4]+.046)/.05,p[5]/.032,p[6]/.068,p[7]/.068]
if __name__=='__main__':
    sols=[least_squares(error,[v0,v1,W*.47,W*.47,-.025,0,0,0],bounds=([0,0,.40,.40,-.13,-.10,-.13,-.13],[80,80,.65,.65,.08,.10,.14,.12]))for v0,v1 in [(12,27),(35,47),(5,55)]]
    f=min(sols,key=lambda i:i.cost);xyz=geometry(f.x);projected=display(xyz)
    print('outward opening angles and fitted dimensions',np.round(f.x,4),'individual px residuals',np.round(np.linalg.norm(projected-uv,axis=2),2))
    args=['left_degrees','right_degrees','left_width_m','right_width_m','hinge_outward_m','common_x_shift_m','bottom_offset_m','top_offset_m']
    obj=dict(original_sha256=r['original_photo_sha256'],crop_sha256=r['crop_sha256'],params={k:float(v)for k,v in zip(args,f.x)},
      working_image_controls=uv.tolist(),world_xyz=xyz.tolist(),reprojected_px=projected.tolist(),residual_px=(projected-uv).tolist(),
      description='左右扇靠两侧转轴外开；左扇反射较亮，右扇反射较暗。两扇自由边不在同一平面，开启角随相机和窗高假设而变。')
    (here/'lower-casement-fit.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
