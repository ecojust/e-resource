"""Estimate cornice and ridge heights from the 2010 Sony photograph and registered south wall."""
from pathlib import Path
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import numpy as np,json
def estimate(focal=530,far_end_height_px=263):
    uv=np.array([[83,366],[466,305],[680,far_end_height_px],[70,174],[466,150],[694,139]],float)
    x=np.array([-33.07,0,33.07,-33.07,0,33.07]);y=np.zeros(6)
    def view(p,xx=x,yy=y,zz=None):
        cx,cy,cz,yaw,up,roll,h=p;zz=np.r_[np.zeros(3),[h]*3]if zz is None else zz
        eye=np.array([cx,cy,cz]);direction=np.array([np.sin(yaw)*np.cos(up),np.cos(yaw)*np.cos(up),np.sin(up)])
        right=np.array([np.cos(yaw),-np.sin(yaw),0]);sky=np.cross(right,direction)
        k=np.column_stack([xx,yy,zz])-eye
        cam=np.column_stack([k@right,-k@sky]);mat=np.array([[np.cos(roll),-np.sin(roll)],[np.sin(roll),np.cos(roll)]])
        return cam@mat.T/(k@direction)[:,None]*focal+[365,241.5]
    p=least_squares(lambda p:(view(p)-uv).ravel(),[-16,-48,18,.28,-.16,0,16],bounds=([-85,-160,3,-1.3,-.8,-.5,8],[10,-8,55,1.3,.2,.5,33]))
    # Central broken pediment at the front and main ridge behind it, measured separately.
    vals=[]
    for pos,xy,px in [('central broken pediment',(0,0),(470,113)),('slope break',(0,2.60*25.144/24.07),(None,122)),('middle ridge',(0,25.144/2),(None,85))]:
        a,b=xy
        def residual(z):
            pred=view(p.x,[a],[b],[z[0]])[0]
            return [pred[1]-px[1]] if px[0] is None else pred-px
        hit=least_squares(residual,[22])
        vals.append({'point':pos,'drawing_xy':list(xy),'pixel':list(px),'estimated_z':float(hit.x[0]),'pixel_residual':float(np.linalg.norm(hit.fun))})
    return {'focal_pixels':focal,'far_base_y_px':far_end_height_px,'camera_fit':p.x.tolist(),'eaves_m':float(p.x[-1]),'rms_pixel':float(np.sqrt(np.mean(p.fun**2))),'top':vals,'features_px':uv.tolist()}
if __name__=='__main__':
    print(json.dumps([estimate(f,p)for f,p in [(530,263),(493,260),(570,270)]],indent=2))
