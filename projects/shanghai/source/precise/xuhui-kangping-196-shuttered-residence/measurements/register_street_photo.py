"""Register the planar frontage using the photographed street wall and the 27 mm EXIF focal length."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
# Original photo scaled uniformly to 800x600. Lines follow precast courses and window edges.
HORIZONTAL=[
 ((31,357),(93,357)),((179,356.9),(244,356.1)),((323,356.4),(433,356.0)),
 ((609,356.3),(735,355.9)),((329,469.6),(433,469.7)),((615,469.9),(746,470.1)),
 ((191,484.0),(299,484.0)),((607,489),(770,489.3)),((130,521.9),(296,522.4)),
 ((606,522.6),(765,522.9))]
VERTICAL=[
 ((110,348),(89,518)),((139.8,350),(126.3,485)),((174.8,358),(173.1,396)),
 ((245.5,358),(243.5,394.9)),((309.8,352),(304.0,482)),((322.9,357.0),(319.1,468.6)),
 ((570.0,355.2),(576.5,504.1)),((602.2,354.8),(608.6,468.7)),
 ((736.2,356.3),(747.9,469.3)),((772.7,347.8),(788.0,484.5))]
def solve(door_height=2.42,focal35=27.):
    focal=np.hypot(800,600)*focal35/np.hypot(36,24)
    K=np.array([[focal,0,399.5],[0,focal,299.5],[0,0,1.]])
    base=np.array([[1.,0.,0.],[0.,0.,-1.],[0.,1.,0.]])
    def orientation(params): return Rotation.from_rotvec(params).as_matrix()@base
    def line_residual(params):
        R=orientation(params);values=[]
        for lines,axis in [(HORIZONTAL,0),(VERTICAL,2)]:
            vanishing=K@R[:,axis]
            for first,last in lines:
                a,b=np.array(first),np.array(last);center=(a+b)/2
                target=vanishing[:2]-center*vanishing[2];target/=np.linalg.norm(target)
                seg=b-a;values.append(seg[0]*target[1]-seg[1]*target[0])
        return values
    opt=least_squares(line_residual,[.12,0,0],loss='soft_l1',f_scale=.7)
    R=orientation(opt.x);invK=np.linalg.inv(K)
    def plane(x,y):
        direction=R.T@invK@[x,y,1]
        return direction/direction[1]
    # Conditional scale from the clear doorway, with a separate pavement datum directly below it.
    bottom,top=plane(527.5,499.5),plane(523.5,357.)
    factor=door_height/(top[2]-bottom[2]);pavement=plane(528.,522.4)
    eye=np.array([-factor*bottom[0],-factor,-factor*pavement[2]])
    P=K@R@np.column_stack([np.eye(3),-eye]);return P,eye,np.asarray(line_residual(opt.x))
def station_scale():
    survey=json.loads((HERE/'2020-street-facade-intersection.json').read_bytes())
    measured={r['key']:r['approx_m'] for r in survey['relative_window_dimensions']}
    windows=json.loads((HERE/'shutter-panel-observations.json').read_bytes())['opening_quads_native_tl_tr_br_bl']
    baseline=2.42
    P,eye,_=solve(baseline)
    inv=np.linalg.inv(P[:,:3])
    def point(u,v):
        ray=inv@[u*800/3968,v*600/2976,1.]
        return eye+ray*(-eye[1])/ray[1]
    def edges(key):
        tl,tr,br,bl=[point(*uv) for uv in windows[key]]
        return ((tl[0]+bl[0])/2,(tr[0]+br[0])/2,(tl[2]+tr[2])/2,(bl[2]+br[2])/2)
    left=edges('small-left');right=edges('small-right');wide=edges('wide-left')
    samples=[('wide_shutter_width',wide[1]-wide[0],.30),
             ('paired_transom_axis_spacing',(right[0]+right[1]-left[0]-left[1])/2,.40),
             ('transom_height_near',right[2]-right[3],.16),
             ('transom_height_far',left[2]-left[3],.16)]
    a=np.array([v for k,v,sigma in samples]);y=np.array([measured[k] for k,v,sigma in samples])
    weights=1/np.square([sigma for k,v,sigma in samples])
    factor=float(np.sum(weights*a*y)/np.sum(weights*a*a))
    rows=[{'feature':k,'initial_m':float(v),'independent_observation_m':measured[k],'weight_scale_m':sigma,'fitted_minus_observed_m':round(float(v*factor-measured[k]),4)} for k,v,sigma in samples]
    return baseline*factor,rows

def main():
    height,controls=station_scale()
    P,eye,res=solve(height)
    sample={}
    for name,uv in {'door.bottom':(527.5,499.5),'door.head':(523.5,357.),'street.grade':(528.,522.4),'left.jamb':(479,498),'right.jamb':(576,498),'high.front':(516,317),'south.sash':(374,413),'north.sash':(671,413),'first.small':(62,376),'second.small':(208,376)}.items():
        v=np.linalg.inv(P[:,:3])@[*uv,1];pt=eye+v*(-eye[1]/v[1]);sample[name]={'working_pixel':uv,'u_d_z_m':pt.round(5).tolist()}
    result={'source':'https://commons.wikimedia.org/wiki/File:196_Kangping_Road.jpg','source_sha256':'70ef2cc3dc44d891242d01dff8d18687b7d039e78162998e39ca8ed64f30ae21','photo_date':'2019-02-23','author':'Livelikerw','camera':'Huawei EVA-AL00','focal_35mm_equivalent':27,'original_size':[3968,2976],'working_size':[800,600],'axes':'u points right along the photographed front; d perpendicular into the building; z from pavement','horizontal_lines':HORIZONTAL,'vertical_lines':VERTICAL,'line_cross_track_errors_px':res.round(4).tolist(),'line_residual_median_px':float(np.median(abs(res))),'line_residual_p90_px':float(np.quantile(abs(res),.90)),'assumption':'The photograph is normalized using an illustrative opening height, then rescaled against the published local widths, heights and spacing of its exterior windows. The tall left jamb is partly obscured by a tree.','scaled_door_height_m':height,'cross_year_scale_ties':controls,'scale_source':'2020-street-facade-intersection.json','P_800':P.tolist(),'estimated_eye_udz':eye.tolist(),'measured_front':sample}
    (HERE/'2019-front-camera.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(eye,round(result['line_residual_median_px'],3),round(result['line_residual_p90_px'],3),sample['high.front'])
if __name__=='__main__':main()
