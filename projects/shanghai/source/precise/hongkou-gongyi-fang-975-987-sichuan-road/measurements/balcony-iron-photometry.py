"""Read iron/background tone and apparent upright width from the licensed native exposure."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent


def run(photo):
    sources=json.loads((HERE/'balcony-photo-traces.json').read_bytes())
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==sources['source_images'][0]['sha256']
    reg=sources['registration']
    layout=json.loads((HERE.parent/'source/front-layout.json').read_bytes())
    im=np.asarray(Image.open(photo).convert('RGB'))
    axes=layout['bay_edges'];span=np.median(np.diff(axes));pier=.097*span
    w=axes[2]-axes[1]-pier
    h=.235*span;face=-layout['balcony_depth']+.43*pier-.021
    points=[];uv=[]
    for level,key,field in [(0,'commons_lower_panel','quadrilateral_top_left_clockwise'),
                            (1,'commons_panel','image_quad_top_left_clockwise')]:
        floor=layout['balcony_z'][level];zlo=floor+.033*h;zhi=floor+.858*h
        points.extend([[axes[1]+pier/2,face,zhi],[axes[2]-pier/2,face,zhi],
                       [axes[2]-pier/2,face,zlo],[axes[1]+pier/2,face,zlo]])
        uv.extend(reg[key][field])
    points=np.array(points);uv=np.array(uv)
    cen=np.array([2656.,1494.])
    p0=np.array([-.5,-18.,3.])
    along=(points.mean(axis=0)-p0);along/=np.linalg.norm(along)
    right=np.cross(along,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(along,right)
    initial=Rotation.from_matrix(np.stack([right,down,along])).as_rotvec()
    def project(b):
        v=(points-b[3:6])@Rotation.from_rotvec(b[:3]).as_matrix().T
        return cen+b[6]*v[:,:2]/v[:,2,None]
    estimate=np.r_[initial,p0,3950.]
    fit=least_squares(lambda b:(project(b)-uv).ravel(),estimate,
        bounds=(np.r_[np.full(6,-np.inf),3730.],np.r_[np.full(6,np.inf),4250.]),loss='soft_l1',f_scale=4.)
    residual=np.linalg.norm(project(fit.x)-uv,axis=1)
    centre=np.array([.5*(axes[1]+axes[2]),face,0.])
    tangent=abs((centre[0]-fit.x[3])/(centre[1]-fit.x[4]))
    traces=[]
    # These upright runs have a light-coloured wall, plaster or clear pane on
    # each side. Separate the two floors despite their shared photographer.
    for name,cols in [('commons_panel',[101,117,132,163,180,195,483,498,513,529,545,560,576]),
                      ('commons_lower_panel',[105,164,180,195,478,493,512,529,545,560,576])]:
        H=np.asarray(reg[name]['drawing_to_native_image'])
        def rgb(x,y):
            q=H@np.asarray([x,y,1.]);u,v=q[:2]/q[2]
            return np.array([map_coordinates(im[:,:,k],[[v],[u]],order=1)[0] for k in range(3)])
        for x in cols:
            offsets=np.arange(-7.,7.001,.25)
            channel=np.array([np.mean([rgb(x+off,y) for y in (78,80,82,84,86)],axis=0) for off in offsets])
            luminance=channel@np.array([.213,.715,.072])
            indices=np.where(abs(offsets)<=3.25)[0];idx=indices[np.argmin(luminance[indices])]
            left=np.median(luminance[:7]);right_l=np.median(luminance[-7:]);back=min(left,right_l)
            half=(back+luminance[idx])/2
            l=r=idx
            while l>0 and luminance[l-1]<half:l-=1
            while r<len(luminance)-1 and luminance[r+1]<half:r+=1
            width_px=(r-l+1)*.25
            use=(back-luminance[idx]>=28 and abs(offsets[idx])<3.1 and
                 l>1 and r<len(luminance)-2 and width_px>=.75)
            actual_x=x+offsets[idx];pixel=H@np.array([actual_x,82.,1.])
            traces.append(dict(panel=name,expected_drawing_x=x,measured_drawing_x=round(actual_x,2),
              native_middle_pixel=(pixel[:2]/pixel[2]).round(2).tolist(),used=bool(use),
              centre_rgb=channel[idx].round(1).tolist(),background_rgb=np.mean([channel[2],channel[-3]],axis=0).round(1).tolist(),
              contrast=round(back-luminance[idx],1),apparent_width_rectified_units=width_px,
              width_on_projected_rail_plane_m=round(w*width_px/670,4)))
    good=[r for r in traces if r['used']]
    widths=np.array([r['width_on_projected_rail_plane_m'] for r in good])
    # The observed silhouette combines front width and the projection of
    # front-to-back stock. Only their combination is measured by this image.
    front_width=w*2.25/670
    depth_interval=(np.percentile(widths,[10,50,90])-front_width)/tangent
    return dict(repair_specification=dict(page='https://m.thepaper.cn/baijiahao_31065777',
              author='上海章明建筑设计事务所',
              visible_finish='原文要求醇酸防锈作底两度，外用醇酸黑漆罩面两遍。',
              interpretation='旧日光照中的褐黑像值受暖色背景、曝光及反光影响。现代模型用近黑色漆，不能从街照单独量取漆膜本色。'),
          strip_section=dict(front_width_model_m=round(front_width,4),front_to_back_model_m=.021,
              apparent_model_width_at_this_view_m=round(front_width+.021*tangent,4),
              inferred_depth_m_at_width_percentiles=depth_interval.round(4).tolist(),
              interpretation='投影轮廓宽约为正脸宽加进深乘斜视角正切。区间条件是正脸采用模型的平条宽，铁条背面未在独立近照清楚显露；截面保留估计。'),
          exposure=sources['source_images'][0],exif=dict(camera='Samsung SM-G9209',physical_focal_mm=4.3,
          equivalent_focal_mm=28,assumed_principal_point=cen.tolist()),eight_rail_corners=dict(camera_eye=fit.x[3:6].round(4).tolist(),
          fitted_focal_px=round(fit.x[6],2),reprojection_error_px=residual.round(2).tolist(),horizontal_view_angle_tangent=round(tangent,4)),
          method='Linear interpolation on the native photograph; five samples along each upright. Apparent width is measured at half the upright-to-neighbour contrast. Both neighbouring backgrounds must be brighter by at least 28 sRGB luma units; all attempts are retained.',
          usable=len(good),total=len(traces),median_dark_rgb=np.median([r['centre_rgb'] for r in good],axis=0).round(1).tolist(),
          median_flanking_rgb=np.median([r['background_rgb'] for r in good],axis=0).round(1).tolist(),
          apparent_width_m_percentiles_10_50_90=np.percentile(widths,[10,50,90]).round(4).tolist(),traces=traces)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('photo',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();r=run(a.photo);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['usable'],r['total'],r['median_dark_rgb'],r['median_flanking_rgb'],r['apparent_width_m_percentiles_10_50_90'],r['eight_rail_corners'])
