"""Measure only the old gatehouse railing on two scans of the same negative."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.optimize import minimize

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def project(matrix, points):
    points=np.asarray(points,float)
    t=np.c_[points.reshape(-1,2),np.ones(points.size//2)] @ matrix.T
    return (t[:,:2]/t[:,2:]).reshape(points.shape)

def sample(im,points):
    points=np.asarray(points)
    return map_coordinates(im,[points[...,1],points[...,0]],order=1,mode='nearest')

def rounded(v):return np.round(v,3).tolist()

def measure(fine,printed,registration):
    hi,lo=[np.asarray(Image.open(f).convert('L'),float)for f in [fine,printed]]
    reg=json.loads(registration.read_bytes())
    assert reg['sources'][0]['sha256']==sha(printed) and reg['sources'][1]['sha256']==sha(fine)
    H=np.asarray(reg['matrix_323_to_640']); inv=np.linalg.inv(H)
    hi_blur=gaussian_filter(hi,.65)
    def pair(label,xy,kind,side=''):
        q=np.asarray(xy,float)
        coords=np.stack(np.mgrid[-5:6,-5:6][::-1],axis=-1)+q
        original=sample(hi_blur,coords).ravel()
        def err(offset):
            other=sample(lo,project(inv,coords)+offset).ravel()
            return 1-np.corrcoef(original,other)[0,1]
        # Independently align an 11x11 native-pixel patch. Adjust both axes together.
        grid=[np.asarray([x,y])for x in [-1,0,1]for y in [-1,0,1]]
        start=min(grid,key=err);fit=minimize(err,start,method='Powell',bounds=[(-1.5,1.5)]*2)
        low=project(inv,q)+fit.x; recovered=project(H,low)
        return dict(label=label,kind=kind,side=side,pixel_640=rounded(q),measured_pixel_323=rounded(low),registered_pixel_323=rounded(project(inv,q)),residual_xy_640=rounded(recovered-q),residual_length_640=round(float(np.linalg.norm(recovered-q)),3),local_patch_correlation=round(float(1-err(fit.x)),4))
    def edge(label,xy,normal,side):
        q=np.asarray(xy,float);v=np.asarray(normal,float);v/=np.linalg.norm(v)
        ts=np.arange(-2.5,2.501,.125);curve=sample(hi_blur,q+ts[:,None]*v)
        i=np.argmax(np.abs(np.gradient(curve,ts))[3:-3])+3
        q=q+ts[i]*v;row=pair(label,q,'实测明暗边',side)
        sides=sample(hi,[q-2*v,q+2*v]);row.update(normal_xy=rounded(v),luma_minus_plus_2px=rounded(sides),contrast_4px=round(abs(float(sides[1]-sides[0])),2),eligible_contour_control=abs(float(sides[1]-sides[0]))>=32)
        return row
    # Hand-located intersections and unbroken one-sided edges in the larger scan.
    # Each seed is within 2.5 pixels of a visible gradient; dark/light is a tone observation.
    panels=[
      ((116,211),[(107,202,1,-1),(106,217,1,1),(111,217,1,1),(123,200,1,1),(125,206,1,1),(125,217,1,-1)]),
      ((175,214),[(168,209,1,-1),(166,217,1,1),(167,224,1,1),(181,210,1,1),(184,218,1,-1),(182,223,1,-1)]),
      ((220,218),[(214,213,1,-1),(215,222,1,1),(214,228,1,1),(227,212,1,1),(227,224,1,-1),(230,228,1,-1)]),
      ((265.5,228.5),[(263,222,1,-.5),(262.5,230,1,.6),(264,235,1,.55),(269,221,1,.55),(270,232,1,-.55),(271,237,1,-.55)])]
    out=[]
    for i,(center,segments) in enumerate(panels):
        pts=[pair('X形交会',center,'人工标定交会中心')]
        for j,(x,y,nx,ny)in enumerate(segments):
            pts.append(edge(['斜边上段','斜边中段','斜边下段'][j%3],[x,y],[nx,ny],'像面左半' if j<3 else '像面右半'))
        # An independent sample on each side of every proposed edge allows an auditor to discard low-contrast covariates.
        out.append(dict(panel=i+1,nominal_center_uncertainty_640_px=(1.5 if i<3 else 2.5),
            observed=('X形交会及其两侧亮地、暗杆' if i==0 else ('面宽明显压缩，右侧暗带与背景连在一起，交会中心区约五像素宽' if i==3 else '浅色交叉形和两侧深色区域，下方有边界较清楚的深色三角')),
            points=pts))
    rail=[]
    for label,pts in [('帽石上缘',[(87,184),(115,187),(137,187),(158,190),(190,195),(211,197),(242,198),(258,202),(279,206)]),('栏身底边接线',[(84,236),(104,235),(120,235),(138,237),(158,238),(189,240),(200,243),(226,242),(246,245),(260,247),(279,252)])]:
        for xy in pts:rail.append(edge(label,xy,[0,1],'沿栏左至右'))
    return dict(building='历史照片所见二层切角门楼',sources=reg['sources'],registered_with=sha(registration),
        calibration=dict(high_coordinates='640px旧照裁片，自左上像素中心起算',low_coordinates='323px出版合图上部，同一原点',hi_to_lo_matrix=inv.tolist(),held_out_median_native640=reg['held_out_median_px'],held_out_p90_native640=reg['held_out_p90_px']),
        method='人工定位交会中心和明暗边，以短法向灰度梯度定位边线。各点在两种扫描上用局部11×11高分像素片独立微移配准，记录低分原坐标、预测坐标与往返残差。左右均指像面方向。',limits='同底片重印只有一个观察角。深色区域能用于比轮廓，透空或后部阴影不能仅据灰度区分。第4格贴近折角，暗面和杆身有并合。栏顶栏底节点标识二维折线形状，角度随像面投影。',panels=out,rail_edge_samples=rail)
if __name__=='__main__':
    p=argparse.ArgumentParser();[p.add_argument(k,type=Path)for k in ('fine','printed','registration','out')];a=p.parse_args()
    obj=measure(a.fine,a.printed,a.registration);a.out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
